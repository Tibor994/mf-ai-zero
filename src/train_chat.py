"""
MF-AI-Zero - v0.7 chat-tanító szkript.

Ugyanazt a CharLSTM architektúrát és tanítási logikát használja, mint a
train.py, csak más bemeneti adaton (data/chat_train.txt) és más
alapértelmezett kimeneti fájlnévvel (models/mf_ai_zero_chat_v0_7.pt).
A régi (nem-chat) modelleket ez a szkript nem érinti.

A data/chat_train.txt "User: <kérdés>\\nAI: <válasz>" formátumú blokkokból
áll, üres sorral elválasztva. A modell a teljes szöveget - a "User:" és
"AI:" címkékkel együtt - karakterenként tanulja meg, így generáláskor is
ugyanilyen formátumú promptot kell neki adni ("User: <kérdés>\\nAI:"), hogy
a tanult mintát felismerve egy válasszal folytassa, ne csak önálló
motivációs mondatokat írjon (ezt csinálja automatikusan a chat.py / a
web/app.py, ha "chat" formátumú modellt tölt be).

Futtatás:
    python src/train_chat.py
    python src/train_chat.py --epochs 200 --patience 15
"""

import argparse
import io
import os
import random
import time

import torch
import torch.nn as nn

import config
from model import CharLSTM

DEFAULT_CHAT_DATA_PATH = os.path.join(config.BASE_DIR, "data", "chat_train.txt")
DEFAULT_CHAT_MODEL_PATH = os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7.pt")


def parse_args():
    parser = argparse.ArgumentParser(description="A MF-AI-Zero chat-modell tanítása.")
    parser.add_argument(
        "--data-path", type=str, default=DEFAULT_CHAT_DATA_PATH, help="A chat tanító szöveg."
    )
    parser.add_argument("--epochs", type=int, default=config.num_epochs, help="Epoch-ok száma.")
    parser.add_argument(
        "--model-path",
        type=str,
        default=DEFAULT_CHAT_MODEL_PATH,
        help="Hova mentse a betanított chat-modellt.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=None,
        help="Early stopping: ha ennyi egymást követő epoch alatt nem javul a "
        "validation loss, a tanítás korábban leáll.",
    )
    return parser.parse_args()


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_train_val(text, val_split, seed):
    """A szöveget User:/AI: blokkokra (egy-egy kérdés-válasz párra) bontja,
    és ezeket osztja train/validation részre - így egy pár sosem szakad
    ketté a train és a validation adat között."""
    blocks = [b for b in text.split("\n\n") if b.strip()]

    order = list(range(len(blocks)))
    random.Random(seed).shuffle(order)

    num_val = max(1, int(len(blocks) * val_split))
    val_idx = set(order[:num_val])

    train_blocks = [blocks[i] for i in range(len(blocks)) if i not in val_idx]
    val_blocks = [blocks[i] for i in range(len(blocks)) if i in val_idx]

    train_text = "\n\n".join(train_blocks) + "\n"
    val_text = "\n\n".join(val_blocks) + "\n"
    return train_text, val_text


def build_vocab(text):
    chars = sorted(set(text))
    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}
    return stoi, itos


def encode(text, stoi):
    return torch.tensor([stoi[ch] for ch in text], dtype=torch.long)


def get_batch(data, seq_length, batch_size, device):
    """Véletlenszerűen kiválasztott (bemenet, cél) szövegdarabokból batch-et épít."""
    max_start = len(data) - seq_length - 1
    starts = [random.randint(0, max_start) for _ in range(batch_size)]
    x = torch.stack([data[s : s + seq_length] for s in starts])
    y = torch.stack([data[s + 1 : s + seq_length + 1] for s in starts])
    return x.to(device), y.to(device)


@torch.no_grad()
def evaluate(model, data, seq_length, batch_size, device, loss_fn, vocab_size, num_batches=10):
    """Átlagos loss számítása a validációs adaton, tanítás nélkül (dropout kikapcsolva)."""
    model.eval()
    total_loss = 0.0
    for _ in range(num_batches):
        x, y = get_batch(data, seq_length, batch_size, device)
        logits, _ = model(x)
        loss = loss_fn(logits.reshape(-1, vocab_size), y.reshape(-1))
        total_loss += loss.item()
    model.train()
    return total_loss / num_batches


