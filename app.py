"""
Generatore di annunci di lavoro — Backend Flask
Cosmin Hodorogea — Test tecnico Jobtech
"""

import json
import os
from pathlib import Path
from flask import Flask, request, jsonify, Response
import anthropic

app = Flask(__name__, static_folder=".", static_url_path="", template_folder=".")

BASE = Path(__file__).parent


def carica_api_key() -> str:
    config_file = BASE / "config.json"
    if config_file.exists():
        with open(config_file, encoding="utf-8") as f:
            key = json.load(f).get("api_key", "").strip()
        if key:
            return key
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    raise ValueError("API key non trovata. Aggiungi un file config.json con la chiave.")


@app.route("/")
def index():
    html_path = BASE / "index.html"
    with open(html_path, encoding="utf-8") as f:
        return Response(f.read(), mimetype="text/html")


@app.route("/genera", methods=["POST"])
def genera():
    dati = request.get_json()
    ruolo       = dati.get("ruolo", "").strip()
    citta       = dati.get("citta", "").strip()
    titolo      = dati.get("titolo", "").strip()
    descrizione = dati.get("descrizione", "").strip()

    if not all([ruolo, citta, titolo, descrizione]):
        return jsonify({"errore": "Tutti i campi sono obbligatori"}), 400

    try:
        api_key = carica_api_key()
    except ValueError as e:
        return jsonify({"errore": str(e)}), 500

    prompt = f"""Sei un redattore di annunci di lavoro per Jobtech, agenzia per il lavoro totalmente digitale.
Devi generare un annuncio che segue esattamente lo stile e la struttura degli annunci Jobtech.

DATI:
- Ruolo: {ruolo}
- Città: {citta}
- Titolo: {titolo}
- Descrizione: {descrizione}

STRUTTURA ESATTA DA SEGUIRE:

1. Prima riga: solo il settore (es. "Settore Ristorazione" o "Settore IT" ecc.)

2. Paragrafo di apertura: "Jobtech, agenzia per il lavoro totalmente digitale, è alla ricerca di [ruolo] per conto di [descrizione contesto]. Inizia con questa formula esatta.

3. Sezione "L'opportunità in questione prevede:" con lista puntata che include:
   - Stipendio (CCNL di riferimento e livello indicativo)
   - Tipologia contrattuale (tempo determinato/indeterminato, durata)
   - Giorni e orari di lavoro
   - Eventuali agevolazioni o benefit

4. Paragrafo descrittivo sull'azienda o sul contesto lavorativo (2-3 righe).

5. Sezione "Cosa vorremo trovare in te:" con lista puntata dei requisiti richiesti.

6. Sezione "Di cosa ti occuperai?" con lista puntata delle attività principali, usando verbi in seconda persona (es. "Gestirai", "Preparerai", "Utilizzerai").

7. Frase di chiusura fissa: "Se pensi che questa possa essere l'opportunità giusta, mandaci la tua candidatura. In Jobtech siamo pronti a dare forma al tuo percorso professionale."

STILE:
- Tono diretto, umano, non burocratico
- Linguaggio inclusivo con barra (es. "il/la candidato/a", "automunito/a")
- Niente aggettivi vuoti
- Usa esattamente le intestazioni di sezione indicate sopra

Genera solo il testo dell'annuncio, pronto per essere pubblicato."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        testo = risposta.content[0].text
        return jsonify({"annuncio": testo})
    except Exception as e:
        return jsonify({"errore": f"Errore API: {str(e)}"}), 500


if __name__ == "__main__":
    print("\n✅ Server avviato su http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)