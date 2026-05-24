# CPU-Based AI Guardrail System

## Overview

This project is a high-performance CPU-based AI guardrail system designed to detect and block malicious prompts targeting Large Language Models (LLMs).

The architecture was specifically designed for:

* Low-latency inference
* CPU-only deployment
* Enterprise/SOC environments
* Air-gapped systems
* Scalable inference pipelines
* Real-time prompt inspection

The system focuses heavily on:

* Prompt injection detection
* Jailbreak prevention
* Instruction override detection
* Data exfiltration prevention
* Obfuscation attack detection
* Multi-language attack analysis

The guardrail currently supports:

* Turkish prompts
* English prompts
* Mixed Turkish-English prompts

---

# Architecture

The system follows a multi-stage pipeline architecture.

```text
                    +----------------+
User Prompt ------> | Language Detect|
                    +----------------+
                             |
                             v
                  +--------------------+
                  | Semantic Embedding |
                  +--------------------+
                             |
                   Threshold Evaluation
                             |
              +--------------+--------------+
              |                             |
              v                             v
          SAFE PASS                 Suspicious Input
                                            |
                                            v
                                +-------------------+
                                | BERT Classifier   |
                                +-------------------+
                                            |
                                            v
                                    Final Decision
```

---

# Detection Pipeline

## 1. Language Detection

The first stage identifies the language of the incoming prompt.

Supported languages:

* English
* Turkish
* Mixed English/Turkish

Language detection improves:

* Embedding quality
* Classification accuracy
* Token interpretation
* Context understanding

---

## 2. Semantic Embedding Layer

After language detection, the prompt enters the semantic embedding pipeline.

The embedding system performs:

* Semantic similarity analysis
* Contextual representation
* Threat proximity scoring
* Vector-based anomaly evaluation

If the semantic similarity threshold is not exceeded, the request is considered safe and bypasses the expensive classification stage.

This significantly reduces:

* CPU utilization
* Inference latency
* Unnecessary classifier execution

Only suspicious prompts are forwarded to the classifier model.

---

## 3. BERT Classifier

The classifier stage uses a BERT-based architecture selected after extensive benchmark testing.

The model is responsible for:

* Attack classification
* Threat categorization
* Injection detection
* Behavioral analysis
* Risk labeling

The BERT architecture was chosen because it provided the best balance between:

* Accuracy
* CPU performance
* Latency
* Stability
* Multilingual contextual understanding

Benchmark results and performance metrics will be shared in a separate publication.

---

# Shared Transformer Pipeline Design

One of the most important architectural decisions was using a shared transformer pipeline between semantic embedding generation and classifier inference.

Both components share the same preprocessing and transformer backbone until the final separation stage.

This means:

* Same tokenizer
* Same embedding layer
* Same transformer encoder
* Same attention mechanism
* Same contextual understanding path

The separation only occurs at the output stage.

| Step                | BERT Classifier  | Semantic Embedding |
| ------------------- | ---------------- | ------------------ |
| Tokenization        | Same             | Same               |
| Embedding Layer     | Same             | Same               |
| Transformer Encoder | Same             | Same               |
| Pooling             | CLS              | Mean / CLS         |
| Output Layer        | Linear + Softmax | None               |
| Output              | Label            | Vector             |

This architecture provides several advantages:

## Advantages of Shared Pipeline

### Consistent Semantic Understanding

Both systems interpret prompts using identical contextual representations.

### Reduced Computational Overhead

The transformer path is reused efficiently.

### Lower Memory Usage

Shared architecture minimizes duplicated model components.

### Better Detection Stability

Embedding similarity and classifier outputs remain semantically aligned.

### Improved CPU Efficiency

Avoiding separate pipelines significantly reduces resource consumption.

---

# Training Dataset

The models were trained using approximately 600,000 prompts.

The dataset includes:

* English prompts
* Turkish prompts
* Mixed-language prompts
* Benign prompts
* Adversarial prompts
* Multi-turn attack structures

The dataset was intentionally designed to simulate real-world enterprise attacks targeting LLM systems.

---

# Dataset Categories

## 1. Direct Prompt Injection (Jailbreaking)

