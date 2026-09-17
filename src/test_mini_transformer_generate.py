"""
MF-AI-Zero - v1.4.3 mini Transformer LAB generálási demó.

FONTOS: ez egy KÍSÉRLETI (LAB) szkript, kézi kipróbálásra - NEM a stabil
chat.py helyettesítője, és a chat.py/web/app.py nem hívja automatikusan.
Csak azt mutatja meg, hogy egy korábban betanított LAB checkpointból
(lásd train_mini_transformer.py) ténylegesen lehet szöveget generálni.

Futtatás (előbb futtasd a train_mini_transformer.py-t):
    python src/test_mini_transformer_generate.py
    python src/test_mini_transformer_generate.py --prompt "Szia" --length 100
"""

import argparse
import os

import torch

import config
from mini_transformer import generate, load_checkpoint

DEFAULT_MODEL_PATH = os.path.join(config.BASE_DIR, "models", "lab_mini_transformer.pt")


def parse_args():
    parser = argparse.ArgumentParser(description="MF-AI-Zero mini Transformer LAB generálási demó.")
    parser.add_argument("--model-path", type=str, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--prompt", type=str, default="Szia")
    parser.add_argument("--length", type=int, default=80, help="Generálandó új karakterek száma.")
    parser.add_argument("--temperature", type=float, default=0.8)
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.model_path):
        print(f"Nincs LAB checkpoint itt: {args.model_path}")
        print("Futtasd előbb: python src/train_mini_transformer.py")
        return

    device = torch.device("cpu")
    model, tokenizer = load_checkpoint(args.model_path, device=device)
    print(f"LAB modell betöltve: {args.model_path} (szótár mérete: {tokenizer.vocab_size})")
    print("FIGYELEM: ez egy kísérleti modell, NEM a stabil chat-lánc.\n")

    text = generate(
        model, tokenizer, args.prompt,
        max_new_tokens=args.length, temperature=args.temperature, device=device,
    )
    print(f"Prompt: {args.prompt!r}")
    print(f"Generált szöveg: {text!r}")


if __name__ == "__main__":
    main()
