"""
MF-AI-Zero - v0.6 helyi webes chat felület (v0.7e-től routerrel).

Ugyanazt a válaszgenerálási logikát használja, mint a terminálos chat.py -
ez a szkript csak egy böngészős felületet ad köré. A v0.7e-től egy
ROUTER (lásd src/router.py) dönti el minden üzenetnél, melyik modell
válaszoljon: általános beszélgetéshez mindig a v0.7 modell (abban a
legjobb), explicit mondatszám-kéréshez ("Írj 5 mondatot...") pedig a
v0.7c modell (arra specializálták) - méréssel igazolt, hogy ez a
szétválasztás jobb eredményt ad, mint bármelyik modell önmagában.

Nem tanít és nem ír felül semmilyen modellt - csak betölti a meglévő,
már kész checkpointokat. A --model-path / --instruction-model-path
kapcsolókkal más modellek is kiválaszthatók, a --no-router pedig
kikapcsolja az útválasztást (csak --model-path válaszol mindenre) - a
modell képességei és korlátai (lásd src/chat.py fejléce) ugyanazok
maradnak: kicsi, karakter-alapú LSTM, nem igazi chatbot.

Futtatás (csak helyi géphez):
    python web/app.py
    python web/app.py --model-path models/mf_ai_zero_v0_4.pt --no-router

Utána nyisd meg a böngészőben:
    http://localhost:8000

Ideiglenes, más géppel/wifiről történő teszteléshez lásd a README.md
"Barátnak megosztás ideiglenesen" szakaszát - ott a --host 0.0.0.0 és a
TEST_PASSWORD környezeti változó együttes használatát javasoljuk, hogy a
szerver ne legyen teljesen nyitott bárkinek a neten.

Éles/tartós deployhoz (Render, Hugging Face Spaces) lásd a README.md
"Deploy Renderre vagy Hugging Face Spacesre" szakaszát - ott gunicorn
alatt fut ("gunicorn web.app:app"), NEM ezzel a szkripttel közvetlenül.
Ilyenkor a konfiguráció (modell-elérési utak, TEST_PASSWORD) mind
környezeti változóból jön, mert gunicorn nem adja tovább a parancssori
kapcsolóinkat - ezért ez a modul úgy van felépítve, hogy a --kapcsolók
CSAK közvetlen "python web/app.py" futtatáskor érvényesülnek, gunicorn
alatt (amikor a modult importálják, nem __main__-ként futtatják) pedig
kizárólag a környezeti változók (MODEL_PATH, INSTRUCTION_MODEL_PATH,
NO_ROUTER, HOST, PORT) számítanak.
"""

import argparse
import os
import sys
from datetime import datetime

from flask import Flask, Response, jsonify, render_template, request

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

import torch  # noqa: E402

import config  # noqa: E402
from chat import respond  # noqa: E402
from evaluator import evaluate_reply  # noqa: E402
from generate import load_model  # noqa: E402
from guard import guarded_route_and_respond  # noqa: E402
from learning_log import log_feedback  # noqa: E402
from router import detect_intent, route_and_respond  # noqa: E402

ALLOWED_TEMPERATURES = (0.5, 0.6, 0.7)
ALLOWED_SENTENCES = (3, 4, 5, 6)
DEFAULT_TEMPERATURE = 0.7
DEFAULT_SENTENCES = 4

DEFAULT_INSTRUCTION_MODEL_PATH = os.path.join(config.BASE_DIR, "models", "mf_ai_zero_chat_v0_7c.pt")


