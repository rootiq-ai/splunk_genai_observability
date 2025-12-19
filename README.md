# GenAI Observability for Splunk

[![Splunkbase](https://img.shields.io/badge/Splunkbase-Published-green)](https://splunkbase.splunk.com/app/YOUR_APP_ID)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
[![Splunk 9.0+](https://img.shields.io/badge/Splunk-9.0+-orange.svg)](https://www.splunk.com/)

**Comprehensive observability solution for LLM and GenAI applications.** Monitor token usage, latency, costs, and errors across OpenAI, Anthropic, and many more providers.
<img width="2472" height="1245" alt="image" src="https://github.com/user-attachments/assets/2a620055-4239-4787-bca3-9f12aa79ecc7" />

---

## Features

- **Real-time Monitoring** - Track LLM calls, RAG pipelines, and AI agents in real-time
- **Token Analytics** - Monitor input/output tokens with automatic extraction
- **Cost Tracking** - Estimate costs with pre-built model pricing lookups
- **Latency Analysis** - View P50, P95, P99 percentiles and latency trends
- **Error Detection** - Identify and debug failing LLM calls
- **Multi-Provider Support** - Works with OpenAI, Anthropic, and many more
- **Pre-built Dashboards** - 5+ ready-to-use dashboards for immediate insights
- **Python SDK** - Simple decorators for easy instrumentation

---

## Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
  - [Splunk App Installation](#1-splunk-app-installation)
  - [Python SDK Installation](#2-python-sdk-installation)
  - [Configure HEC](#3-configure-hec)
- [Usage](#-usage)
  - [Basic Example](#basic-example)
  - [OpenAI Example](#openai-example)
  - [Anthropic Example](#anthropic-example)
  - [RAG Pipeline Example](#rag-pipeline-example)
  - [Agent Example](#agent-example)
- [Decorators Reference](#-decorators-reference)
- [Dashboards](#-dashboards)
- [Configuration](#-configuration)
- [Splunk Queries](#-splunk-queries)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## Quick Start

### 1. Install the App

Download from [Splunkbase](https://splunkbase.splunk.com/app/YOUR_APP_ID) or install manually:

```bash
tar -xzf splunk_genai_observability.tar.gz -C $SPLUNK_HOME/etc/apps/
splunk restart
```

### 2. Install Python SDK

```bash
pip install genai-telemetry
```

### 3. Instrument Your Code

```python
## Prerequisites

- Splunk Enterprise 9.0+ or Splunk Cloud
- HEC (HTTP Event Collector) enabled
- Python 3.8+ (for SDK)

## Installation Steps

### 1. Install the App

Download and install from Splunkbase, or:
```bash
tar -xzf splunk_genai_observability.tar.gz -C $SPLUNK_HOME/etc/apps/
splunk restart
```

### 2. Create Index

Create a new index named `genai_traces`:
Settings → Indexes → New Index
Name: genai_traces

### 3. Configure HEC Token
Settings → Data Inputs → HTTP Event Collector → New Token
Name: genai_traces_token
Index: genai_traces
Sourcetype: genai:trace

### 4. Install Python SDK
```bash
pip install genai-telemetry
```

### 5. Configure Your Application
```python
from genai_telemetry import setup_telemetry, trace_llm
setup_telemetry(
    workflow_name="my-chatbot",
    exporter="splunk",
    splunk_url="https://splunk.company.com:8088",
    splunk_token="your-hec-token",
    splunk_index="genai_traces"
)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat(message):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content

# Telemetry is automatic!
answer = chat("What is the capital of France?")

```

## Verify Installation

Run this search to confirm data is flowing:
index=genai_traces | head 10
```

### 4. View Dashboards

Navigate to **GenAI Observability** app in Splunk and explore the dashboards!

---

## Installation

### 1. Splunk App Installation

#### Option A: From Splunkbase (Recommended)

1. Go to [Splunkbase](https://splunkbase.splunk.com/app/8308)
2. Click **Download**
3. Install via Splunk Web: **Apps → Manage Apps → Install app from file**

#### Option B: Clone from GitHub

```bash
cd $SPLUNK_HOME/etc/apps/
git clone https://github.com/rootiq-ai/splunk_genai_observability.git
$SPLUNK_HOME/bin/splunk restart
```

### 2. Python SDK Installation

```bash
pip install genai-telemetry-splunk
```

### 3. Configure HEC

#### Step 1: Create Index

```
Settings → Indexes → New Index
Name: genai_traces
```

#### Step 2: Enable HEC

```
Settings → Data Inputs → HTTP Event Collector → Global Settings
Enable
```

#### Step 3: Create HEC Token in Splunk

```
Settings → Data Inputs → HTTP Event Collector → New Token
Name: genai_observability
Indexes: genai_traces
Sourcetype: genai:trace
```

#### Step 4: Test HEC Connection

```bash
curl -k https://your-splunk:8088/services/collector/event \
  -H "Authorization: Splunk YOUR_HEC_TOKEN" \
  -d '{"event": "test"}'
```

Expected response:
```json
{"text":"Success","code":0}
```

---

## Usage

### Basic Example

```python
from genai_telemetry import setup_splunk_telemetry, trace_llm, trace_chain
from openai import OpenAI

# Initialize telemetry
setup_splunk_telemetry(
    workflow_name="my-chatbot",
    splunk_hec_url="https://splunk.example.com:8088",
    splunk_hec_token="your-hec-token",
    splunk_index="genai_traces"
)

client = OpenAI()

@trace_llm(model_name="gpt-4o-mini", model_provider="openai")
def chat(message: str):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message}]
    )

# Call the function
response = chat("Hello, how are you?")
print(response.choices[0].message.content)
```

### OpenAI Example

```python
from genai_telemetry import setup_splunk_telemetry, trace_llm, trace_embedding
from openai import OpenAI

setup_splunk_telemetry(
    workflow_name="openai-app",
    splunk_hec_url="https://splunk:8088",
    splunk_hec_token="your-token",
    splunk_index="genai_traces"
)

client = OpenAI()

# Chat completion
@trace_llm(model_name="gpt-4o-mini", model_provider="openai")
def chat(message: str):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": message}]
    )

# Embeddings
@trace_embedding(model="text-embedding-3-small")
def get_embedding(text: str):
    return client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

# Streaming (also supported)
@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat_stream(message: str):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": message}],
        stream=True
    )
```

### Anthropic Example

```python
from genai_telemetry import setup_splunk_telemetry, trace_llm
from anthropic import Anthropic

setup_splunk_telemetry(
    workflow_name="anthropic-app",
    splunk_hec_url="https://splunk:8088",
    splunk_hec_token="your-token",
    splunk_index="genai_traces"
)

client = Anthropic()

@trace_llm(model_name="claude-3-5-sonnet-20241022", model_provider="anthropic")
def chat(message: str):
    return client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": message}]
    )

response = chat("Explain quantum computing")
print(response.content[0].text)
```

### RAG Pipeline Example

```python
from genai_telemetry import (
    setup_splunk_telemetry,
    trace_llm,
    trace_chain,
    trace_retrieval,
    trace_embedding
)
from openai import OpenAI

setup_splunk_telemetry(
    workflow_name="rag-chatbot",
    splunk_hec_url="https://splunk:8088",
    splunk_hec_token="your-token",
    splunk_index="genai_traces"
)

client = OpenAI()

@trace_embedding(model="text-embedding-3-small")
def get_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

@trace_retrieval(vector_store="pinecone", embedding_model="text-embedding-3-small")
def search_documents(query: str, top_k: int = 5):
    # Your vector search logic here
    # Returns list of documents with scores
    return [
        {"text": "Splunk is a data analytics platform", "score": 0.95},
        {"text": "Splunk provides observability solutions", "score": 0.89},
    ]

@trace_llm(model_name="gpt-4o-mini", model_provider="openai")
def generate_answer(context: str, question: str):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Answer based on context:\n{context}"},
            {"role": "user", "content": question}
        ]
    )

@trace_chain(name="rag_pipeline")
def rag(question: str) -> str:
    # 1. Search for relevant documents
    docs = search_documents(question)
    
    # 2. Build context
    context = "\n".join([d["text"] for d in docs])
    
    # 3. Generate answer
    response = generate_answer(context, question)
    
    return response.choices[0].message.content

# Run RAG pipeline
answer = rag("What is Splunk?")
print(answer)
```

### Agent Example

```python
from genai_telemetry import (
    setup_splunk_telemetry,
    trace_llm,
    trace_agent,
    trace_tool
)
from openai import OpenAI
import json

setup_splunk_telemetry(
    workflow_name="ai-agent",
    splunk_hec_url="https://splunk:8088",
    splunk_hec_token="your-token",
    splunk_index="genai_traces"
)

client = OpenAI()

@trace_tool(tool_name="calculator")
def calculator(expression: str) -> str:
    try:
        result = eval(expression)
        return str(result)
    except:
        return "Error: Invalid expression"

@trace_tool(tool_name="weather")
def get_weather(city: str) -> str:
    # Simulated weather API
    return f"Weather in {city}: 72°F, Sunny"

@trace_llm(model_name="gpt-4o-mini", model_provider="openai")
def call_llm(messages: list):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Perform calculations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string"}
                        },
                        "required": ["expression"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "weather",
                    "description": "Get weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"}
                        },
                        "required": ["city"]
                    }
                }
            }
        ]
    )

@trace_agent(agent_name="assistant", agent_type="react")
def agent(question: str, max_steps: int = 5) -> str:
    messages = [{"role": "user", "content": question}]
    
    for step in range(max_steps):
        response = call_llm(messages)
        message = response.choices[0].message
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                if func_name == "calculator":
                    result = calculator(args["expression"])
                elif func_name == "weather":
                    result = get_weather(args["city"])
                
                messages.append(message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            return message.content
    
    return "Max steps reached"

# Run agent
result = agent("What is 25 * 4 and what's the weather in New York?")
print(result)
```

---

## Decorators Reference

| Decorator | Purpose | Key Fields Captured |
|-----------|---------|---------------------|
| `@trace_llm(model_name, model_provider)` | LLM inference calls | input_tokens, output_tokens, duration_ms |
| `@trace_chain(name)` | Pipelines/workflows (starts new trace) | duration_ms, child spans |
| `@trace_retrieval(vector_store, embedding_model)` | Vector search | documents_retrieved, relevance_score |
| `@trace_embedding(model)` | Embedding generation | duration_ms |
| `@trace_tool(tool_name)` | Tool/function calls | duration_ms, result |
| `@trace_agent(agent_name, agent_type)` | Agent executions (starts new trace) | duration_ms, steps |

### Decorator Parameters

#### @trace_llm
```python
@trace_llm(
    model_name="gpt-4o-mini",      # Required: Model name
    model_provider="openai"         # Required: Provider name
)
```

#### @trace_chain
```python
@trace_chain(
    name="my_pipeline"              # Required: Chain/pipeline name
)
```

#### @trace_retrieval
```python
@trace_retrieval(
    vector_store="pinecone",        # Required: Vector store name
    embedding_model="text-embedding-3-small"  # Optional: Embedding model
)
```

---

## Dashboards

### 1. Overview Dashboard
High-level KPIs and trends for all GenAI operations.
<img width="2480" height="1206" alt="image" src="https://github.com/user-attachments/assets/488c7206-9504-4dd6-b68e-0730222b4481" />


### 2. Operations Center
Real-time monitoring with auto-refresh for production systems.
<img width="2484" height="1263" alt="image" src="https://github.com/user-attachments/assets/2c0ec336-a974-4c04-aa81-5be6cf4147d1" />

### 3. LLM Performance
Deep dive into model-level performance metrics.
<img width="2474" height="1275" alt="image" src="https://github.com/user-attachments/assets/fc7f45a8-23fc-4619-b7f7-2300b8d592b1" />


### 4. RAG Analytics
<img width="2484" height="1094" alt="image" src="https://github.com/user-attachments/assets/3c73e920-0ef5-4c98-ad43-f75a1908b5f9" />

### 5. Agents & Tools
<img width="2483" height="1188" alt="image" src="https://github.com/user-attachments/assets/88c7a58b-589f-4ac9-b48b-9020cc2f700d" />


### 6. Cost Analysis
Token usage and cost tracking by model, workflow, and time.
<img width="2478" height="1248" alt="image" src="https://github.com/user-attachments/assets/5bf9c155-b893-43ee-b52c-a5d5446c4085" />


### 7. Error Analysis
Error tracking and debugging for failed LLM calls.
<img width="2480" height="1257" alt="image" src="https://github.com/user-attachments/assets/bd6a5577-ee9c-46c4-a9e7-516721aac769" />


---

## Configuration

### Setup Options

```python
setup_splunk_telemetry(
    # Required
    workflow_name="my-app",              # Application name
    
    # Splunk HEC Configuration
    splunk_hec_url="https://splunk:8088", # HEC endpoint URL
    splunk_hec_token="your-token",        # HEC token
    splunk_index="genai_traces",          # Target index
    splunk_sourcetype="genai:trace",      # Sourcetype (default)
    
    # Optional
    console=False,                        # Also print to console
    file_path=None,                       # Also write to file (JSONL)
    verify_ssl=True,                      # Verify SSL certificates
    batch_size=1,                         # Events per batch (1=immediate)
    flush_interval=5.0                    # Seconds between flushes
)
```

### Environment Variables

```bash
export SPLUNK_HEC_URL="https://splunk:8088"
export SPLUNK_HEC_TOKEN="your-token"
export SPLUNK_INDEX="genai_traces"
export OPENAI_API_KEY="sk-..."
```

```python
import os
from genai_telemetry import setup_splunk_telemetry

setup_splunk_telemetry(
    workflow_name="my-app",
    splunk_hec_url=os.getenv("SPLUNK_HEC_URL"),
    splunk_hec_token=os.getenv("SPLUNK_HEC_TOKEN"),
    splunk_index=os.getenv("SPLUNK_INDEX", "genai_traces")
)
```

---

## Splunk Queries

### Basic Queries

```spl
# All GenAI traces
index=genai_traces

# LLM calls only
index=genai_traces span_type="LLM"

# Errors only
index=genai_traces is_error=1

# Specific workflow
index=genai_traces workflow_name="my-chatbot"
```

### Analytics Queries

```spl
# Token usage by model
index=genai_traces span_type="LLM"
| stats sum(input_tokens) as input, sum(output_tokens) as output by model_name
| eval total = input + output

# Average latency by model
index=genai_traces span_type="LLM"
| stats avg(duration_ms) as avg_latency, 
        perc95(duration_ms) as p95_latency 
  by model_name

# Error rate by workflow
index=genai_traces
| stats count as total, sum(is_error) as errors by workflow_name
| eval error_rate = round((errors/total)*100, 2)

# Cost estimation
index=genai_traces span_type="LLM"
| lookup genai_model_costs model_name OUTPUT input_cost_per_1k, output_cost_per_1k
| eval cost = (input_tokens/1000 * input_cost_per_1k) + (output_tokens/1000 * output_cost_per_1k)
| stats sum(cost) as total_cost by model_name

# Requests per minute
index=genai_traces
| timechart span=1m count as requests
```

### Trace Analysis

```spl
# View complete trace
index=genai_traces trace_id="abc123"
| sort _time
| table _time, span_type, name, duration_ms, status

# Slow traces (>5 seconds)
index=genai_traces span_type="CHAIN"
| where duration_ms > 5000
| table _time, workflow_name, name, duration_ms, trace_id
```

---

## Troubleshooting

### No Data in Splunk

1. **Check HEC is enabled:**
   ```bash
   curl -k https://your-splunk:8088/services/collector/health
   ```

2. **Verify HEC token:**
   ```bash
   curl -k https://your-splunk:8088/services/collector/event \
     -H "Authorization: Splunk YOUR_TOKEN" \
     -d '{"event":"test"}'
   ```

3. **Check index exists:**
   ```spl
   | eventcount index=genai_traces
   ```

4. **Test from Python:**
   ```python
   from genai_telemetry import setup_splunk_telemetry
   
   setup_splunk_telemetry(
       workflow_name="test",
       splunk_hec_url="https://splunk:8088",
       splunk_hec_token="token",
       splunk_index="genai_traces",
       console=True  # Also print to console
   )
   ```

### Zero Token Counts

Return the **full response object**, not just the text:

```python
#  Correct - returns full response
@trace_llm(model_name="gpt-4o-mini", model_provider="openai")
def chat(message: str):
    return client.chat.completions.create(...)

#  Wrong - loses token info
@trace_llm(model_name="gpt-4o-mini", model_provider="openai")
def chat(message: str):
    response = client.chat.completions.create(...)
    return response.choices[0].message.content  # Just text!
```

### Connection Errors

- Use `http://` for non-SSL, `https://` for SSL
- Include port: `:8088`
- Set `verify_ssl=False` for self-signed certificates:
  ```python
  setup_splunk_telemetry(
      ...,
      verify_ssl=False
  )
  ```

### SSL Certificate Errors

```python
setup_splunk_telemetry(
    ...,
    verify_ssl=False  # Disable SSL verification for dev
)
```

### Permission Denied Errors

Ensure HEC token has access to the target index:
```
Settings → Data Inputs → HTTP Event Collector → Your Token → Edit
Allowed Indexes: genai_traces 
```

---

## Project Structure

```
splunk_genai_observability/
├── default/
│   ├── app.conf                    # App metadata
│   ├── props.conf                  # Field extractions
│   ├── transforms.conf             # Lookups configuration
│   ├── macros.conf                 # Search macros
│   ├── indexes.conf                # Index definitions
│   └── data/ui/
│       ├── nav/default.xml         # Navigation menu
│       └── views/                  # Dashboards
│           ├── overview.xml
│           ├── operation_center.xml
│           ├── llm_performance.xml
│           ├── cost_analysis.xml
│           └── error_analysis.xml
├── lookups/
│   ├── genai_model_costs.csv       # Model pricing data
│   └── genai_model_info.csv        # Model metadata
├── metadata/
│   └── default.meta                # Permissions
├── static/
│   ├── appIcon.png                 # App icon (36x36)
├── README.txt
└── LICENSE
```

---

## Roadmap

### Version 1.0 (Current)
- ✅ Basic dashboards
- ✅ Python SDK with decorators
- ✅ Support for OpenAI, Anthropic
- ✅ Token and cost tracking
- ✅ Error monitoring

### Version 2.0 (Planned)
- ⬜ Accelerated data model (10-100x faster queries)
- ⬜ CIM compliance
- ⬜ Alerting templates
- ⬜ Prompt Analytics & Optimization
- ⬜ User analytics & attribution
- ⬜ Enhanced cost analytics
- ⬜ SLA monitoring

### Version 3.0 (Future)
- ⬜ LangChain auto-instrumentation
- ⬜ LlamaIndex integration
- ⬜ Anomaly detection
- ⬜ Cost optimization recommendations

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Kamal Bisht

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 📞 Support

- **GitHub Issues:** [Report a bug](https://github.com/kamalbisht/genai-observability-splunk/issues)
- **Splunkbase:** [App page](https://splunkbase.splunk.com/app/YOUR_APP_ID)
- **PyPI:** [genai-telemetry-splunk](https://pypi.org/project/genai-telemetry-splunk/)

---

## ⭐ Star History

If you find this project useful, please give it a star! ⭐

---

**Made with ❤️ by [Kamal Bisht](https://github.com/kamalbisht)**