def save_checkpoint(checkpoint, path, attempts=10, delay_seconds=2.0):
    """A checkpointot előbb memóriába szerializálja, majd egy ideiglenes
    fájlból egy gyors, atomi os.replace-dzsel teszi a helyére (OneDrive-
    barát mentés, lásd train.py)."""
    buffer = io.BytesIO()
    torch.save(checkpoint, buffer)
    tmp_path = path + ".tmp"

    for attempt in range(1, attempts + 1):
        try:
            with open(tmp_path, "wb") as f:
                f.write(buffer.getvalue())
            os.replace(tmp_path, path)
            return
        except OSError:
            if attempt == attempts:
                raise
            time.sleep(delay_seconds)


def main():
    args = parse_args()

    random.seed(config.seed)
    torch.manual_seed(config.seed)

    device = torch.device("cpu")
    print(f"Eszköz: {device}")

    if not os.path.exists(args.data_path):
        raise FileNotFoundError(f"Nem található a chat tanító szöveg: {args.data_path}")

    text = load_text(args.data_path)
    print(f"Betöltött chat szöveg hossza: {len(text)} karakter")
    print(f"Kérdés-válasz párok száma: {text.count('User: ')}")

    stoi, itos = build_vocab(text)
    vocab_size = len(stoi)
    print(f"Szótár mérete (egyedi karakterek): {vocab_size}")

    train_text, val_text = split_train_val(text, config.val_split, config.seed)
    print(f"Train szöveg: {len(train_text)} karakter, validation szöveg: {len(val_text)} karakter")

    min_len = config.seq_length + 1
    if len(train_text) < min_len or len(val_text) < min_len:
        raise ValueError(
            "A train vagy a validation szövegrész túl rövid a beállított seq_length-hez "
            "képest. Adj hozzá több kérdés-válasz párt a data/chat_train.txt fájlhoz, "
            "vagy csökkentsd a seq_length értékét a src/config.py-ban."
        )

    train_data = encode(train_text, stoi)
    val_data = encode(val_text, stoi)

    model = CharLSTM(
        vocab_size=vocab_size,
        embedding_dim=config.embedding_dim,
        hidden_size=config.hidden_size,
        num_layers=config.num_layers,
        dropout=config.dropout,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    loss_fn = nn.CrossEntropyLoss()

    steps_per_epoch = max(1, len(train_text) // (config.seq_length * config.batch_size))

    os.makedirs(os.path.dirname(args.model_path), exist_ok=True)
    best_val_loss = float("inf")
    best_train_loss = None
    best_epoch = None
    epochs_since_improvement = 0

    print("Chat tanítás indul...")
    model.train()
    for epoch in range(1, args.epochs + 1):
        epoch_loss = 0.0
        for _ in range(steps_per_epoch):
            x, y = get_batch(train_data, config.seq_length, config.batch_size, device)

            logits, _ = model(x)
            loss = loss_fn(logits.reshape(-1, vocab_size), y.reshape(-1))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        train_loss = epoch_loss / steps_per_epoch
        val_loss = evaluate(
            model, val_data, config.seq_length, config.batch_size, device, loss_fn, vocab_size
        )
        print(
            f"Epoch {epoch}/{args.epochs} - "
            f"train loss: {train_loss:.4f} - validation loss: {val_loss:.4f}"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_train_loss = train_loss
            best_epoch = epoch
            epochs_since_improvement = 0
            checkpoint = {
                "model_state_dict": model.state_dict(),
                "stoi": stoi,
                "itos": itos,
                "vocab_size": vocab_size,
                "embedding_dim": config.embedding_dim,
                "hidden_size": config.hidden_size,
                "num_layers": config.num_layers,
                "dropout": config.dropout,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "epoch": epoch,
                # ez jelzi a generate.py / chat.py számára, hogy ez a modell
                # "User: ...\nAI:" formátumú promptot vár, nem önálló mondatot.
                "prompt_format": "chat",
            }
            save_checkpoint(checkpoint, args.model_path)
            print(f"  -> új legjobb validation loss, modell elmentve: {args.model_path}")
        else:
            epochs_since_improvement += 1
            if args.patience is not None and epochs_since_improvement >= args.patience:
                print(
                    f"Early stopping: {args.patience} epochja nem javult a validation loss, "
                    f"a tanítás leáll a(z) {epoch}. epoch-nál."
                )
                break

    print("\n--- Összegzés ---")
    print(f"Legjobb epoch: {best_epoch}")
    print(f"Train loss (a legjobb epoch-on): {best_train_loss:.4f}")
    print(f"Validation loss (a legjobb epoch-on): {best_val_loss:.4f}")


if __name__ == "__main__":
    main()
