import json
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

from transformers import (
    AutoTokenizer,
    AutoModel
)

# =========================================================
# LOAD CONFIG
# =========================================================

MODEL_DIR = "HomayShield"

with open(
    f"{MODEL_DIR}/meta.json",
    "r",
    encoding="utf-8"
) as f:

    META = json.load(f)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =========================================================
# SHARED ENCODER
# =========================================================

class SharedEncoder(nn.Module):

    def __init__(self):
        super().__init__()

        self.encoder = AutoModel.from_pretrained(
            META["model_name"]
        )

    def mean_pool(self, hidden, attention_mask):

        mask = attention_mask.unsqueeze(-1).expand(hidden.size()).float()

        masked = hidden * mask

        summed = masked.sum(dim=1)

        counts = mask.sum(dim=1).clamp(min=1e-9)

        return summed / counts

    def forward(self, input_ids, attention_mask):

        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        pooled = self.mean_pool(
            outputs.last_hidden_state,
            attention_mask
        )

        pooled = F.normalize(
            pooled,
            p=2,
            dim=-1
        )

        return pooled

# =========================================================
# CLASSIFIER HEAD
# =========================================================

class ClassifierHead(nn.Module):

    def __init__(self):
        super().__init__()

        self.net = nn.Sequential(

            nn.Linear(768, 256),

            nn.ReLU(),

            nn.Dropout(0.1),

            nn.Linear(256, 1)
        )

    def forward(self, x):

        return self.net(x).squeeze(-1)

# =========================================================
# LOAD MODELS
# =========================================================

tokenizer = AutoTokenizer.from_pretrained(
    f"{MODEL_DIR}/tokenizer"
)

encoder = SharedEncoder().to(DEVICE)

encoder.load_state_dict(
    torch.load(
        f"{MODEL_DIR}/shared_encoder.pt",
        map_location=DEVICE
    )
)

encoder.eval()

head = ClassifierHead().to(DEVICE)

head.load_state_dict(
    torch.load(
        f"{MODEL_DIR}/classifier_head.pt",
        map_location=DEVICE
    )
)

head.eval()

normal_bank = np.load(
    f"{MODEL_DIR}/normal_bank.npy"
)

attack_bank = np.load(
    f"{MODEL_DIR}/attack_bank.npy"
)

# =========================================================
# SEMANTIC GATE
# =========================================================

def semantic_scores(embedding):

    normal_score = np.max(
        normal_bank @ embedding
    )

    attack_score = np.max(
        attack_bank @ embedding
    )

    return normal_score, attack_score

# =========================================================
# INFERENCE
# =========================================================

def predict(text):

    batch = tokenizer(
        text,
        truncation=True,
        max_length=META["max_length"],
        padding=True,
        return_tensors="pt"
    )

    batch = {
        k: v.to(DEVICE)
        for k, v in batch.items()
    }

    with torch.no_grad():

        embedding = encoder(
            batch["input_ids"],
            batch["attention_mask"]
        )

    embedding_np = embedding[0].cpu().numpy()

    normal_score, attack_score = semantic_scores(
        embedding_np
    )

    if attack_score > normal_score + 0.05:

        return {
            "label": "JAILBREAK",
            "decision_source": "semantic_gate",
            "normal_score": float(normal_score),
            "attack_score": float(attack_score)
        }

    with torch.no_grad():

        logit = head(embedding)

        probability = torch.sigmoid(logit).item()

    label = (
        "JAILBREAK"
        if probability >= META["classifier_threshold"]
        else "SAFE"
    )

    return {
        "label": label,
        "decision_source": "classifier",
        "probability_attack": probability,
        "normal_score": float(normal_score),
        "attack_score": float(attack_score)
    }

# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    while True:

        text = input("\nPrompt > ")

        result = predict(text)

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )
