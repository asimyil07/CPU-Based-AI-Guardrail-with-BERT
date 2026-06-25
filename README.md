# HomayShield: CPU-Based AI Guardrail for Turkish & English Security Filtering

HomayShield is a lightweight **CPU-based AI guardrail system** designed to detect malicious, adversarial, and suspicious inputs targeting AI systems.

The project focuses on providing practical AI security for organizations that **cannot deploy GPU-heavy guardrail solutions**.

Supported languages:

* Turkish
* English
* Mixed Turkish-English prompts

---

# Why HomayShield?

As AI adoption grows, organizations increasingly deploy:

* LLM applications
* Chatbots
* AI agents
* RAG systems
* Internal AI assistants
* Web-integrated AI pipelines

These systems introduce new attack surfaces.

Examples include:

* Prompt injection
* Jailbreak attacks
* Instruction override
* Data exfiltration
* Tool abuse
* Indirect prompt injection

Modern guardrails often rely on LLM-based security analysis.

These systems are powerful, but they introduce major operational challenges:

* High infrastructure cost
* GPU dependency
* High inference latency
* Expensive scaling
* Complex deployment

Many small and mid-sized organizations cannot afford dedicated GPU infrastructure for security layers.

This creates a major security gap.

---

# Project Goal

HomayShield aims to provide a practical alternative.

Main objectives:

* CPU-based inference
* Low latency
* No GPU requirement in production
* Easy enterprise deployment
* Lower operational cost
* Strong baseline AI security

HomayShield is designed for:

* SOC environments
* Enterprise AI systems
* Air-gapped systems
* On-prem deployments
* CPU-only environments

---

# Important Note

HomayShield is **not intended to replace LLM-based guardrails**.

LLM guardrails typically provide:

* deeper reasoning
* better contextual understanding
* stronger zero-day detection
* more adaptive behavior

In most scenarios, LLM-based guardrails are more powerful.

However, HomayShield offers an important tradeoff:

* lower detection capability than advanced LLM guardrails
* significantly lower infrastructure cost
* much easier deployment
* much faster CPU inference

For many organizations, deployability matters.

> A CPU-based guardrail is better than having no guardrail.

---

# Core Architecture

HomayShield is built around one key principle:

> Run encoder once. Use output twice.

A single shared encoder generates embeddings used by both:

* Semantic similarity detection
* Classifier prediction

Architecture:

```text
Input Prompt
    ↓
Language Detector (TR / EN)
    ↓
Shared Encoder (Single Pass)
    ↓
Embedding
 ┌───────────────┴───────────────┐
 ↓                               ↓
Semantic Similarity         Classifier Head
 ↓                               ↓
Semantic Score              Classifier Score
          ↓
     Decision Engine
          ↓
   ATTACK / NORMAL
```

This architecture minimizes compute cost and reduces latency.

---

# Why Shared Encoder?

Traditional guardrail systems may run:

* Language model
* Embedding model
* Classifier model
* Policy model

This increases:

* CPU/GPU utilization
* latency
* memory consumption
* infrastructure complexity

HomayShield avoids this by sharing the encoder.

Advantages:

* Lower CPU usage
* Faster inference
* Lower memory footprint
* Better scalability
* Consistent semantic representation

---

# Supported Languages

Current supported languages:

* Turkish (`tr`)
* English (`en`)

Inference begins with language detection.

If input language is unsupported:

* Reject
  or
* Skip evaluation

---

# Detection Strategy

HomayShield combines two detection mechanisms.

---

## 1) Semantic Detection

Semantic similarity compares incoming prompt embeddings against known malicious attack embeddings.

Useful for detecting:

* similar attacks
* prompt injection variants
* jailbreak attempts
* semantic anomalies
* adversarial patterns

---

## 2) Classifier Detection

Classifier predicts attack probability using shared embeddings.

Useful for detecting:

* known attack patterns
* learned malicious behavior
* structured adversarial prompts

---

# Inference Modes

HomayShield supports 3 inference strategies.

---

## Option 1 — OR Logic

Security-first mode.

```python
if semantic_score >= semantic_threshold or classifier_score >= classifier_threshold:
    ATTACK
else:
    NORMAL
```

Best for:

* strict environments
* low false negatives

---

## Option 2 — Weighted Fusion

Balanced mode.

```python
fusion_score = semantic_weight * semantic_score + classifier_weight * classifier_score
```

Best for:

* balanced security
* tunable sensitivity

