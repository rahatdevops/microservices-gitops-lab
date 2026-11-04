import os
import time

import psycopg
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "microservices")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "changeme")


def get_connection():
    return psycopg.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=3
    )


def initialize_database():
    for attempt in range(30):
        try:
            with get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        product VARCHAR(100) NOT NULL,
                        quantity INTEGER NOT NULL
                    )
                """)
            return
        except psycopg.OperationalError:
            if attempt == 29:
                raise
            time.sleep(2)


@app.get("/health")
def health():
    return jsonify({"status": "healthy", "service": "order-service"})


@app.get("/orders")
def get_orders():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, user_id, product, quantity FROM orders ORDER BY id"
        ).fetchall()

    return jsonify([
        {
            "id": row[0],
            "user_id": row[1],
            "product": row[2],
            "quantity": row[3]
        }
        for row in rows
    ])


@app.post("/orders")
def create_order():
    data = request.get_json(silent=True) or {}

    if not data.get("user_id") or not data.get("product"):
        return jsonify({"error": "user_id and product are required"}), 400

    quantity = data.get("quantity", 1)

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO orders (user_id, product, quantity)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, product, quantity
            """,
            (data["user_id"], data["product"], quantity)
        ).fetchone()

    return jsonify({
        "id": row[0],
        "user_id": row[1],
        "product": row[2],
        "quantity": row[3]
    }), 201


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000)
