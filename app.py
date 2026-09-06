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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
