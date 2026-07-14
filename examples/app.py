"""
app.py — an OpenAI + Pinecone RAG pipeline traced with OpenTelemetry,
exported to Splunk via the OpenTelemetry Collector.

No custom SDK. Three layers only:
  1. Standard OTel SDK wiring (or skip it entirely — see "Zero-code" below).
  2. Official OpenAI auto-instrumentation, which emits the gen_ai.* semantic
     conventions on every chat and embeddings call (model, tokens, status).
  3. ~4 vanilla span.set_attribute() calls for the things OTel cannot know:
     that a span is a RETRIEVER, and how well retrieval actually did.

The gen_ai.* -> flat-field mapping the Splunk dashboards need happens in the
Collector (collector/otel-collector-config.yaml), not here.

Run:
    set -a; source .env; set +a           # or: python-dotenv loads it below
    otelcol-contrib --config collector/otel-collector-config.yaml   # separate shell
    python app.py --seed                  # --seed only needed on the first run

Zero-code alternative (delete the OTel wiring block, keep the set_attributes):
    opentelemetry-instrument python app.py
"""
import argparse
import os
import time

from dotenv import load_dotenv

# Load OPENAI_API_KEY / PINECONE_* / OTEL_* before anything reads os.environ.
load_dotenv()

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor

# ---- config ---------------------------------------------------------------- #
# CHAT_MODEL must match a row in the Splunk app's genai_model_pricing.csv, or the
# cost panels silently report $0 for it (the SPL coalesces a missing price to 0).
CHAT_MODEL = os.environ.get("CHAT_MODEL", "gpt-4o")

# The embedding model's native dimension MUST equal the Pinecone index dimension:
#   text-embedding-3-small -> 1536   |   text-embedding-3-large -> 3072
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = int(os.environ.get("EMBED_DIM", "1536"))

INDEX_NAME = os.environ.get("PINECONE_INDEX", "genai-rag-demo")
PINECONE_CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.environ.get("PINECONE_REGION", "us-east-1")
TOP_K = int(os.environ.get("RAG_TOP_K", "5"))

OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
WORKFLOW = os.environ.get("OTEL_SERVICE_NAME", "rag-demo")

SEED_DOCS = [
    "Splunk HEC accepts JSON events over HTTPS on port 8088.",
    "The genai_traces index stores one event per span.",
    "Data model acceleration speeds up the tstats dashboards.",
]


# ---- stamp workflow_name on EVERY span, including auto-instrumented ones ---- #
class WorkflowAttributeProcessor(SpanProcessor):
    """Set workflow_name on each span at creation.

    Auto-instrumentation doesn't know about your application's concepts, so the
    OpenAI chat/embedding spans would otherwise be missing workflow_name — and
    any dashboard filtering by workflow would silently drop them. on_start is
    the hook for injecting app context into spans you didn't write (tenant,
    environment, deploy version, ...).
    """

    def __init__(self, workflow_name: str):
        self._workflow_name = workflow_name

    def on_start(self, span, parent_context=None):
        span.set_attribute("workflow_name", self._workflow_name)

    def on_end(self, span): ...
    def shutdown(self): ...
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


# ---- standard OTel wiring (the OTel SDK, not a custom one) ------------------ #
provider = TracerProvider(resource=Resource.create({"service.name": WORKFLOW}))
trace.set_tracer_provider(provider)

# Register before the exporter so every span is stamped on the way out.
provider.add_span_processor(WorkflowAttributeProcessor(WORKFLOW))
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)  # TLS in production
    )
)

# One line: every OpenAI chat AND embeddings call now emits a gen_ai.* span
# carrying model, input/output tokens, and error status.
# Set OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true to also capture
# prompts and completions — that writes user text to your log index, so treat it
# as a PII decision, not a config one.
OpenAIInstrumentor().instrument()

tracer = trace.get_tracer("rag-app")
client = OpenAI()
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])


# ---- index bootstrap -------------------------------------------------------- #
def ensure_index(seed: bool = False) -> None:
    """Create the index if missing, wait until it's queryable, optionally seed."""
    existing = [i["name"] for i in pc.list_indexes()]

    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBED_DIM,
            metric="cosine",  # cosine -> scores ~0..1, matching the dashboard scale
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )
        # create_index is asynchronous: upserting or querying before the index is
        # ready fails. Poll rather than sleeping a guessed interval.
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(1)

    if seed:
        index = pc.Index(INDEX_NAME)
        vectors = []
        for i, text in enumerate(SEED_DOCS):
            emb = client.embeddings.create(model=EMBED_MODEL, input=text)
            vectors.append((f"doc-{i}", emb.data[0].embedding, {"text": text}))
        index.upsert(vectors=vectors)


# ---- the pipeline ----------------------------------------------------------- #
def retrieve(query: str):
    """RETRIEVER span. span_type + retrieval quality are the irreducible attrs:
    nothing but your app can report how many docs came back and how good they were.
    """
    with tracer.start_as_current_span("vector_search") as span:
        span.set_attribute("span_type", "RETRIEVER")
        span.set_attribute("vector_store", "pinecone")
        span.set_attribute("embedding_model", EMBED_MODEL)

        # Auto-instrumented -> becomes a child EMBEDDING span for free.
        emb = client.embeddings.create(model=EMBED_MODEL, input=query)

        index = pc.Index(INDEX_NAME)
        res = index.query(
            vector=emb.data[0].embedding, top_k=TOP_K, include_metadata=True
        )
        matches = res.get("matches", [])

        # The RAG quality signal: when answers degrade, this is what tells you
        # whether the model got worse or retrieval did. Very different bugs.
        span.set_attribute("documents_retrieved", len(matches))
        if matches:
            avg_score = sum(m["score"] for m in matches) / len(matches)
            span.set_attribute("relevance_score", round(avg_score, 4))
        return matches


def lookup(symbol: str) -> float:
    """TOOL span."""
    with tracer.start_as_current_span("price_lookup") as span:
        span.set_attribute("span_type", "TOOL")
        span.set_attribute("tool_name", "market_data_api")
        return {"AAPL": 213.4}.get(symbol, 0.0)


def rag(question: str) -> str:
    """CHAIN parent — the root span per request. Without it you have no
    end-to-end latency and no request count."""
    with tracer.start_as_current_span("rag_pipeline") as span:
        span.set_attribute("span_type", "CHAIN")

        matches = retrieve(question)
        context = "\n".join(m["metadata"].get("text", "") for m in matches)

        # Fully auto-instrumented -> gen_ai.* attrs, token counts, status.
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "user", "content": f"Context:\n{context}\n\nQ: {question}"}
            ],
        )
        return resp.choices[0].message.content


def agent(question: str):
    """AGENT span — routes to the tool or the RAG chain."""
    with tracer.start_as_current_span("router_agent") as span:
        span.set_attribute("span_type", "AGENT")
        if any(c.isdigit() for c in question):
            return lookup("AAPL")
        return rag(question)


# ---- entrypoint ------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        action="store_true",
        help="upsert the demo documents (needed once, on a fresh index)",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="How does data get into the genai_traces index?",
    )
    args = parser.parse_args()

    ensure_index(seed=args.seed)
    try:
        print(agent(args.question))
    finally:
        # Flush the BatchSpanProcessor — without this, the last spans of a
        # short-lived process are lost.
        provider.shutdown()


if __name__ == "__main__":
    main()