Detects attempts to bypass AI safety restrictions directly.

Includes:

* DAN attacks
* Developer mode prompts
* Emotional manipulation
* Threat-based prompts
* Research-purpose deception

---

## 2. Instruction Overriding / Goal Hijacking

Detects attempts to replace or override system instructions.

Examples:

* "Ignore previous instructions"
* "You are now another AI"
* Hidden override payloads

---

## 3. System Prompt Leakage Attempts

Designed to prevent internal prompt exposure.

Includes:

* System prompt extraction
* Hidden instruction requests
* Config leakage attempts
* Structured extraction payloads

---

## 4. Data Exfiltration / Sensitive Information Extraction

Critical for enterprise and SOC environments.

Includes:

* Credential requests
* Internal log extraction
* API key harvesting
* Database dump requests
* Memory disclosure attempts

---

## 5. Obfuscation & Encoding Attacks

Designed to bypass traditional keyword filtering.

Includes:

* Base64 encoding
* Hex encoding
* Unicode homoglyphs
* Zero-width characters
* Typoglycemia
* Mixed obfuscation methods

---

## 6. Indirect Prompt Injection (RAG Attacks)

Focuses on malicious external-context injection.

Includes:

* HTML hidden payloads
* Markdown injection
* PDF poisoning
* Email-based payloads
* Invisible instruction embedding

---

## 7. Payload Splitting & Reconstruction Attacks

Detects fragmented malicious logic.

Includes:

* Variable reconstruction
* Multi-stage prompt building
* Puzzle-based attacks
* Distributed payload assembly

---

## 8. Multi-Turn Conversation Attacks

One of the most critical attack classes.

Includes:

* Trust-building attacks
* Gradual escalation
* Delayed instruction override
* Roleplay escalation chains

This dataset includes sequence-based structures instead of isolated prompts.

---

## 9. Contextual Trust Exploitation

Detects fake authority or legitimacy claims.

Examples:

* "I am admin"
* "Authorized request"
* "Internal security audit"

These attacks are especially dangerous in enterprise environments.

---

## 10. Roleplay-Based Attacks

Attempts to bypass restrictions using fictional scenarios.

Includes:

* Simulation environments
* Fictional universes
* Pretend-role prompts
* Story-based jailbreaks

---

## 11. Tool / Function Abuse Prompts

Designed for LLM systems integrated with tools or agents.

Includes:

* Hidden tool invocation
* Unauthorized API calls
* Function execution attempts
* Agent manipulation

---

## 12. Code Injection / Execution Prompts

Detects malicious code execution intent.

Includes:

* Shell payloads
* Python execution prompts
* SQL injection patterns
* Remote execution requests

---

## 13. Cross-Language / Multilingual Attacks

Targets multilingual evasion techniques.

Includes:

* English + Turkish mixed prompts
* Multi-language instruction mixing
* Slang/formal language blending

---

## 14. Adversarial Noise & Perturbation

Attempts to break pattern-based detection systems.

Includes:

* Typo attacks
* Random spacing
* Symbol injection
* Broken grammar structures

---

## 15. Long Context Attacks

Hides malicious payloads inside extremely long prompts.

Includes:

* 1K–10K token inputs
* Hidden mid-context attacks
* Payloads embedded in noise

---

## 16. Ambiguous / Borderline Inputs

Designed to reduce false positives.

Includes:

* Academic discussions
* Security research questions
* Neutral attack discussions

---

## 17. Benign Dataset

Contains normal and safe prompts.

Includes:

* Business requests
* Technical questions
* Daily conversations
* General assistance prompts

---

## 18. Hard Negative Samples

One of the most important dataset categories for improving precision.

Examples:

* "Explain prompt injection"
* "Translate ignore rules"
* Fictional security discussions

These samples look malicious syntactically but are semantically safe.

---

## 19. Policy Boundary Cases

Designed to teach nuanced decision-making.

Includes:

* Ethical discussions
* Gray-area prompts
* Partial policy violations

---

## 20. Output-Based Attacks

Focuses on response-level manipulation.

Includes:

* Hidden message embedding
* Invisible output instructions
* Encoded response payloads

---

## 21. Self-Referential / Meta Attacks

