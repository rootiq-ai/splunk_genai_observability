"""
Standard OpenTelemetry -> Splunk GenAI Observability app.
=========================================================
NO custom SDK. This script imports ONLY the official opentelemetry-* libraries
and openai. If you already use OpenTelemetry, this is all it takes to light up
the dashboards in the GenAI Observability for Splunk app.

Install (all standard, published OpenTelemetry packages):
    pip install opentelemetry-sdk \
                opentelemetry-exporter-otlp-proto-http \
                opentelemetry-instrumentation-openai-v2 \
                openai

Run an OpenTelemetry Collector on :4318 that forwards to Splunk
(use otel-collector-config.yaml shipped with the Splunk app), then:
    export OPENAI_API_KEY="sk-..."     # $env:OPENAI_API_KEY on PowerShell
    python otel_native_example.py

Pipeline:
    your normal OpenAI code
      -> OpenTelemetry auto-instrumentation (emits gen_ai.* semantic conventions)
      -> OTLP/HTTP to the Collector (:4318)
      -> Collector maps gen_ai.* -> dashboard fields, ships to Splunk HEC (genai:otel)
      -> GenAI Observability app dashboards
"""

import os

from openai import OpenAI

# --- standard OpenTelemetry SDK setup (nothing custom) -----------------------
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor

provider = TracerProvider(resource=Resource.create({"service.name": "support-assistant"}))
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces"))
)
trace.set_tracer_provider(provider)

# Official GenAI auto-instrumentation: every OpenAI call now emits gen_ai.* spans
# (model, token usage, latency) automatically -- you write no telemetry code.
OpenAIInstrumentor().instrument()

tracer = trace.get_tracer("support_qa")
client = OpenAI()  # reads OPENAI_API_KEY from the environment


def retrieve(question: str):
    # Retrieval isn't auto-instrumented, so add ONE plain OpenTelemetry span.
    # Still no custom SDK -- just the OTel API + gen_ai.* semantic conventions.
    with tracer.start_as_current_span("retrieve documents") as span:
        span.set_attribute("gen_ai.operation.name", "retrieve")     # -> span_type RETRIEVER
        span.set_attribute("gen_ai.retrieval.vector_store", "pinecone")
        docs = ["billing policy doc", "refund policy doc"]          # your real query here
        span.set_attribute("gen_ai.retrieval.documents_retrieved", len(docs))
        return docs


def answer(question: str) -> str:
    with tracer.start_as_current_span("support_qa") as root:
        root.set_attribute("gen_ai.operation.name", "chain")        # -> span_type CHAIN
        root.set_attribute("gen_ai.workflow.name", "support_qa")
        docs = retrieve(question)
        context = "\n".join(docs)
        # Auto-instrumented: this call emits a gen_ai.* LLM span with tokens/model/latency.
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Use this context:\n{context}"},
                {"role": "user", "content": question},
            ],
        )
        return resp.choices[0].message.content


if __name__ == "__main__":
    for q in ["How do refunds work?", "What payment methods are supported?"]:
        print(f"\nQ: {q}\nA: {answer(q)}")
    trace.get_tracer_provider().shutdown()  # flush spans before exit
    print("\nSent via standard OTLP. In Splunk:  index=genai_traces | head 20")
