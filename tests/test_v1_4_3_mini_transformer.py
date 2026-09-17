"""
MF-AI-Zero - v1.4.3 mini Transformer LAB teszt (tokenizer.py +
mini_transformer.py). Ez a modul KÍSÉRLETI - a tesztek csak azt
igazolják, hogy az ALAPOK (tokenizer, architektúra, tanítás/generálás/
mentés-betöltés) működnek, NEM azt, hogy a stabil chat-láncba be van
kötve (nincs, és ez szándékos - lásd guard.py/chat.py/web/app.py).

Hat rész:
  1. Tokenizer encode/decode kerekítési teszt.
  2. Magyar ékezetes karakterek kezelése.
  3. Vocab save/load teszt.
  4. Mini Transformer forward pass teszt (kimenet alakja/tartalma).
  5. Mini Transformer save/load teszt (determinisztikus kerekítés eval
     módban).
  6. Rövid generálás teszt + a stabil chat-lánc VÁLTOZATLANSÁGÁNAK
     ellenőrzése (a lab modul importja/megléte nem hat a guard.py
     alapértelmezett viselkedésére).

Futtatás:
    python tests/test_v1_4_3_mini_transformer.py
"""

import os
import sys
import tempfile

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

import torch  # noqa: E402

from tokenizer import CharTokenizer  # noqa: E402
from mini_transformer import (  # noqa: E402
    MiniTransformer,
    generate,
    load_checkpoint,
    save_checkpoint,
)

FAILURES = []


def check(label, condition):
    status = "OK" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        FAILURES.append(label)


# ---------------------------------------------------------------------------
# 1) Tokenizer encode/decode kerekítés
# ---------------------------------------------------------------------------
print("--- Tokenizer encode/decode teszt ---")

text = "Szia! Hogy vagy? Ez egy teszt mondat."
tok = CharTokenizer().build_vocab_from_text(text)
check("vocab_size a szöveg egyedi karaktereinek száma", tok.vocab_size == len(set(text)))

ids = tok.encode("Szia!")
check("encode() nem üres listát ad vissza ismert szövegre", len(ids) == len("Szia!"))
check("decode(encode(x)) == x, ha minden karakter ismert", tok.decode(ids) == "Szia!")

ids_unknown = tok.encode("Szia! @@@")
check("encode() kihagyja az ismeretlen karaktereket (nem dob hibát)",
      len(ids_unknown) == len("Szia! ") - 0)  # "@" nincs a szótárban, kimarad

check("üres szöveg encode()-ja üres lista", tok.encode("") == [])
check("üres lista decode()-ja üres string", tok.decode([]) == "")
check("érvénytelen id decode()-nál kimarad, nem hibázik", tok.decode([99999]) == "")


# ---------------------------------------------------------------------------
# 2) Magyar ékezetes karakterek
# ---------------------------------------------------------------------------
print("\n--- Magyar ékezetes karakterek teszt ---")

accented_text = "Árvíztűrő tükörfúrógép - ÁÉÍÓÖŐÚÜŰ áéíóöőúüű"
tok_accented = CharTokenizer().build_vocab_from_text(accented_text)
accented_sample = "Árvíztűrő ŐÚÜŰ"
ids_accented = tok_accented.encode(accented_sample)
check("minden ékezetes karakter bekerül a szótárba",
      all(ch in tok_accented.stoi for ch in accented_sample))
check("ékezetes szöveg encode+decode kerekítése hibátlan",
      tok_accented.decode(ids_accented) == accented_sample)


# ---------------------------------------------------------------------------
# 3) Vocab save/load
# ---------------------------------------------------------------------------
print("\n--- Vocab save/load teszt ---")

with tempfile.TemporaryDirectory() as tmp_dir:
    vocab_path = os.path.join(tmp_dir, "vocab.json")
    tok_accented.save(vocab_path)
    check("a vocab fájl létrejön", os.path.exists(vocab_path))

    loaded_tok = CharTokenizer.load(vocab_path)
    check("betöltés után a vocab_size egyezik", loaded_tok.vocab_size == tok_accented.vocab_size)
    check("betöltés után a stoi tartalma egyezik", loaded_tok.stoi == tok_accented.stoi)
    check("betöltött tokenizerrel az ékezetes szöveg is helyesen kerekít",
          loaded_tok.decode(loaded_tok.encode(accented_sample)) == accented_sample)


