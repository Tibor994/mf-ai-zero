"""
MF-AI-Zero - v1.4.3 mini Transformer (LAB / candidate modul).

FONTOS - EZ A MODUL KÍSÉRLETI (LAB):
  - A STABIL chat-lánc (chat.py, web/app.py, router.py, guard.py, ...)
    ALAPBÓL NEM használja ezt a modult - a v0.7/v0.7c CharLSTM modellek
    maradnak az éles válaszgenerálás alapja.
  - NEM ír felül semmilyen meglévő modellt - a mini Transformer saját,
    külön névtérben él (models/lab_mini_transformer*.pt).
  - NEM használ külső AI API-t és NEM tölt le előre betanított súlyokat -
    a paraméterek véletlenszerűen inicializálódnak, és KIZÁRÓLAG a helyi
    tanítóadaton tanul, CPU-n, ugyanúgy, mint a CharLSTM (lásd model.py).
  - Lásd docs/v0.9-lab-plan.md a korábbi becslésekért arról, mennyi idő/
    adat kellene egy VALÓBAN versenyképes Transformerhez - ez a modul
    csak az ALAPOKAT (tokenizer, architektúra, tanítás/generálás/mentés-
    betöltés) rakja le, nem cél a CharLSTM-mel való minőségi verseny.

Architektúra: karakter-alapú, dekóder-only (kauzális) Transformer. A
PyTorch beépített nn.TransformerEncoderLayer rétegeit használja kauzális
maszkkal - ez pontosan egy dekóder-only Transformer-réteggel egyenértékű
(a "kauzális maszk" miatt egy pozíció csak a megelőző pozíciókra
figyelhet), csak a PyTorch API history miatt hívják "Encoder"-nek.
"""

import io
import os
import time

import torch
import torch.nn as nn

from tokenizer import CharTokenizer

DEFAULT_D_MODEL = 64
DEFAULT_N_HEADS = 2
DEFAULT_N_LAYERS = 2
DEFAULT_D_FF = 128
DEFAULT_MAX_SEQ_LEN = 128
DEFAULT_DROPOUT = 0.1


class MiniTransformer(nn.Module):
    def __init__(
        self, vocab_size, d_model=DEFAULT_D_MODEL, n_heads=DEFAULT_N_HEADS,
        n_layers=DEFAULT_N_LAYERS, d_ff=DEFAULT_D_FF, max_seq_len=DEFAULT_MAX_SEQ_LEN,
        dropout=DEFAULT_DROPOUT,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff
        self.max_seq_len = max_seq_len
        self.dropout_p = dropout

        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position_embedding = nn.Embedding(max_seq_len, d_model)
        self.embedding_dropout = nn.Dropout(dropout)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_ff,
            dropout=dropout, batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.fc = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        """x: (batch, seq_len) token id-k. Visszaadja a logitokat: (batch,
        seq_len, vocab_size)."""
        batch_size, seq_len = x.shape
        if seq_len > self.max_seq_len:
            raise ValueError(
                f"seq_len ({seq_len}) nagyobb, mint a modell max_seq_len-je ({self.max_seq_len})"
            )
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0).expand(batch_size, seq_len)
        embedded = self.token_embedding(x) + self.position_embedding(positions)
        embedded = self.embedding_dropout(embedded)

        causal_mask = nn.Transformer.generate_square_subsequent_mask(seq_len).to(x.device)
        output = self.transformer(embedded, mask=causal_mask, is_causal=True)
        logits = self.fc(output)
        return logits


@torch.no_grad()
def generate(model, tokenizer, prompt, max_new_tokens=80, temperature=0.8, device=None):
    """Rövid szöveget generál a prompt folytatásaként - egyszerű,
    mintavételezéses (nem legmohóbb) generálás, ugyanaz az elv, mint
    generate.py-ban a CharLSTM-hez."""
    device = device or torch.device("cpu")
    model.eval()
    ids = tokenizer.encode(prompt)
    if not ids:
        return ""

    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    for _ in range(max_new_tokens):
        context = input_ids[:, -model.max_seq_len:]
        logits = model(context)
        next_logits = logits[0, -1] / max(temperature, 1e-6)
        probs = torch.softmax(next_logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1)
        input_ids = torch.cat([input_ids, next_id.unsqueeze(0)], dim=1)

    generated_ids = input_ids[0].tolist()
    return tokenizer.decode(generated_ids)


def save_checkpoint(model, tokenizer, path, extra=None):
    """Atomi mentés (előbb ideiglenes fájlba, majd os.replace) - ugyanaz
    az OneDrive-barát minta, mint train_chat.save_checkpoint()."""
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "vocab_size": model.vocab_size,
        "d_model": model.d_model,
        "n_heads": model.n_heads,
        "n_layers": model.n_layers,
        "d_ff": model.d_ff,
        "max_seq_len": model.max_seq_len,
        "dropout": model.dropout_p,
        "stoi": tokenizer.stoi,
    }
    if extra:
        checkpoint.update(extra)

    buffer = io.BytesIO()
    torch.save(checkpoint, buffer)
    tmp_path = path + ".tmp"
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    attempts, delay_seconds = 10, 2.0
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


def load_checkpoint(path, device=None):
    """Visszaad egy (model, tokenizer) párt egy korábban elmentett LAB
    checkpointból."""
    device = device or torch.device("cpu")
    checkpoint = torch.load(path, map_location=device, weights_only=False)

    tokenizer = CharTokenizer()
    tokenizer.stoi = checkpoint["stoi"]
    tokenizer.itos = {i: ch for ch, i in tokenizer.stoi.items()}

    model = MiniTransformer(
        vocab_size=checkpoint["vocab_size"],
        d_model=checkpoint["d_model"],
        n_heads=checkpoint["n_heads"],
        n_layers=checkpoint["n_layers"],
        d_ff=checkpoint["d_ff"],
        max_seq_len=checkpoint["max_seq_len"],
        dropout=checkpoint.get("dropout", DEFAULT_DROPOUT),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    return model, tokenizer
