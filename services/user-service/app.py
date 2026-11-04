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
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(150) UNIQUE NOT NULL
                    )
                """)
            return
        except psycopg.OperationalError:
            if attempt == 29:
                raise
            time.sleep(2)


@app.get("/health")
def health():
    return jsonify({"status": "healthy", "service": "user-service"})


@app.get("/users")
def get_users():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, email FROM users ORDER BY id"
        ).fetchall()

    return jsonify([
        {"id": row[0], "name": row[1], "email": row[2]}
        for row in rows
    ])


@app.post("/users")
def create_user():
    data = request.get_json(silent=True) or {}

    if not data.get("name") or not data.get("email"):
        return jsonify({"error": "name and email are required"}), 400

    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                INSERT INTO users (name, email)
                VALUES (%s, %s)
                RETURNING id, name, email
                """,
                (data["name"], data["email"])
            ).fetchone()

        return jsonify({
            "id": row[0],
            "name": row[1],
            "email": row[2]
        }), 201

    except psycopg.errors.UniqueViolation:
        return jsonify({"error": "email already exists"}), 409


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000)
