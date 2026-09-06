import json
import os
import urllib.error
import urllib.request

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

SCORES = {
    "XS": 1,
    "S": 2,
    "M": 3,
    "L": 5,
    "XL": 8,
}

CATEGORIES = ("business_rules", "interface_elements", "boundaries")
AI_CATEGORIES = ("regras", "interface", "integracoes")
AI_SCORE_LIMITS = range(1, 4)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/options")
def options():
    return jsonify({"scores": SCORES})


@app.post("/api/calculate")
def calculate():
    payload = request.get_json(silent=True) or {}
    selections = payload.get("selections") or {}

    invalid_categories = [category for category in CATEGORIES if selections.get(category) not in SCORES]
    if invalid_categories:
        return jsonify({"error": "Selecione um tamanho válido para todas as categorias."}), 400

    values = {category: SCORES[selections[category]] for category in CATEGORIES}
    return jsonify({"values": values, "total": sum(values.values())})


@app.post("/api/classificar")
def classify():
    payload = request.get_json(silent=True) or {}
    story = (payload.get("story") or "").strip()

    if len(story) < 20:
        return jsonify({"error": "Descreva a história com pelo menos 20 caracteres."}), 400
    if len(story) > 6000:
        return jsonify({"error": "A descrição deve ter no máximo 6.000 caracteres."}), 400

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "A classificação automática está desativada: GEMINI_API_KEY não foi configurada."}), 503

    prompt = f"""Classifique a história de usuário abaixo segundo a matriz BCP.

História:
{story}

Retorne somente JSON válido neste formato exato:
{{
  "regras": {{"nota": 1, "justificativa": "..."}},
  "interface": {{"nota": 1, "justificativa": "..."}},
  "integracoes": {{"nota": 1, "justificativa": "..."}}
}}"""
    system_instruction = """Você é especialista em métricas de software BCP. Classifique cada dimensão com uma nota inteira de 1 a 3.

Regras de negócio: 1 para instruções diretas, fórmulas simples ou validações; 2 para processo iterativo com poucas etapas e decisões; 3 para muitas etapas e/ou muitos pontos de decisão.
Interface: 1 para até 5 elementos estáticos em contexto existente; 2 para até 5 elementos estáticos em novo contexto; 3 para até 5 elementos dinâmicos em novo contexto ou interface sofisticada.
Integrações: 1 quando banco e/ou UI não cruzam fronteiras; 2 para dispositivo físico ou serviço remoto com troca contínua de informação; 3 para serviço remoto com troca eventual ou complexa de informação.

Use apenas evidências presentes na história. Quando uma dimensão não estiver explícita, classifique como 1 e explique a ausência de evidência. Não invente integrações, telas ou regras."""

    try:
        response = _call_gemini(api_key, system_instruction, prompt)
        classification = _validate_classification(response)
    except (ValueError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
        app.logger.warning("Falha na classificação BCP: %s", error)
        return jsonify({"error": "Não foi possível classificar a história agora. Verifique a chave da IA e tente novamente."}), 502

    return jsonify({"classification": classification, "total": sum(item["nota"] for item in classification.values())})


def _call_gemini(api_key, system_instruction, prompt):
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }
    request_data = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(request_data, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("Resposta da IA fora do formato esperado") from error


def _validate_classification(classification):
    if not isinstance(classification, dict) or set(classification) != set(AI_CATEGORIES):
        raise ValueError("Categorias incompletas")

    validated = {}
    for category in AI_CATEGORIES:
        item = classification[category]
        score = item.get("nota") if isinstance(item, dict) else None
        justification = item.get("justificativa") if isinstance(item, dict) else None
        if isinstance(score, bool) or not isinstance(score, int) or score not in AI_SCORE_LIMITS:
            raise ValueError("Nota BCP inválida")
        if not isinstance(justification, str) or not justification.strip():
            raise ValueError("Justificativa BCP ausente")
        validated[category] = {"nota": score, "justificativa": justification.strip()}
    return validated


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
