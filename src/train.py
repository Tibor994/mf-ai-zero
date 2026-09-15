"""
MF-AI-Zero - tanító szkript.

Ez a szkript:
  1. Beolvassa a data/train.txt fájlt, és a mondatokat train/validation
     részre osztja (alapértelmezetten 90/10 arányban).
  2. Felépíti a karakter-szótárat (vocab): minden egyedi karakterhez
     egy egész számot rendel.
  3. Betanítja a CharLSTM modellt, hogy megjósolja a következő karaktert,
     minden epoch után kiírva a train és a validation loss-t is.
  4. Elmenti azt a modellállapotot, amelyik a legalacsonyabb validation
     loss-t érte el (nem feltétlenül az utolsó epoch-ot) - ez segít
     elkerülni a túltanulást (overfitting). Ha a validation loss sokáig
     (--patience epochig) nem javul, a tanítás korábban leáll.

Futtatás:
    python src/train.py
    python src/train.py --epochs 120 --patience 15 --model-path models/mf_ai_zero_v0_3b_120.pt
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


def parse_args():
    parser = argparse.ArgumentParser(description="A MF-AI-Zero modell tanítása.")
    parser.add_argument(
        "--epochs", type=int, default=config.num_epochs, help="Epoch-ok száma."
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=config.MODEL_PATH,
        help="Hova mentse a betanított modellt.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=None,
        help="Early stopping: ha ennyi egymást követő epoch alatt nem javul a "
        "validation loss, a tanítás korábban leáll. Alapértelmezésben nincs "
        "early stopping.",
    )
    return parser.parse_args()


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_train_val(text, val_split, seed):
    """A szöveget soronként (mondatonként) osztja train/validation részre,
    hogy a validáció valóban a modell számára nem látott mondatokat mérje."""
    lines = [line for line in text.split("\n") if line.strip() != ""]

    order = list(range(len(lines)))
    random.Random(seed).shuffle(order)

    num_val = max(1, int(len(lines) * val_split))
    val_idx = set(order[:num_val])

    train_lines = [lines[i] for i in range(len(lines)) if i not in val_idx]
    val_lines = [lines[i] for i in range(len(lines)) if i in val_idx]

    train_text = "\n".join(train_lines) + "\n"
    val_text = "\n".join(val_lines) + "\n"
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


def save_checkpoint(checkpoint, path, attempts=10, delay_seconds=2.0):
    """A checkpointot előbb memóriába szerializálja, majd egy ideiglenes
    fájlból egy gyors, atomi os.replace-dzsel teszi a helyére. A projekt
    OneDrive-ban van, ami írás közben néha zárolja a célfájlt szinkronizálás
    miatt - ezzel a módszerrel a lassú rész (szerializálás) nem a zárolt
    fájlon történik, csak a végső, pillanatok alatt lezajló csere."""
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


def main():
    args = parse_args()

    random.seed(config.seed)
    torch.manual_seed(config.seed)

    device = torch.device("cpu")
    print(f"Eszköz: {device}")

    if not os.path.exists(config.DATA_PATH):
        raise FileNotFoundError(f"Nem található a tanító szöveg: {config.DATA_PATH}")

    text = load_text(config.DATA_PATH)
    print(f"Betöltött szöveg hossza: {len(text)} karakter")

    # A vocab a teljes szövegből épül, hogy a validációs rész se tartalmazzon
    # a modell számára ismeretlen karaktert.
    stoi, itos = build_vocab(text)
    vocab_size = len(stoi)
    print(f"Szótár mérete (egyedi karakterek): {vocab_size}")

    train_text, val_text = split_train_val(text, config.val_split, config.seed)
    print(f"Train szöveg: {len(train_text)} karakter, validation szöveg: {len(val_text)} karakter")

    min_len = config.seq_length + 1
    if len(train_text) < min_len or len(val_text) < min_len:
        raise ValueError(
            "A train vagy a validation szövegrész túl rövid a beállított seq_length-hez "
            "képest. Adj hozzá több mondatot a data/train.txt fájlhoz, vagy csökkentsd "
            "a seq_length értékét a src/config.py-ban."
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

    print("Tanítás indul...")
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