Attempts to confuse reasoning systems.

Includes:

* Recursive prompts
* Logic loops
* Self-analysis traps

---

## 22. Multi-Modal Injection (Future Scope)

Future-proof category for multimodal systems.

Planned support includes:

* OCR-based injection
* Image-hidden prompts
* Audio command injection

---

## 23. Behavioral Labels

Each dataset sample contains structured behavioral metadata.

Example:

```json
{
  "label": "PROMPT_INJECTION",
  "subtype": "INSTRUCTION_OVERRIDE",
  "difficulty": "hard",
  "language": "mixed",
  "multi_turn": false
}
```

These labels improve:

* Fine-grained classification
* Threat analytics
* Benchmarking
* Error analysis
* Future model tuning

---

# Training & Inference Consistency

One of the core design principles of the project is maintaining identical processing logic during both:

* Model training
* Real-time inference

The same preprocessing pipeline is reused end-to-end.

This includes:

* Tokenization
* Attention flow
* Transformer encoding
* Embedding generation
* Pooling strategy

This consistency improves:

* Stability
* Prediction reliability
* Semantic alignment
* Generalization quality

---

# Source Code

The repository includes:

* Training pipeline
* Inference pipeline
* Dataset structure
* Embedding generation logic
* Benchmark scripts
* Evaluation tools
* Model loading system
* Real-time inspection architecture

---

# Future Work

Planned future improvements include:

* Expanded multilingual support
* Multi-modal injection detection
* Quantized ultra-low latency inference
* Distributed guardrail deployment
* Online learning pipelines
* GPU fallback acceleration
* Adaptive threat scoring
* Real-time telemetry dashboards

---

# Conclusion

This project demonstrates that high-quality AI guardrails can be implemented efficiently using CPU-only architectures.

By combining:

* Semantic embeddings
* Shared transformer pipelines
* BERT classification
* Large-scale adversarial datasets
* Real-world attack simulation

it is possible to build scalable and production-ready AI safety systems suitable for enterprise environments.

---

# GitHub Repository

Add your repository link here.

```text
https://github.com/your-username/your-project
```

---

# Author

Darin Mooran

Incident Response | AI Security Engineering | Malware Analysis

## Introduction

As AI systems become more widely deployed, guardrails are becoming a critical component of reliable and secure inference pipelines. Most modern guardrail solutions heavily rely on GPUs or large external services, which can increase infrastructure costs and deployment complexity.

In this project, I focused on building a lightweight **CPU-based guardrail system** designed to work efficiently even in resource-constrained environments.

The goal of this article is to explain:

* Why CPU-based guardrails matter
* The architecture of the system
* Design decisions and tradeoffs
* Performance considerations
* Future improvements

---

# Why CPU-Based Guardrails?

Many AI deployments already dedicate GPUs entirely to model inference. Running additional safety or filtering pipelines on GPUs can:

* Increase latency
* Increase infrastructure cost
* Compete with inference workloads
* Reduce scalability

A CPU-based guardrail system provides several advantages:

## Advantages

### 1. Resource Isolation

Guardrails operate independently from GPU inference workloads.

### 2. Lower Infrastructure Cost

CPU workloads are generally cheaper and easier to scale horizontally.

### 3. Better Deployment Flexibility

The system can run:

* On-premise
* Edge devices
* Virtual machines
* Kubernetes sidecars
* Air-gapped environments

### 4. Improved Stability

Even if GPU inference becomes overloaded, the guardrail layer can continue functioning.

---

# Project Goals

The primary design goals of this project were:

* Low latency
* Minimal memory usage
* CPU-only execution
* Easy integration with existing inference pipelines
* Modular detection architecture
* High throughput under concurrent requests

---

# High-Level Architecture

```text
                +----------------+
User Request -> | Guardrail API  |
                +----------------+
                         |
                         v
               +-------------------+
               | Input Validation  |
               +-------------------+
                         |
                         v
               +-------------------+
               | Risk Detection    |
               +-------------------+
                  |    |      |
                  |    |      |
                  v    v      v
              Regex  Rules  ML/NLP
                  \    |    /
                   \   |   /
                    v  v  v
               +-------------------+
               | Decision Engine   |
               +-------------------+
                         |
          +--------------+--------------+
          |                             |
          v                             v
      Allow                        Block/Flag
```

