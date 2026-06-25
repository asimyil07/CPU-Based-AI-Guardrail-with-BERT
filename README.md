# HomayShield: CPU-Based Guardrail for AI Security

HomayShield is a lightweight CPU-based guardrail designed to protect AI systems against malicious, adversarial, and suspicious inputs in **Turkish and English**.

Unlike modern guardrail systems that rely heavily on Large Language Models (LLMs), HomayShield focuses on practical deployment for companies that cannot afford GPU-heavy infrastructure.

---

# Why This Project?

As AI adoption increases, companies need guardrails to protect:

* LLM applications
* Chatbots
* AI agents
* Web applications
* Internal AI assistants

Modern guardrails often use LLMs for security analysis.

Examples:

* Prompt injection detection
* Jailbreak detection
* Adversarial prompt detection
* Malicious instruction filtering

LLM-based guardrails are powerful.

However, they have major challenges:

* High infrastructure cost
* GPU dependency
* High inference latency
* Complex deployment
* Expensive scaling

Many companies—especially small and mid-sized organizations—cannot deploy GPU-based security systems.

This creates a major security gap.

---

# HomayShield Goal

HomayShield aims to provide a practical alternative:

* CPU-based inference
* No GPU required in production
* Low latency
* Easy deployment
* Lower cost
* Strong baseline security

This project is designed for organizations that need AI security but cannot deploy expensive LLM guardrails.

---

# Important Note

HomayShield is **not intended to replace LLM-based guardrails**.

LLM guardrails generally provide:

* deeper reasoning
* stronger contextual understanding
* better zero-day attack detection

LLM guardrails are usually more powerful.

However, HomayShield offers an important tradeoff:

* lower accuracy than LLM guardrails
* significantly lower cost
* much easier deployment

For many companies, practical deployment matters more than perfect detection.

A CPU-based guardrail is better than having no guardrail.

---

# Core Idea

HomayShield uses a shared encoder architecture.

The encoder runs only once.

The same embedding is reused for:

* Semantic similarity detection
* Classifier prediction

Architecture:

```text
Input
  ↓
Language Detector (TR / EN only)
  ↓
Shared Encoder (run once)
  ↓
Embedding
  ├── Semantic Similarity Engine
  └── Classifier Head
```

This design minimizes compute cost.

Traditional systems may run:

* embedding model
* classifier model
* policy model

HomayShield avoids this by optimizing around a single encoder.

---

# Why Shared Encoder?

The main optimization is simple:

> Run encoder once, use output twice.

This provides:

* lower CPU usage
* faster inference
* lower memory consumption
* easier scaling

This makes HomayShield suitable for:

* on-prem environments
* edge deployments
* CPU-only servers
* enterprise AI pipelines

---

# Supported Languages

Currently supported:

* Turkish
* English

Inference begins with language detection.

If input language is not:

* Turkish (`tr`)
* English (`en`)

Input can be rejected or skipped.

---

# Detection Strategy

HomayShield combines two detection methods.

---

## 1. Semantic Detection

Uses embedding similarity against known attack embeddings.

Good for detecting:

* similar attacks
* adversarial patterns
* prompt injection variants
* semantic anomalies

---

## 2. Classifier Detection

Classifier predicts attack probability.

Good for detecting:

* known attack patterns
* previously learned malicious behavior

---

# Inference Modes

HomayShield supports 3 decision modes.

### Option 1 — OR Logic

```python
if semantic_score >= semantic_threshold or classifier_score >= classifier_threshold:
    ATTACK
else:
    NORMAL
```

---

### Option 2 — Weighted Fusion

```python
fusion_score = semantic_weight * semantic_score + classifier_weight * classifier_score
```

---

### Option 3 — Single Signal

Use either:

* semantic only
  or
* classifier only

---

# Key Philosophy

HomayShield is built around one belief:

> Security should not be limited to companies with GPU infrastructure.

AI security should be practical, deployable, and accessible.

Even without LLMs, strong CPU-based guardrails can provide meaningful protection.
