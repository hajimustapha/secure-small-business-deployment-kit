
import os
import psycopg
from flask import Flask, request

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200




def get_db_password():
    secret_file = os.getenv(
        "DB_PASSWORD_FILE",
        "/run/secrets/db_password"
    )

    with open(secret_file, "r", encoding="utf-8") as file:
        return file.read().rstrip("\r\n")
    
def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=get_db_password(),
        connect_timeout=5
    )

@app.route("/notes", methods=["GET"])
def get_notes():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, content, created_at
                    FROM notes
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

        return {
            "notes": [
                {
                    "id": row[0],
                    "content": row[1],
                    "created_at": row[2].isoformat()
                }
                for row in rows
            ]
        }, 200

    except psycopg.Error:
        app.logger.exception("Failed to retrieve notes")
        return {"error": "Database unavailable"}, 503


@app.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "Expected a JSON object"}, 400

    content = data.get("content")

    if not isinstance(content, str) or not content.strip():
        return {"error": "Content must be a non-empty string"}, 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO notes (content)
                    VALUES (%s)
                    RETURNING id, content, created_at
                    """,
                    (content.strip(),)
                )
                row = cur.fetchone()

        return {
            "id": row[0],
            "content": row[1],
            "created_at": row[2].isoformat()
        }, 201

    except psycopg.Error:
        app.logger.exception("Failed to create note")
        return {"error": "Database unavailable"}, 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
