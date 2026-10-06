import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = "catalog.db"
API_KEY = os.environ.get("API_KEY", "devkey")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def check_auth():
    key = request.headers.get("X-API-KEY")
    return key == API_KEY


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


@app.route("/products", methods=["GET"])
def get_products():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401
    conn = get_db()
    rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401
    conn = get_db()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@app.route("/products", methods=["POST"])
def create_product():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json()
    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock")
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        (name, price, stock)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({"id": new_id, "name": name, "price": price, "stock": stock}), 201


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json()
    conn = get_db()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "not found"}), 404

    name = data.get("name", row["name"])
    price = data.get("price", row["price"])
    stock = data.get("stock", row["stock"])

    conn.execute(
        "UPDATE products SET name = ?, price = ?, stock = ? WHERE id = ?",
        (name, price, stock, product_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"id": product_id, "name": name, "price": price, "stock": stock})


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": product_id})


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)