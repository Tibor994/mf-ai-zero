"""
MF-AI-Zero - v1.4.3 karakter-alapú tokenizer (LAB modul).

Egy önálló, újrafelhasználható tokenizer osztály - ugyanazt a
karakter-alapú elvet formalizálja, amit a projekt eddig is használt (lásd
train_chat.py build_vocab()/encode()), de külön, tesztelhető modulként, a
mini Transformer laborhoz (lásd mini_transformer.py).

FONTOS: ez a modul NEM változtatja meg a meglévő CharLSTM-es
láncot (train_chat.py, generate.py) - azok továbbra is a saját, belső
szótár-építésüket használják. Ez a tokenizer egy KÜLÖN, a mini
Transformer laborhoz tartozó komponens.

A magyar ékezetes karakterek (á é í ó ö ő ú ü ű és nagybetűs párjaik)
minden külön kezelés nélkül működnek, mert a szótár KÖZVETLENÜL a
tanítószövegből épül - amilyen karakterek ténylegesen előfordulnak a
szövegben, azok kerülnek be a szótárba (UTF-8 kódolással mentve/
betöltve).
"""

import json
import os


class CharTokenizer:
    """Karakter <-> egész szám (token id) megfeleltetés. A szótárat
    build_vocab_from_text() építi fel egy tanítószövegből, vagy
    load()-dal egy korábban elmentett szótárfájlból."""

    def __init__(self):
        self.stoi = {}
        self.itos = {}

    @property
    def vocab_size(self):
        return len(self.stoi)

    def build_vocab_from_text(self, text):
        """Rendezett, egyedi karakterlistából épít szótárat - ugyanaz az
        elv, mint train_chat.build_vocab(), determinisztikus (a rendezés
        miatt mindig ugyanazt az id-kiosztást adja ugyanarra a szövegre)."""
        chars = sorted(set(text or ""))
        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.itos = {i: ch for i, ch in enumerate(chars)}
        return self

    def encode(self, text):
        """Szöveg -> token id lista. Az ismeretlen (a szótárban nem
        szereplő) karaktereket KIHAGYJA - ugyanaz a konvenció, mint amit a
        projekt eddig is használt (lásd generate.py known_prompt szűrés),
        nem dob hibát egy váratlan karakteren."""
        return [self.stoi[ch] for ch in (text or "") if ch in self.stoi]

    def decode(self, ids):
        """Token id lista -> szöveg. Az érvénytelen (szótáron kívüli)
        id-ket kihagyja."""
        return "".join(self.itos[i] for i in ids if i in self.itos)

    def save(self, path):
        """A szótárat (KIZÁRÓLAG a stoi-t, az itos ebből mindig
        visszaépíthető) UTF-8 kódolású JSON fájlba menti - a magyar
        ékezetes karakterek emiatt nem sérülnek (ensure_ascii=False)."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"stoi": self.stoi}, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        tokenizer = cls()
        tokenizer.stoi = data["stoi"]
        tokenizer.itos = {i: ch for ch, i in tokenizer.stoi.items()}
        return tokenizer
