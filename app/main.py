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
    """
    Liveness check.

    This endpoint only verifies that the application process
    is running and responding.
    """
    return {"status": "healthy"}


@app.get("/ready")
def ready():
    """
    Readiness check.

    Verifies that the application can connect to PostgreSQL.
    Kubernetes uses this endpoint to decide whether the pod
    should receive traffic.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT 1")

        cursor.close()
        connection.close()

        return {"status": "ready"}

    except Exception as error:
        print(f"Readiness check failed: {error}")

        raise HTTPException(
            status_code=503,
            detail="Database is not available",
        )


@app.get("/api/users")
def get_users():
    """
    Fetch users from PostgreSQL.
    """
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, name, email FROM users ORDER BY id"
        )

        users = cursor.fetchall()

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

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
