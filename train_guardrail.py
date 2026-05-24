import os
import json
import random
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from torch.utils.data import Dataset, DataLoader

from transformers import (
    AutoTokenizer,
    AutoModel,
    DataCollatorWithPadding
)

# =========================================================
# CONFIG
# =========================================================

@dataclass
class Config:

    model_name = "dbmdz/bert-base-turkish-cased"

    train_file = "datasets/sample.jsonl"

    output_dir = "HomayShield"

    max_length = 256

    device = "cuda" if torch.cuda.is_available() else "cpu"

    encoder_epochs = 2
    classifier_epochs = 5

    encoder_lr = 2e-5
    classifier_lr = 1e-3

    batch_size = 16

    hidden_dim = 256

    dropout = 0.1

    classifier_threshold = 0.5


CFG = Config()

os.makedirs(CFG.output_dir, exist_ok=True)

# =========================================================
# HELPERS
# =========================================================

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

set_seed()

# =========================================================
# LOAD DATASET
# =========================================================

def label_to_binary(label):

    label = label.upper()

    if label in ["SAFE", "NORMAL", "BENIGN"]:
        return 0

    return 1


rows = []

with open(CFG.train_file, "r", encoding="utf-8") as f:

    for line in f:

        obj = json.loads(line)

        rows.append({
            "text": obj["text"],
            "label": label_to_binary(obj["label"])
        })

print(f"Loaded {len(rows)} samples")

# =========================================================
# TOKENIZER
# =========================================================

tokenizer = AutoTokenizer.from_pretrained(CFG.model_name)

# =========================================================
# DATASET
# =========================================================

class PromptDataset(Dataset):

    def __init__(self, rows):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):

        item = self.rows[idx]

        enc = tokenizer(
            item["text"],
            truncation=True,
            max_length=CFG.max_length,
            padding=False
        )

        enc["labels"] = item["label"]

        return enc


class PromptCollator:

    def __init__(self):
        self.base = DataCollatorWithPadding(
            tokenizer=tokenizer,
            return_tensors="pt"
        )

    def __call__(self, features):

        labels = torch.tensor(
            [x.pop("labels") for x in features],
            dtype=torch.float32
        )

        batch = self.base(features)

        batch["labels"] = labels

        return batch

# =========================================================
# SHARED ENCODER
# =========================================================

class SharedEncoder(nn.Module):

    def __init__(self):
        super().__init__()

        self.encoder = AutoModel.from_pretrained(
            CFG.model_name
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

    def __init__(self, input_dim=768):

        super().__init__()

        self.net = nn.Sequential(

            nn.Linear(input_dim, CFG.hidden_dim),

            nn.ReLU(),

            nn.Dropout(CFG.dropout),

            nn.Linear(CFG.hidden_dim, 1)
        )

    def forward(self, x):

        return self.net(x).squeeze(-1)

# =========================================================
# DATALOADER
# =========================================================

dataset = PromptDataset(rows)

loader = DataLoader(
    dataset,
    batch_size=CFG.batch_size,
    shuffle=True,
    collate_fn=PromptCollator()
)

# =========================================================
# TRAIN SHARED ENCODER
# =========================================================

encoder = SharedEncoder().to(CFG.device)

optimizer = torch.optim.AdamW(
    encoder.parameters(),
    lr=CFG.encoder_lr
)

criterion = nn.CosineEmbeddingLoss()

print("Training shared encoder...")

for epoch in range(CFG.encoder_epochs):

    encoder.train()

    losses = []

    for batch in loader:

        input_ids = batch["input_ids"].to(CFG.device)

        attention_mask = batch["attention_mask"].to(CFG.device)

        labels = batch["labels"].to(CFG.device)

        emb = encoder(
            input_ids,
            attention_mask
        )

        shuffled = emb[torch.randperm(len(emb))]

        targets = torch.where(
            labels == labels.flip(0),
            torch.tensor(1.0).to(CFG.device),
            torch.tensor(-1.0).to(CFG.device)
        )

        loss = criterion(
            emb,
            shuffled,
            targets
        )

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

        losses.append(loss.item())

    print(f"Encoder Epoch {epoch+1} Loss {np.mean(losses):.4f}")

# =========================================================
# EXTRACT EMBEDDINGS
# =========================================================

encoder.eval()

embeddings = []
labels_all = []

with torch.no_grad():

    for batch in loader:

        input_ids = batch["input_ids"].to(CFG.device)

        attention_mask = batch["attention_mask"].to(CFG.device)

        emb = encoder(
            input_ids,
            attention_mask
        )

        embeddings.append(emb.cpu())

        labels_all.append(batch["labels"])

X = torch.cat(embeddings).numpy()

y = torch.cat(labels_all).numpy()

# =========================================================
# BUILD SEMANTIC BANKS
# =========================================================

normal_bank = X[y == 0]

attack_bank = X[y == 1]

np.save(
    f"{CFG.output_dir}/normal_bank.npy",
    normal_bank
)

np.save(
    f"{CFG.output_dir}/attack_bank.npy",
    attack_bank
)

# =========================================================
# TRAIN CLASSIFIER HEAD
# =========================================================

head = ClassifierHead().to(CFG.device)

optimizer = torch.optim.AdamW(
    head.parameters(),
    lr=CFG.classifier_lr
)

criterion = nn.BCEWithLogitsLoss()

X_tensor = torch.tensor(X).to(CFG.device)

y_tensor = torch.tensor(y).to(CFG.device)

print("Training classifier head...")

for epoch in range(CFG.classifier_epochs):

    head.train()

    logits = head(X_tensor)

    loss = criterion(
        logits,
        y_tensor
    )

    optimizer.zero_grad()

    loss.backward()

    optimizer.step()

    print(f"Classifier Epoch {epoch+1} Loss {loss.item():.4f}")

# =========================================================
# SAVE
# =========================================================

torch.save(
    encoder.state_dict(),
    f"{CFG.output_dir}/shared_encoder.pt"
)

torch.save(
    head.state_dict(),
    f"{CFG.output_dir}/classifier_head.pt"
)

tokenizer.save_pretrained(
    f"{CFG.output_dir}/tokenizer"
)

meta = {
    "model_name": CFG.model_name,
    "max_length": CFG.max_length,
    "classifier_threshold": CFG.classifier_threshold,
}

with open(
    f"{CFG.output_dir}/meta.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(meta, f, indent=2)

print("Training completed")
