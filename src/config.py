"""
Konfiguráció a MF-AI-Zero karakter-alapú nyelvi modellhez.

Ha "okosabb" modellt szeretnél, itt tudod állítani a méretét
(embedding_dim, hidden_size, num_layers), illetve a tanítás
hosszát (num_epochs).
"""

import os

# --- Elérési utak ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "train.txt")
# Ez mindig az aktuális "legjobb" modellre mutat. Egy kísérleti tanítás
# (pl. --model-path models/mf_ai_zero_v0_4.pt) nem írja felül ezt a fájlt -
# ha egy új verzió jobbnak bizonyul, ezt a pointert kézzel frissítjük rá.
MODEL_PATH = os.path.join(BASE_DIR, "models", "mf_ai_zero_best.pt")
# A v0.7-től kezdve a chat.py és a web/app.py alapból ezt a chat-formátumra
# (User:/AI: párokra) tanított modellt tölti be, nem a fenti MODEL_PATH-ot.
CHAT_MODEL_PATH = os.path.join(BASE_DIR, "models", "mf_ai_zero_chat_v0_7.pt")

# --- Modell méret ---
embedding_dim = 64      # egy karakter vektoros reprezentációjának mérete
hidden_size = 128        # az LSTM rejtett állapotának mérete
num_layers = 2           # egymásra épülő LSTM rétegek száma
dropout = 0.2             # kikapcsolt neuronok aránya tanítás közben (overfitting ellen)

# --- Tanítás ---
seq_length = 64           # hány karaktert lát a modell egyszerre tanítás közben
batch_size = 32
num_epochs = 80
learning_rate = 0.0005
val_split = 0.1           # a mondatok ennyi százaléka legyen validációs adat

# --- Generálás ---
default_gen_length = 200   # hány karaktert generáljon alapértelmezetten
default_temperature = 0.7  # kisebb érték = óvatosabb, nagyobb = kreatívabb szöveg

# --- Egyéb ---
seed = 1337