---

# Core Components

## 1. Input Validation Layer

The first stage validates incoming requests.

Examples:

* Payload size limits
* Encoding validation
* Prompt structure checks
* Injection detection
* Token count limits

This layer is intentionally lightweight to reduce unnecessary processing.

---

## 2. Detection Engine

The detection engine combines multiple strategies.

### Rule-Based Detection

Fast deterministic rules for:

* Prompt injection
* Suspicious keywords
* Policy violations
* System prompt extraction attempts

### Regex-Based Detection

Efficient pattern matching for:

* Encoded payloads
* Obfuscation attempts
* Malicious command structures
* Secrets/API keys

### Lightweight NLP Models

Optional CPU-optimized models for:

* Toxicity detection
* Risk classification
* Contextual analysis

This hybrid approach balances:

* Speed
* Accuracy
* Resource usage

---

## 3. Decision Engine

The decision engine aggregates outputs from all detectors.

Possible outcomes:

* Allow
* Block
* Log only
* Human review
* Risk scoring

Example logic:

```python
if risk_score >= 90:
    action = "block"
elif risk_score >= 60:
    action = "review"
else:
    action = "allow"
```

---

# Performance Considerations

Since the system is CPU-based, optimization is critical.

## Optimizations Used

### Efficient Regex Compilation

Precompiled regex patterns reduce repeated parsing overhead.

### Asynchronous Processing

Non-blocking request handling improves concurrency.

### Batching

Small request batching improves throughput under load.

### Lightweight Models

Smaller quantized NLP models reduce:

* RAM usage
* CPU utilization
* Response latency

### Caching

Frequently observed patterns can be cached to avoid repeated analysis.

---

# Example Workflow

```text
1. User sends prompt
2. Guardrail validates request
3. Detection engine scans input
4. Risk score calculated
5. Decision engine applies policy
6. Request allowed or blocked
```

---

# Deployment Scenarios

This project can be deployed in multiple environments.

## Local AI Inference

Works alongside:

* vLLM
* Ollama
* llama.cpp
* Hugging Face Transformers

## SOC / Security Environments

Can be adapted for:

* Malware analysis filtering
* Security prompt monitoring
* Threat intelligence pipelines
* Internal AI assistants

## Kubernetes

Can run as:

* Sidecar container
* API gateway
* Dedicated microservice

---

# Example Tech Stack

Example technologies that fit this architecture:

| Layer            | Technology                  |
| ---------------- | --------------------------- |
| API              | FastAPI                     |
| Detection        | Python                      |
| NLP              | ONNX Runtime / Transformers |
| Concurrency      | asyncio                     |
| Containerization | Docker                      |
| Deployment       | Kubernetes                  |
| Logging          | ELK / Loki                  |

---

# Challenges

During development, several challenges appeared:

## False Positives

Aggressive filtering can block legitimate prompts.

## Latency Tradeoffs

More advanced analysis increases CPU usage.

## Obfuscation

Attackers may use:

* Encoding
* Prompt splitting
* Indirect instructions
* Multi-stage injections

Balancing detection quality with performance was one of the most important engineering tasks.

---

# Future Improvements

Planned improvements include:

* Semantic similarity detection
* Better contextual understanding
* Adaptive scoring
* Real-time telemetry dashboards
* Distributed rule synchronization
* Multi-language support
* GPU fallback mode

---

# Lessons Learned

Building a CPU-based guardrail system showed that effective AI safety layers do not always require expensive GPU infrastructure.

A carefully designed hybrid architecture using:

* Rules
* Regex
* Lightweight NLP
* Efficient concurrency

can provide strong protection while remaining scalable and cost efficient.

---

# Conclusion

This project demonstrates that CPU-based guardrails are a practical solution for modern AI deployments.

By separating safety logic from GPU inference workloads, organizations can improve:

* Stability
* Scalability
* Security
* Operational cost

while maintaining fast response times.

---

# Author

ASIM YILDIZ

Security Researcher | Incident Response | AI & Security Engineering
