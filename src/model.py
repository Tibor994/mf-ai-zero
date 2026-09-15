"""
A MF-AI-Zero modell definíciója.

Ez egy karakter-alapú LSTM nyelvi modell:
  1. Minden karaktert egy vektorra képez le (Embedding réteg).
  2. Az LSTM megjegyzi a korábbi karakterek sorrendjét, mintázatát.
  3. Egy lineáris réteg megjósolja, mi lehet a következő karakter.

Ez a legegyszerűbb "szöveget értő" architektúrák egyike, ezért jó
kiindulópont egy saját, nulláról tanított modellhez.
"""

import torch
import torch.nn as nn


class CharLSTM(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_size, num_layers, dropout=0.0):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            # a rétegek közötti dropout csak 2+ LSTM rétegnél hat, kevesebbnél PyTorch figyelmen kívül hagyja
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, vocab_size)

    def forward(self, x, hidden=None):
        # x alakja: (batch_size, seq_length) - karakter indexek
        embedded = self.embedding(x)                    # (batch, seq, embedding_dim)
        output, hidden = self.lstm(embedded, hidden)     # (batch, seq, hidden_size)
        output = self.dropout(output)
        logits = self.fc(output)                         # (batch, seq, vocab_size)
        return logits, hidden

    def init_hidden(self, batch_size, device):
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        return (h0, c0)