def _env_bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def resolve_settings():
    """A beállításokat (modell-elérési utak, host, port, router be/ki)
    ELSŐSORBAN környezeti változókból olvassa - ez mindig működik, akár
    közvetlenül futtatjuk a szkriptet, akár gunicorn tölti be WSGI
    alkalmazásként (éles deploy, pl. Render vagy Hugging Face Spaces).

    Ha a szkriptet KÖZVETLENÜL futtatjuk (python web/app.py), a
    parancssori kapcsolók felülírják az env-változós alapértékeket - ez a
    korábbi (v0.7e) viselkedés, változatlanul. Gunicorn alatt a sys.argv
    nem a mi kapcsolóinkat tartalmazza, ezért ilyenkor argparse-ot el
    sem indítjuk, csak a környezeti változókra hagyatkozunk."""
    settings = {
        "model_path": os.environ.get("MODEL_PATH", config.CHAT_MODEL_PATH),
        "instruction_model_path": os.environ.get(
            "INSTRUCTION_MODEL_PATH", DEFAULT_INSTRUCTION_MODEL_PATH
        ),
        "no_router": _env_bool("NO_ROUTER", default=False),
        "no_guard": _env_bool("NO_GUARD", default=False),
        "host": os.environ.get("HOST", "127.0.0.1"),
        "port": int(os.environ.get("PORT", 8000)),
    }

    if __name__ == "__main__":
        parser = argparse.ArgumentParser(description="MF-AI-Zero webes chat felület.")
        parser.add_argument(
            "--model-path",
            type=str,
            default=settings["model_path"],
            help="Melyik modell válaszoljon az ÁLTALÁNOS beszélgetésre (alapértelmezés: "
            "a v0.7 chat-modell, vagy a MODEL_PATH környezeti változó).",
        )
        parser.add_argument(
            "--instruction-model-path",
            type=str,
            default=settings["instruction_model_path"],
            help="Melyik modell válaszoljon a mondatszám-kérésekre (alapértelmezés: "
            "a v0.7c modell, vagy az INSTRUCTION_MODEL_PATH környezeti változó).",
        )
        parser.add_argument(
            "--no-router",
            action="store_true",
            default=settings["no_router"],
            help="Router kikapcsolása: minden üzenetre csak a --model-path modell "
            "válaszol (vagy a NO_ROUTER=1 környezeti változó).",
        )
        parser.add_argument(
            "--no-guard",
            action="store_true",
            default=settings["no_guard"],
            help="A v0.9-guard (kategória-alapú tartalmi őr + retry + kontrollált "
            "fallback, lásd src/guard.py) kikapcsolása - ekkor a router nyers "
            "válasza megy tovább (vagy a NO_GUARD=1 környezeti változó). "
            "--no-router mellett nincs hatása.",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=settings["port"],
            help="Melyik porton induljon a szerver (alapértelmezés: a PORT "
            "környezeti változó, vagy ha az sincs, 8000).",
        )
        parser.add_argument(
            "--host",
            type=str,
            default=settings["host"],
            help="Melyik hoston figyeljen a szerver (alapértelmezés: a HOST "
            "környezeti változó, vagy ha az sincs, 127.0.0.1 - csak a saját géped "
            "éri el). Add meg 0.0.0.0-t, ha más géppel/wifiről is el akarod érni "
            "(lásd README 'Barátnak megosztás ideiglenesen' szakasza) - ilyenkor "
            "MINDENKÉPP állíts be TEST_PASSWORD környezeti változót is.",
        )
        args = parser.parse_args()
        settings.update(vars(args))

    return settings


cli_args_dict = resolve_settings()


class _Settings:
    """Apró wrapper, hogy cli_args_dict["port"] helyett cli_args.port
    írható legyen - megtartja a v0.7e-ből ismerős cli_args.xyz szintaxist."""

    def __init__(self, d):
        self.__dict__.update(d)


cli_args = _Settings(cli_args_dict)

TEST_PASSWORD = os.environ.get("TEST_PASSWORD")
TEST_USERNAME = "friend"

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.before_request
def require_test_password():
    """Ha be van állítva a TEST_PASSWORD környezeti változó, minden kérésnél
    (oldal, statikus fájl, API) HTTP Basic Auth-ot kér - ez egy egyszerű,
    de valódi védelem, ha a szervert 0.0.0.0-n, a helyi hálózaton kívülről
    is elérhetővé teszed (pl. tunnel-en keresztül). Ha nincs beállítva a
    jelszó, a szerver nyitva marad - ez OK tisztán localhost teszteléshez,
    de NEM ajánlott, ha a géped bárhonnan elérhető a neten."""
    if not TEST_PASSWORD:
        return None
    auth = request.authorization
    if not auth or auth.username != TEST_USERNAME or auth.password != TEST_PASSWORD:
        return Response(
            "Jelszó szükséges a beléptetéshez. Kérd el a linket küldő embertől "
            "a felhasználónevet (friend) és a jelszót.",
            401,
            {"WWW-Authenticate": 'Basic realm="MF-AI-Zero teszt"'},
        )
    return None

device = torch.device("cpu")
print("Modell betöltése...")
model, stoi, itos, prompt_format = load_model(device, cli_args.model_path)
print(f"Kész! Általános modell: {cli_args.model_path} (formátum: {prompt_format})")

