# MF-AI-Zero - Dockerfile Hugging Face Spaces-hez (Docker SDK) vagy bármilyen
# más Docker-alapú hoszthoz. Render-hez NEM kötelező (Render natívan, Docker
# nélkül is tudja futtatni Python projekteket - lásd render.yaml és a
# README "Deploy Renderre" szakasza), de ha valaki mégis Dockerrel akarná
# futtatni Renderen, ez a Dockerfile arra is jó.
#
# A Hugging Face Spaces Docker SDK-ja alapból a 7860-as portot várja, ezért
# azt exportáljuk és arra kötjük a gunicorn-t.

FROM python:3.11-slim

# A Hugging Face Spaces Docker-konténerei nem root felhasználóként, hanem
# UID 1000-es felhasználóként futnak - ezért létrehozunk egy ilyet, és neki
# adjuk a /app mappa tulajdonjogát. Enélkül a conversations/ mappába írás
# (a chat-naplózás) jogosultsági hibával elszállna induláskor.
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

# Csak a requirements.txt-et másoljuk be előbb, hogy a Docker cache-elje a
# pip install réteget, amíg a kód (nem a függőségek) változik. Ez még root
# felhasználóként fut (a pip-nek írnia kell a rendszer site-packages mappát).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

ENV HOST=0.0.0.0
ENV PORT=7860
EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--timeout", "120", "web.app:app"]