---

## Option 3 — Single Signal

Choose one:

* semantic only
* classifier only

Useful for benchmarking or lightweight deployments.

---

# Training Pipeline

Training consists of 2 stages.

---

## Stage 1 — Encoder Training

The encoder is trained using similarity learning.

Goal:

* similar attacks cluster together
* similar normal prompts cluster together
* attacks and normal prompts separate clearly

Loss:

```text
CosineEmbeddingLoss
```

---

## Stage 2 — Classifier Training

After encoder training:

* embeddings are extracted
* classifier head is trained on embeddings

Loss:

```text
BCEWithLogitsLoss
```

Outputs:

* trained encoder
* trained classifier
* attack embedding bank
* normal embedding bank

---

# Training Command

```bash
python training_final.py \
  --train /home/asimyil/train.jsonl \
  --output-dir /home/asimyil/HomayShield_v5
```

---

# Training Dataset

HomayShield was trained using a large dataset of:

* benign prompts
* adversarial prompts
* Turkish prompts
* English prompts
* mixed-language prompts

Dataset includes attack categories such as:

* Direct prompt injection
* Jailbreak attacks
* Instruction override
* Prompt leakage
* Data exfiltration
* Obfuscation attacks
* Multi-turn attacks
* Roleplay attacks
* Tool abuse
* Code injection
* Long context attacks
* Hard negative samples

This helps improve detection robustness in real-world enterprise environments.

---

# Training Dataset Format

JSONL example:

```json
{"text":"normal request","label":"NORMAL"}
{"text":"ignore previous instructions","label":"ATTACK"}
```

---

# Generated Files

Training produces:

```text
homayshield_encoder.pt
homayshield_classifier.pt
homayshield_attack_bank.npy
homayshield_normal_bank.npy
```

---

# Hugging Face Artifacts

Pretrained artifacts will be shared on Hugging Face.

## Encoder

HF_ENCODER_URL

## Classifier

HF_CLASSIFIER_URL

## Attack Embeddings

HF_ATTACK_BANK_URL

---

# Inference Commands

## Option 1 — OR Logic

```bash
python inference_hybrid.py \
  --input test.jsonl \
  --output pred.jsonl \
  --encoder homayshield_encoder.pt \
  --classifier homayshield_classifier.pt \
  --attack-embeddings homayshield_attack_bank.npy \
  --mode or \
  --semantic-threshold 0.92 \
  --classifier-threshold 0.80
```

---

## Option 2 — Weighted Fusion

```bash
python inference_hybrid.py \
  --input test.jsonl \
  --output pred.jsonl \
  --encoder homayshield_encoder.pt \
  --classifier homayshield_classifier.pt \
  --attack-embeddings homayshield_attack_bank.npy \
  --mode fusion \
  --semantic-weight 0.4 \
  --classifier-weight 0.6 \
  --fusion-threshold 0.75
```

---

## Option 3A — Semantic Only

```bash
python inference_hybrid.py \
  --input test.jsonl \
  --output pred.jsonl \
  --encoder homayshield_encoder.pt \
  --classifier homayshield_classifier.pt \
  --attack-embeddings homayshield_attack_bank.npy \
  --mode semantic_only \
  --semantic-threshold 0.92
```

---

## Option 3B — Classifier Only

```bash
python inference_hybrid.py \
  --input test.jsonl \
  --output pred.jsonl \
  --encoder homayshield_encoder.pt \
  --classifier homayshield_classifier.pt \
  --attack-embeddings homayshield_attack_bank.npy \
  --mode classifier_only \
  --classifier-threshold 0.80
```

---

# Use Cases

HomayShield can be used for:

* LLM guardrails
* Prompt injection detection
* Jailbreak prevention
* Adversarial prompt detection
* AI chatbot protection
* SOC automation
* Enterprise AI security

---

# Future Work

Planned improvements:

* ONNX export
* Quantized inference
* Distilled encoder versions
* Faster CPU optimization
* Extended multilingual support
* Real-time streaming inference
* Optional LLM fallback for high-risk prompts

---

# Key Philosophy

HomayShield is built around one core belief:

> AI security should not be limited to organizations with GPU infrastructure.

Security should be:

* practical
* deployable
* efficient
* accessible

Even without LLMs, optimized CPU-based guardrails can provide meaningful protection for real-world AI systems.

---

# Author

**ASIM YILDIZ**
Security Researcher | Incident Response | AI & Security Engineering
