# training_final.py

import os
import json
import random
import argparse
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

from transformers import AutoTokenizer, AutoModel
from torch.utils.data import Dataset, DataLoader


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class JsonDataset(Dataset):
    def __init__(self, rows, tokenizer, max_length=256):
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]

        enc = self.tokenizer(
            row["text"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )

        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "label": torch.tensor(row["label"], dtype=torch.float)
        }


class PairDataset(Dataset):
    def __init__(self, rows, tokenizer, max_length=256):
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_length = max_length

        self.normal = [x for x in rows if x["label"] == 0]
        self.attack = [x for x in rows if x["label"] == 1]

    def __len__(self):
        return len(self.rows)

    def encode(self, text):
        enc = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )
        return enc

    def __getitem__(self, idx):
        anchor = self.rows[idx]

        if random.random() < 0.5:
            other = random.choice(
                self.normal if anchor["label"] == 0 else self.attack
            )
            target = 1
        else:
            other = random.choice(
                self.attack if anchor["label"] == 0 else self.normal
            )
            target = -1

        a = self.encode(anchor["text"])
        b = self.encode(other["text"])

        return {
            "a_input_ids": a["input_ids"].squeeze(0),
            "a_attention_mask": a["attention_mask"].squeeze(0),
            "b_input_ids": b["input_ids"].squeeze(0),
            "b_attention_mask": b["attention_mask"].squeeze(0),
            "target": torch.tensor(target, dtype=torch.float)
        }


class SharedEncoder(nn.Module):
    def __init__(self, model_name):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)

    def mean_pool(self, hidden, mask):
        mask = mask.unsqueeze(-1).expand(hidden.size()).float()
        masked = hidden * mask
        summed = masked.sum(1)
        counts = mask.sum(1).clamp(min=1e-9)
        return summed / counts

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        pooled = self.mean_pool(outputs.last_hidden_state, attention_mask)
        pooled = F.normalize(pooled, p=2, dim=-1)
        return pooled


class ClassifierHead(nn.Module):
    def __init__(self, dim=768):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 1)
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)

            label = row["label"]
            label = 0 if label == "NORMAL" else 1

            rows.append({
                "text": row["text"],
                "label": label
            })
    return rows


def train_encoder(model, loader, device, epochs=2):
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    criterion = nn.CosineEmbeddingLoss(margin=0.2)

    model.train()

    for epoch in range(epochs):
        losses = []

        for batch in loader:
            emb1 = model(
                batch["a_input_ids"].to(device),
                batch["a_attention_mask"].to(device)
            )

            emb2 = model(
                batch["b_input_ids"].to(device),
                batch["b_attention_mask"].to(device)
            )

            loss = criterion(emb1, emb2, batch["target"].to(device))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            losses.append(loss.item())

        print(f"[Encoder Epoch {epoch+1}] Loss: {np.mean(losses):.4f}")


def extract_embeddings(model, loader, device):
    model.eval()

    X = []
    y = []

    with torch.no_grad():
        for batch in loader:
            emb = model(
                batch["input_ids"].to(device),
                batch["attention_mask"].to(device)
            )

            X.append(emb.cpu().numpy())
            y.extend(batch["label"].numpy())

    return np.concatenate(X), np.array(y)


def train_classifier(X_train, y_train, device):
    model = ClassifierHead().to(device)

    X = torch.tensor(X_train).float().to(device)
    y = torch.tensor(y_train).float().to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.BCEWithLogitsLoss()

    for epoch in range(8):
        logits = model(X)
        loss = criterion(logits, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        print(f"[Classifier Epoch {epoch+1}] Loss: {loss.item():.4f}")

    return model


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--train", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-name", default="dbmdz/bert-base-turkish-cased")

    args = parser.parse_args()

    set_seed()

    os.makedirs(args.output_dir, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    rows = []
    for path in args.train:
        print(f"Loading: {path}")
        rows.extend(load_jsonl(path))

    print("Loaded rows:", len(rows))

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    pair_dataset = PairDataset(rows, tokenizer)
    pair_loader = DataLoader(pair_dataset, batch_size=16, shuffle=True)

    encoder = SharedEncoder(args.model_name).to(device)

    print("Training encoder...")
    train_encoder(encoder, pair_loader, device)

    ds = JsonDataset(rows, tokenizer)
    loader = DataLoader(ds, batch_size=16)

    print("Extracting embeddings...")
    X, y = extract_embeddings(encoder, loader, device)

    normal_bank = X[y == 0]
    attack_bank = X[y == 1]

    np.save(
        os.path.join(args.output_dir, "homayshield_normal_bank.npy"),
        normal_bank
    )

    np.save(
        os.path.join(args.output_dir, "homayshield_attack_bank.npy"),
        attack_bank
    )

    torch.save(
        encoder.state_dict(),
        os.path.join(args.output_dir, "homayshield_encoder.pt")
    )

    print("Training classifier...")
    classifier = train_classifier(X, y, device)

    torch.save(
        classifier.state_dict(),
        os.path.join(args.output_dir, "homayshield_classifier.pt")
    )

    print("Training completed.")

if __name__ == "__main__":
    main()
