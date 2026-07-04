import json
import os
from pathlib import Path
from flask import Flask, request, jsonify, Response
import anthropic

app = Flask(__name__)
BASE = Path(__file__).parent

# Legge la API key da config.json o dalla variabile d'ambiente
def get_api_key():
    config_path = BASE / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            key = json.load(f).get("api_key", "")
        if key:
            return key
    return os.environ.get("ANTHROPIC_API_KEY", "")

# Pagina principale
@app.route("/")
def index():
    with open(BASE / "index.html", encoding="utf-8") as f:
        return Response(f.read(), mimetype="text/html")

# Genera l'annuncio
@app.route("/genera", methods=["POST"])
def genera():
    dati = request.get_json()

    # Controlla che tutti i campi siano presenti
    campi = ["ruolo", "citta", "titolo", "descrizione"]
    for campo in campi:
        if not dati.get(campo, "").strip():
            return jsonify({"errore": f"Il campo '{campo}' è obbligatorio"}), 400

    # Costruisce il prompt nello stile Jobtech
    prompt = f"""Sei un redattore di annunci di lavoro per Jobtech, agenzia per il lavoro totalmente digitale.
Genera un annuncio che segue esattamente la struttura degli annunci Jobtech.

DATI:
- Ruolo: {dati['ruolo']}
- Città: {dati['citta']}
- Titolo: {dati['titolo']}
- Descrizione: {dati['descrizione']}

STRUTTURA DA SEGUIRE:
1. Prima riga: solo il settore (es. "Settore Ristorazione")
2. Apertura: "Jobtech, agenzia per il lavoro totalmente digitale, è alla ricerca di [ruolo] per conto di [contesto]."
3. "L'opportunità in questione prevede:" con lista puntata (stipendio, contratto, orari, benefit)
4. Paragrafo descrittivo sull'azienda (2-3 righe)
5. "Cosa vorremo trovare in te:" con lista puntata dei requisiti
6. "Di cosa ti occuperai?" con lista puntata delle attività in seconda persona (es. "Gestirai", "Preparerai")
7. Chiusura fissa: "Se pensi che questa possa essere l'opportunità giusta, mandaci la tua candidatura. In Jobtech siamo pronti a dare forma al tuo percorso professionale."

STILE: tono diretto, linguaggio inclusivo, niente aggettivi vuoti."""

    # Chiama Claude API
    api_key = get_api_key()
    if not api_key:
        return jsonify({"errore": "API key non trovata. Aggiungi config.json o imposta ANTHROPIC_API_KEY."}), 500

    try:
        client = anthropic.Anthropic(api_key=api_key)
        risposta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"annuncio": risposta.content[0].text})
    except Exception as e:
        return jsonify({"errore": str(e)}), 500

if __name__ == "__main__":
    print("Server avviato su http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)