router_active = not cli_args.no_router
guard_active = router_active and not cli_args.no_guard
instruction_model = None
if router_active:
    i_model, i_stoi, i_itos, i_fmt = load_model(device, cli_args.instruction_model_path)
    instruction_model = (i_model, i_stoi, i_itos, device, i_fmt)
    print(f"Kész! Mondatszám-kérésekhez: {cli_args.instruction_model_path} (formátum: {i_fmt})")

conversations_dir = os.path.join(os.path.dirname(SRC_DIR), "conversations")
os.makedirs(conversations_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
conversation_path = os.path.join(conversations_dir, f"web_conversation_{timestamp}.txt")


def closest_allowed(value, allowed, default):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return min(allowed, key=lambda a: abs(a - value))


def log_exchange(user_message, reply):
    try:
        with open(conversation_path, "a", encoding="utf-8") as f:
            f.write(f"User: {user_message}\n")
            f.write(f"AI: {reply}\n")
    except OSError:
        pass  # a naplózás hibája ne szakítsa meg a beszélgetést


@app.route("/")
def index():
    return render_template(
        "index.html",
        temperatures=ALLOWED_TEMPERATURES,
        sentence_options=ALLOWED_SENTENCES,
        default_temperature=DEFAULT_TEMPERATURE,
        default_sentences=DEFAULT_SENTENCES,
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Üres üzenet."}), 400

    temperature = closest_allowed(data.get("temperature"), ALLOWED_TEMPERATURES, DEFAULT_TEMPERATURE)
    sentences = int(closest_allowed(data.get("sentences"), ALLOWED_SENTENCES, DEFAULT_SENTENCES))

    guard_info = None
    if router_active:
        general_model = (model, stoi, itos, device, prompt_format)
        if guard_active:
            reply, intent, model_used, sentence_info, guard_info = guarded_route_and_respond(
                general_model, instruction_model, user_message, temperature,
                sentence_target=sentences,
            )
        else:
            reply, intent, model_used, sentence_info = route_and_respond(
                general_model, instruction_model, user_message, temperature,
                sentence_target=sentences,
            )
    else:
        reply = respond(
            model, stoi, itos, device, user_message, temperature,
            sentence_target=sentences, prompt_format=prompt_format,
        )
        intent = detect_intent(user_message)
        model_used = cli_args.model_path
        sentence_info = None

    log_exchange(user_message, reply)

    # v0.8: minden választ kiértékelünk (szabályalapú pontozás) és
    # naplózunk - ez CSAK NAPLÓZ, nem tanít és nem módosítja a választ.
    # v0.9-guard: ha a guard aktív volt, a napló a guard_info mezőivel is
    # kiegészül (lásd src/learning_log.py, src/guard.py) - a webes és a
    # terminálos chat ugyanazt a naplóformátumot írja.
    score, flags = evaluate_reply(user_message, reply, intent, sentence_info)
    log_feedback(user_message, reply, intent, model_used, score, flags, sentence_info, guard_info=guard_info)

    return jsonify({
        "reply": reply,
        "temperature": temperature,
        "sentences": sentences,
        "intent": intent,
        "model_used": model_used,
    })


@app.route("/api/clear", methods=["POST"])
def api_clear():
    try:
        with open(conversation_path, "a", encoding="utf-8") as f:
            f.write("--- a felhasználó törölte a beszélgetést a felületen ---\n")
    except OSError:
        pass
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print(f"Beszélgetés naplózása ide: {conversation_path}")
    print(f"Nyisd meg a böngészőben: http://localhost:{cli_args.port}")

    if TEST_PASSWORD:
        print(f"Jelszavas védelem: BEKAPCSOLVA (felhasználónév: {TEST_USERNAME})")
    else:
        print("Jelszavas védelem: KIKAPCSOLVA (nincs TEST_PASSWORD beállítva)")

    if cli_args.host != "127.0.0.1":
        print(f"FIGYELEM: a szerver külső hoston ({cli_args.host}) figyel - a helyi "
              "hálózaton (pl. wifin) bárki elérheti, akinek megadod a gép IP-címét.")
        if not TEST_PASSWORD:
            print("FIGYELEM: nincs jelszó beállítva! Állíts be TEST_PASSWORD "
                  "környezeti változót, mielőtt megosztod a linket - lásd README.")

    app.run(host=cli_args.host, port=cli_args.port, debug=False)