# ---------------------------------------------------------------------------
# 4) Mini Transformer forward pass
# ---------------------------------------------------------------------------
print("\n--- Mini Transformer forward pass teszt ---")

model = MiniTransformer(vocab_size=tok.vocab_size, d_model=32, n_heads=2, n_layers=2, d_ff=64, max_seq_len=32)
x = torch.tensor([tok.encode("Szia! Hogy vagy")])
logits = model(x)
check("forward pass kimenet alakja (batch, seq_len, vocab_size)",
      logits.shape == (1, x.shape[1], tok.vocab_size))
check("a kimenet nem tartalmaz NaN/Inf értéket", torch.isfinite(logits).all().item())

param_count = sum(p.numel() for p in model.parameters())
check("a modellnek van tanítható paramétere", param_count > 0)

try:
    too_long = torch.tensor([[0] * 100])
    model(too_long)
    check("túl hosszú szekvenciára hibát dob (max_seq_len védelem)", False)
except ValueError:
    check("túl hosszú szekvenciára hibát dob (max_seq_len védelem)", True)


# ---------------------------------------------------------------------------
# 5) Mini Transformer save/load
# ---------------------------------------------------------------------------
print("\n--- Mini Transformer save/load teszt ---")

with tempfile.TemporaryDirectory() as tmp_dir:
    ckpt_path = os.path.join(tmp_dir, "lab_test.pt")
    save_checkpoint(model, tok, ckpt_path, extra={"epoch": 1, "train_loss": 1.23})
    check("a checkpoint fájl létrejön", os.path.exists(ckpt_path))

    loaded_model, loaded_tokenizer = load_checkpoint(ckpt_path, device=torch.device("cpu"))
    check("betöltött modell vocab_size-a egyezik", loaded_model.vocab_size == model.vocab_size)
    check("betöltött modell d_model-je egyezik", loaded_model.d_model == model.d_model)
    check("betöltött tokenizer stoi-ja egyezik", loaded_tokenizer.stoi == tok.stoi)

    model.eval()
    loaded_model.eval()
    with torch.no_grad():
        original_logits = model(x)
        reloaded_logits = loaded_model(x)
    check("eval módban a betöltött modell PONTOSAN ugyanazt a kimenetet adja, mint az eredeti",
          torch.allclose(original_logits, reloaded_logits))


# ---------------------------------------------------------------------------
# 6) Rövid generálás + a stabil chat-lánc változatlansága
# ---------------------------------------------------------------------------
print("\n--- Rövid generálás teszt + stabil lánc változatlansága ---")

generated = generate(model, tok, "Szia", max_new_tokens=15, temperature=0.8)
check("generate() nem üres stringet ad vissza", isinstance(generated, str) and len(generated) > 0)
check("generate() a prompt-tal kezdődik (a promptot is visszaadja)", generated.startswith("Szia"))

empty_gen = generate(model, tok, "@@@@", max_new_tokens=5)
check("ismeretlen karakterekből álló prompt -> üres string, nem hibázik", empty_gen == "")

# a lab modul megléte/importja NEM változtatja meg a guard.py alapértelmezett
# viselkedését - a guarded_route_and_respond()-nak fogalma sincs a mini
# Transformerről, nincs rá importja/hivatkozása.
import guard  # noqa: E402
check("guard.py NEM importálja/hivatkozza a mini_transformer modult (nincs bekötve)",
      "mini_transformer" not in guard.__dict__ and not hasattr(guard, "MiniTransformer"))


# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
if FAILURES:
    print(f"EREDMÉNY: {len(FAILURES)} teszt megbukott:")
    for f in FAILURES:
        print(f"  - {f}")
    print("STÁTUSZ: NEM STABIL")
else:
    print("EREDMÉNY: minden teszt sikeres.")
    print("STÁTUSZ: STABIL")
print("=" * 60)

if __name__ == "__main__":
    sys.exit(1 if FAILURES else 0)
