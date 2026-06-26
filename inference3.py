import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel


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


def load_models():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model_name = "dbmdz/bert-base-turkish-cased"
    encoder_path = "HomayShield_v5/homayshield_encoder.pt"
    classifier_path = "HomayShield_v5/homayshield_classifier.pt"
    attack_bank_path = "HomayShield_v5/homayshield_attack_bank.npy"

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    encoder = SharedEncoder(model_name).to(device)
    encoder.load_state_dict(torch.load(encoder_path, map_location=device))
    encoder.eval()

    classifier = ClassifierHead().to(device)
    classifier.load_state_dict(torch.load(classifier_path, map_location=device))
    classifier.eval()

    attack_bank = np.load(attack_bank_path)

    return tokenizer, encoder, classifier, attack_bank, device


def encode_text(text, tokenizer, encoder, device):
    batch = tokenizer(
        text,
        truncation=True,
        max_length=256,
        padding="max_length",
        return_tensors="pt"
    )

    batch = {k: v.to(device) for k, v in batch.items()}

    with torch.no_grad():
        emb = encoder(batch["input_ids"], batch["attention_mask"])

    return emb[0].cpu().numpy()


def semantic_score(emb, attack_bank):
    return float(np.max(attack_bank @ emb))


def predict(text, mode, config, tokenizer, encoder, classifier, attack_bank, device):
    emb = encode_text(text, tokenizer, encoder, device)

    attack_score = semantic_score(emb, attack_bank)

    with torch.no_grad():
        x = torch.tensor(emb).float().unsqueeze(0).to(device)
        logits = classifier(x)
        classifier_score = torch.sigmoid(logits).item()

    if mode == "or":
        label = "ATTACK" if (
            attack_score >= config["semantic_threshold"] or
            classifier_score >= config["classifier_threshold"]
        ) else "NORMAL"

    elif mode == "fusion":
        fusion_score = (
            config["semantic_weight"] * attack_score +
            config["classifier_weight"] * classifier_score
        )

        label = "ATTACK" if fusion_score >= config["fusion_threshold"] else "NORMAL"

    elif mode == "semantic_only":
        label = "ATTACK" if attack_score >= config["semantic_threshold"] else "NORMAL"

    elif mode == "classifier_only":
        label = "ATTACK" if classifier_score >= config["classifier_threshold"] else "NORMAL"

    else:
        raise ValueError("Invalid mode")

    return {
        "label": label,
        "semantic_score": attack_score,
        "classifier_score": classifier_score
    }


def ask_mode():
    print("\nSelect Mode:")
    print("1 -> OR")
    print("2 -> Fusion")
    print("3 -> Semantic Only")
    print("4 -> Classifier Only")

    choice = input("Enter choice: ").strip()

    mapping = {
        "1": "or",
        "2": "fusion",
        "3": "semantic_only",
        "4": "classifier_only"
    }

    if choice not in mapping:
        raise ValueError("Invalid choice")

    return mapping[choice]


def ask_thresholds(mode):
    config = {}

    if mode in ["or", "semantic_only"]:
        config["semantic_threshold"] = float(
            input("Semantic threshold (default 0.92): ") or 0.92
        )

    if mode in ["or", "classifier_only"]:
        config["classifier_threshold"] = float(
            input("Classifier threshold (default 0.80): ") or 0.80
        )

    if mode == "fusion":
        config["semantic_weight"] = float(
            input("Semantic weight (default 0.3): ") or 0.3
        )
        config["classifier_weight"] = float(
            input("Classifier weight (default 0.7): ") or 0.7
        )
        config["fusion_threshold"] = float(
            input("Fusion threshold (default 0.75): ") or 0.75
        )

    return config


def main():
    tokenizer, encoder, classifier, attack_bank, device = load_models()

    while True:
        try:
            mode = ask_mode()
            config = ask_thresholds(mode)

            text = input("\nEnter text to analyze:\n")

            result = predict(
                text,
                mode,
                config,
                tokenizer,
                encoder,
                classifier,
                attack_bank,
                device
            )

            print("\n========== RESULT ==========")
            print("Label:", result["label"])
            print("Semantic Score:", result["semantic_score"])
            print("Classifier Score:", result["classifier_score"])

            again = input("\nAnalyze another? (y/n): ").strip().lower()
            if again != "y":
                break

        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
