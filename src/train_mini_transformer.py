"""
MF-AI-Zero - v1.4.3 mini Transformer LAB tanító szkript.

FONTOS: ez egy KÍSÉRLETI (LAB) szkript - a kimenete (alapból
models/lab_mini_transformer.pt) NEM a stabil chat-lánc modellje, a
chat.py/web/app.py NEM használja automatikusan, és ez a szkript SOSEM
írja felül a meglévő v0.7/v0.7c/v0.8b_* CharLSTM checkpointokat (külön
névtér, "lab_" előtaggal).

Cél ezzel a körrel: bebizonyítani, hogy a tokenizer + mini Transformer
alapok (lásd tokenizer.py, mini_transformer.py) ténylegesen működnek -
tud tanulni, menteni/betölteni, generálni - NEM az, hogy versenyezzen a
CharLSTM minőségével (lásd docs/v0.9-lab-plan.md a valós idő-/adatigény
becsléséért egy komolyabb kísérlethez).

Futtatás:
    python src/train_mini_transformer.py
    python src/train_mini_transformer.py --epochs 30 --data-path data/chat_train.txt
"""

import argparse
import os
import random

import torch
import torch.nn as nn

import config
from mini_transformer import MiniTransformer, save_checkpoint
from tokenizer import CharTokenizer

DEFAULT_DATA_PATH = os.path.join(config.BASE_DIR, "data", "chat_train.txt")
DEFAULT_MODEL_PATH = os.path.join(config.BASE_DIR, "models", "lab_mini_transformer.pt")


def parse_args():
    parser = argparse.ArgumentParser(description="MF-AI-Zero mini Transformer LAB tanítása (kísérleti).")
    parser.add_argument("--data-path", type=str, default=DEFAULT_DATA_PATH, help="Tanítószöveg.")
    parser.add_argument("--model-path", type=str, default=DEFAULT_MODEL_PATH,
                         help="Hova mentse a LAB checkpointot (SOSEM a stabil modellek helyére).")
    parser.add_argument("--epochs", type=int, default=10, help="Epoch-ok száma (LAB - alacsony alapérték).")
    parser.add_argument("--seq-length", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    return parser.parse_args()


def get_batch(data, seq_length, batch_size, device):
    max_start = len(data) - seq_length - 1
    starts = [random.randint(0, max_start) for _ in range(batch_size)]
    x = torch.stack([data[s: s + seq_length] for s in starts])
    y = torch.stack([data[s + 1: s + seq_length + 1] for s in starts])
    return x.to(device), y.to(device)


def main():
    args = parse_args()
    random.seed(config.seed)
    torch.manual_seed(config.seed)

    device = torch.device("cpu")
    print(f"Eszköz: {device}")
    print("FIGYELEM: ez egy LAB/kísérleti tanítás - a kimenet NEM kerül be a stabil chat-láncba,")
    print("és NEM írja felül a meglévő CharLSTM modelleket.\n")

    if not os.path.exists(args.data_path):
        raise FileNotFoundError(f"Nem található a tanítószöveg: {args.data_path}")

    with open(args.data_path, encoding="utf-8") as f:
        text = f.read()
    print(f"Betöltött szöveg hossza: {len(text)} karakter")

    tokenizer = CharTokenizer().build_vocab_from_text(text)
    print(f"Szótár mérete (egyedi karakterek): {tokenizer.vocab_size}")

    encoded = tokenizer.encode(text)
    data = torch.tensor(encoded, dtype=torch.long)

    min_len = args.seq_length + 1
    if len(data) < min_len * 2:
        raise ValueError("A tanítószöveg túl rövid a beállított seq-length-hez képest.")

    n_val = max(min_len, int(len(data) * 0.1))
    train_data, val_data = data[:-n_val], data[-n_val:]
    print(f"Train adat: {len(train_data)} token, validation adat: {len(val_data)} token")

    model = MiniTransformer(vocab_size=tokenizer.vocab_size, max_seq_len=args.seq_length).to(device)
    param_count = sum(p.numel() for p in model.parameters())
    print(f"Modell paraméterszáma: {param_count:,}")

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.CrossEntropyLoss()

    steps_per_epoch = max(1, len(train_data) // (args.seq_length * args.batch_size))
    os.makedirs(os.path.dirname(args.model_path), exist_ok=True)
    best_val_loss = float("inf")

    print("\nMini Transformer LAB tanítás indul...")
    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_loss = 0.0
        for _ in range(steps_per_epoch):
            x, y = get_batch(train_data, args.seq_length, args.batch_size, device)
            logits = model(x)
            loss = loss_fn(logits.reshape(-1, tokenizer.vocab_size), y.reshape(-1))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        train_loss = epoch_loss / steps_per_epoch

        model.eval()
        with torch.no_grad():
            vx, vy = get_batch(val_data, args.seq_length, args.batch_size, device)
            val_logits = model(vx)
            val_loss = loss_fn(val_logits.reshape(-1, tokenizer.vocab_size), vy.reshape(-1)).item()

        print(f"Epoch {epoch}/{args.epochs} - train loss: {train_loss:.4f} - validation loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            save_checkpoint(
                model, tokenizer, args.model_path,
                extra={"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss, "lab": True},
            )
            print(f"  -> új legjobb validation loss, LAB modell elmentve: {args.model_path}")

    print("\n--- LAB tanítás vége ---")
    print(f"Legjobb validation loss: {best_val_loss:.4f}")
    print("EZ EGY KÍSÉRLETI MODELL - nincs bekötve a stabil chat-láncba.")
    print(f"Kipróbálás: python src/test_mini_transformer_generate.py --model-path {args.model_path}")


if __name__ == "__main__":
    main()
