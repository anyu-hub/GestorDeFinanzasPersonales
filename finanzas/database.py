import sqlite3

from flask import current_app, g

from finanzas.catalog import CATEGORIES_BY_MODEL, FINANCIAL_MODELS


class Database:
    @staticmethod
    def connect(database_path=None):
        path = database_path or current_app.config["DATABASE"]
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def initialize(database_path=None):
        connection = Database.connect(database_path)
        try:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS financial_models (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    display_name TEXT NOT NULL,
                    model_id INTEGER REFERENCES financial_models(id)
                );
                CREATE TABLE IF NOT EXISTS questionnaires (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    budgeting_style TEXT NOT NULL,
                    income_stability TEXT NOT NULL,
                    savings_priority TEXT NOT NULL,
                    recommended_model_id INTEGER NOT NULL REFERENCES financial_models(id),
                    completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY,
                    model_id INTEGER NOT NULL REFERENCES financial_models(id),
                    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('income', 'expense')),
                    group_name TEXT NOT NULL,
                    name TEXT NOT NULL,
                    UNIQUE (model_id, transaction_type, name)
                );
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    category_id INTEGER NOT NULL REFERENCES categories(id),
                    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('income', 'expense')),
                    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                    transaction_date TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date
                    ON transactions(user_id, transaction_date);
                """
            )
            for model in FINANCIAL_MODELS:
                connection.execute(
                    """INSERT OR IGNORE INTO financial_models (code, name, description)
                       VALUES (?, ?, ?)""",
                    (model["code"], model["name"], model["description"]),
                )
            model_ids = {
                row["code"]: row["id"]
                for row in connection.execute("SELECT id, code FROM financial_models")
            }
            for model_code, categories in CATEGORIES_BY_MODEL.items():
                connection.executemany(
                    """INSERT OR IGNORE INTO categories
                       (model_id, transaction_type, group_name, name)
                       VALUES (?, ?, ?, ?)""",
                    [
                        (model_ids[model_code], transaction_type, group_name, name)
                        for transaction_type, group_name, name in categories
                    ],
                )
            connection.commit()
        finally:
            connection.close()


def get_db():
    if "db" not in g:
        g.db = Database.connect()
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()
