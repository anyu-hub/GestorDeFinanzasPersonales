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
                    owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('income', 'expense')),
                    group_name TEXT NOT NULL,
                    name TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    category_id INTEGER NOT NULL REFERENCES categories(id),
                    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('income', 'expense')),
                    expense_kind TEXT CHECK (expense_kind IN ('fixed', 'variable')),
                    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                    transaction_date TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS monthly_budgets (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                    UNIQUE (user_id, category_id)
                );
                CREATE TABLE IF NOT EXISTS cash_flow_settings (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    monthly_income_cents INTEGER NOT NULL DEFAULT 0
                        CHECK (monthly_income_cents >= 0)
                );
                CREATE TABLE IF NOT EXISTS savings_goals (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 80),
                    target_cents INTEGER NOT NULL CHECK (target_cents > 0),
                    current_cents INTEGER NOT NULL DEFAULT 0 CHECK (current_cents >= 0),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS goal_contributions (
                    id INTEGER PRIMARY KEY,
                    goal_id INTEGER NOT NULL REFERENCES savings_goals(id) ON DELETE CASCADE,
                    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date
                    ON transactions(user_id, transaction_date);
                """
            )
            Database._migrate_categories(connection)
            Database._migrate_transactions(connection)
            connection.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_default_unique
                   ON categories(model_id, transaction_type, name)
                   WHERE owner_user_id IS NULL"""
            )
            connection.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_custom_unique
                   ON categories(owner_user_id, model_id, transaction_type, name)
                   WHERE owner_user_id IS NOT NULL"""
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

    @staticmethod
    def _migrate_categories(connection):
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(categories)")
        }
        if "owner_user_id" in columns:
            return

        connection.execute("PRAGMA foreign_keys = OFF")
        try:
            connection.execute("BEGIN")
            connection.execute(
                """CREATE TABLE categories_new (
                    id INTEGER PRIMARY KEY,
                    model_id INTEGER NOT NULL REFERENCES financial_models(id),
                    owner_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    transaction_type TEXT NOT NULL
                        CHECK (transaction_type IN ('income', 'expense')),
                    group_name TEXT NOT NULL,
                    name TEXT NOT NULL
                )"""
            )
            connection.execute(
                """INSERT INTO categories_new
                   (id, model_id, owner_user_id, transaction_type, group_name, name)
                   SELECT id, model_id, NULL, transaction_type, group_name, name
                   FROM categories"""
            )
            connection.execute("DROP TABLE categories")
            connection.execute("ALTER TABLE categories_new RENAME TO categories")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys = ON")

    @staticmethod
    def _migrate_transactions(connection):
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(transactions)")
        }
        if "expense_kind" not in columns:
            connection.execute(
                """ALTER TABLE transactions ADD COLUMN expense_kind TEXT
                   CHECK (expense_kind IN ('fixed', 'variable'))"""
            )


def get_db():
    if "db" not in g:
        g.db = Database.connect()
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()
