import os

import psycopg2
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Kubernetes Infrastructure Challenge")


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "password"),
    )


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/users")
def get_users():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, name, email FROM users ORDER BY id"
        )

        users = cursor.fetchall()

        cursor.close()
        connection.close()

        return [
            {
                "id": user[0],
                "name": user[1],
                "email": user[2],
            }
            for user in users
        ]

    except Exception as error:
        print(f"Database connection error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Database connection failed",
        )
