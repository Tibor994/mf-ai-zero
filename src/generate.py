"""
MF-AI-Zero - szöveggeneráló szkript.

Betölti a betanított modellt (models/mf_ai_zero_best.pt), majd egy
kezdő szövegből (prompt) kiindulva, karakterről karakterre folytatja azt.
A végén megmutatja azt is, hogy a generált mondatok hány százaléka egyezik
szó szerint a tanító adat (data/train.txt) valamelyik sorával - ez a
"bemagolás" egyszerű mérőszáma.

Futtatás:
    python src/generate.py --prompt "Az erő bennem"
    python src/generate.py --prompt "Az erő bennem" --seed 42        # megismételhető kimenet
    python src/generate.py --prompt "Az erő bennem" --sentences 3    # 3 teljes mondat után megáll
"""

import argparse
import os
import re

import torch
import torch.nn.functional as F

import config
from model import CharLSTM

SENTENCE_END_CHARS = {".", "!", "?"}


def parse_args():
    parser = argparse.ArgumentParser(description="Szöveg generálása a MF-AI-Zero modellel.")
    parser.add_argument("--prompt", type=str, default="Az erő bennem", help="Kezdő szöveg.")
    parser.add_argument(
        "--length", type=int, default=config.default_gen_length, help="Generált karakterek száma."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=config.default_temperature,
        help="Kreativitás mértéke (kisebb = óvatosabb, nagyobb = kreatívabb).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Véletlenszám-generátor magja. Ugyanaz a seed + prompt + paraméterek "
        "ugyanazt a generált szöveget adja vissza.",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=config.MODEL_PATH,
        help="Melyik betanított modellfájlt töltse be.",
    )
    parser.add_argument(
        "--sentences",
        type=int,
        default=None,
        help="Ha meg van adva, a generálás ennyi teljes mondat (. ! ? után) "
        "után megáll, még mielőtt elérné a --length határt.",
    )
    return parser.parse_args()


def load_model(device, model_path):
    """Betölt egy checkpointot. A visszaadott prompt_format megmondja, hogy a
    modell önálló mondatokra ("plain", pl. v0.1-v0.4) vagy "User: .../AI:"
    formátumú kérdés-válasz párokra ("chat", v0.7+) lett-e tanítva - ez
    szabja meg, hogyan kell hozzá promptot építeni (lásd chat.py)."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Nem található betanított modell: {model_path}\n"
            "Előbb futtasd: python src/train.py"
        )

    checkpoint = torch.load(model_path, map_location=device)

    model = CharLSTM(
        vocab_size=checkpoint["vocab_size"],
        embedding_dim=checkpoint["embedding_dim"],
        hidden_size=checkpoint["hidden_size"],
        num_layers=checkpoint["num_layers"],
        dropout=checkpoint.get("dropout", 0.0),
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    prompt_format = checkpoint.get("prompt_format", "plain")
    return model, checkpoint["stoi"], checkpoint["itos"], prompt_format


def generate(model, prompt, stoi, itos, length, temperature, device, sentences=None):
    known_chars = [ch for ch in prompt if ch in stoi]
    unknown_chars = sorted(set(prompt) - set(stoi.keys()))
    if unknown_chars:
        print(
            "Figyelem: ezek a karakterek nem szerepelnek a tanító szövegben, "
            f"ezért kimaradnak a promptból: {unknown_chars}"
        )
    if not known_chars:
        raise ValueError(
            "A megadott prompt egyetlen ismert karaktert sem tartalmaz. "
            "Adj meg olyan szöveget, ami a data/train.txt-ben előforduló karakterekből áll."
        )

    input_ids = torch.tensor(
        [[stoi[ch] for ch in known_chars]], dtype=torch.long, device=device
    )

    hidden = None
    generated = list(known_chars)
    sentence_count = 0

    with torch.no_grad():
        # A promptot végigfuttatjuk a modellen, hogy felépüljön a "memóriája" (hidden state).
        logits, hidden = model(input_ids, hidden)

        last_char_id = input_ids[:, -1:]
        for _ in range(length):
            logits, hidden = model(last_char_id, hidden)
            logits = logits[:, -1, :] / max(temperature, 1e-6)
            probs = F.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)

            next_char = itos[next_id.item()]
            generated.append(next_char)

            last_char_id = next_id

            if next_char in SENTENCE_END_CHARS:
                sentence_count += 1
                if sentences is not None and sentence_count >= sentences:
                    break

    return "".join(generated)


def split_into_sentences(text):
    """Szöveget teljes mondatokra bont a mondatvégi írásjelek (. ! ?) mentén."""
    return [s.strip() for s in re.findall(r"[^.!?]*[.!?]", text) if s.strip()]


def load_train_sentences(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def copy_ratio(generated_text, train_sentences):
    """Megmondja, a generált mondatok hány százaléka egyezik szó szerint a
    tanító adat valamelyik sorával - ez a "bemagolás" egyszerű mérőszáma.
    Az eredmény mindig 0 és 100 közé esik (matches sosem lehet negatív vagy
    nagyobb, mint a mondatok száma), de a biztonság kedvéért explicit módon
    is korlátozzuk, nehogy egy jövőbeli módosítás ezt óvatlanul elrontsa."""
    sentences = split_into_sentences(generated_text)
    if not sentences:
        return 0, 0, 0.0
    matches = sum(1 for s in sentences if s in train_sentences)
    percent = max(0.0, min(100.0, 100 * matches / len(sentences)))
    return matches, len(sentences), percent


def main():
    args = parse_args()

    if args.seed is not None:
        torch.manual_seed(args.seed)

    device = torch.device("cpu")
    model, stoi, itos, prompt_format = load_model(device, args.model_path)
    if prompt_format == "chat":
        print(
            "Figyelem: ez egy chat-formátumú modell (User:/AI: párokon tanítva). "
            "A src/generate.py a promptot nyers szövegként adja tovább neki - "
            "kérdés-válasz stílusú beszélgetéshez inkább a src/chat.py-t vagy a "
            "web/app.py-t használd.\n"
        )

    result = generate(
        model=model,
        prompt=args.prompt,
        stoi=stoi,
        itos=itos,
        length=args.length,
        temperature=args.temperature,
        device=device,
        sentences=args.sentences,
    )

    print("\n--- Generált szöveg ---")
    print(result)

    train_sentences = load_train_sentences(config.DATA_PATH)
    matches, total, percent = copy_ratio(result, train_sentences)
    if total > 0:
        print(
            f"\nSzó szerinti egyezés a tanító adattal: {matches}/{total} mondat "
            f"({percent:.0f}%)"
        )


if __name__ == "__main__":
    main()
