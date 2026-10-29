from calendar import monthrange

from flask import abort

from finanzas.models import CashFlowProjection


class FinanceService:
    @staticmethod
    def model_for_user(connection, user_id):
        return connection.execute(
            """SELECT fm.* FROM profiles p
               LEFT JOIN financial_models fm ON fm.id = p.model_id
               WHERE p.user_id = ?""",
            (user_id,),
        ).fetchone()

    @staticmethod
    def set_user_model(connection, user_id, model_code):
        model = connection.execute(
            "SELECT id FROM financial_models WHERE code = ?", (model_code,)
        ).fetchone()
        if model is None:
            abort(404)
        connection.execute(
            "UPDATE profiles SET model_id = ? WHERE user_id = ?", (model["id"], user_id)
        )

    @staticmethod
    def categories_for_user(connection, user_id, transaction_type=None):
        query = """SELECT c.id, c.name, c.group_name, c.transaction_type
                   FROM categories c
                   JOIN profiles p ON p.model_id = c.model_id
                   WHERE p.user_id = ?
                     AND (c.owner_user_id IS NULL OR c.owner_user_id = p.user_id)"""
        parameters = [user_id]
        if transaction_type:
            query += " AND c.transaction_type = ?"
            parameters.append(transaction_type)
        return connection.execute(query + " ORDER BY c.group_name, c.name", parameters).fetchall()

    @staticmethod
    def balance_for_user(connection, user_id):
        row = connection.execute(
            """SELECT COALESCE(SUM(CASE transaction_type
                                  WHEN 'income' THEN amount_cents
                                  ELSE -amount_cents END), 0) AS balance_cents
               FROM transactions WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
        return row["balance_cents"]

    @staticmethod
    def category_migration_plan(connection, user_id, target_model_code):
        target_model = connection.execute(
            "SELECT id, code, name FROM financial_models WHERE code = ?",
            (target_model_code,),
        ).fetchone()
        if target_model is None:
            abort(404)

        current_model = FinanceService.model_for_user(connection, user_id)
        if current_model is None or current_model["id"] == target_model["id"]:
            return target_model, {}, [], []

        source_categories = connection.execute(
            """SELECT DISTINCT c.id, c.name, c.group_name, c.transaction_type
               FROM categories c
               WHERE c.model_id = ?
                 AND (c.owner_user_id IS NULL OR c.owner_user_id = ?)
                 AND (
                   EXISTS (SELECT 1 FROM transactions t
                           WHERE t.user_id = ? AND t.category_id = c.id)
                   OR EXISTS (SELECT 1 FROM monthly_budgets b
                              WHERE b.user_id = ? AND b.category_id = c.id)
                 )
               ORDER BY c.transaction_type, c.name""",
            (current_model["id"], user_id, user_id, user_id),
        ).fetchall()
        target_categories = connection.execute(
            """SELECT id, name, group_name, transaction_type
               FROM categories
               WHERE model_id = ? AND (owner_user_id IS NULL OR owner_user_id = ?)
               ORDER BY group_name, name""",
            (target_model["id"], user_id),
        ).fetchall()

        automatic_mapping = {}
        manual_mapping = []
        for source in source_categories:
            compatible = [
                target for target in target_categories
                if target["transaction_type"] == source["transaction_type"]
            ]
            exact_match = next(
                (target for target in compatible if target["name"].casefold() == source["name"].casefold()),
                None,
            )
            if exact_match is not None:
                automatic_mapping[source["id"]] = exact_match["id"]
            else:
                manual_mapping.append({"source": source, "options": compatible})

        return target_model, automatic_mapping, manual_mapping, source_categories

    @staticmethod
    def migrate_user_method(connection, user_id, target_model_code, submitted_mapping=None):
        target_model, automatic_mapping, manual_mapping, source_categories = (
            FinanceService.category_migration_plan(connection, user_id, target_model_code)
        )
        mapping = dict(automatic_mapping)
        submitted_mapping = submitted_mapping or {}
        required_ids = {item["source"]["id"] for item in manual_mapping}
        if set(submitted_mapping) != required_ids:
            return False

        valid_options = {
            item["source"]["id"]: {option["id"] for option in item["options"]}
            for item in manual_mapping
        }
        for source_id, target_id in submitted_mapping.items():
            if target_id not in valid_options[source_id]:
                return False
            mapping[source_id] = target_id

        if len(mapping) != len(source_categories):
            return False

        with connection:
            for source_id, target_id in mapping.items():
                connection.execute(
                    "UPDATE transactions SET category_id = ? WHERE user_id = ? AND category_id = ?",
                    (target_id, user_id, source_id),
                )
                budget = connection.execute(
                    """SELECT amount_cents FROM monthly_budgets
                       WHERE user_id = ? AND category_id = ?""",
                    (user_id, source_id),
                ).fetchone()
                if budget is not None:
                    connection.execute(
                        """INSERT INTO monthly_budgets (user_id, category_id, amount_cents)
                           VALUES (?, ?, ?)
                           ON CONFLICT(user_id, category_id) DO UPDATE SET
                             amount_cents = monthly_budgets.amount_cents + excluded.amount_cents""",
                        (user_id, target_id, budget["amount_cents"]),
                    )
                    connection.execute(
                        "DELETE FROM monthly_budgets WHERE user_id = ? AND category_id = ?",
                        (user_id, source_id),
                    )
            connection.execute(
                "UPDATE profiles SET model_id = ? WHERE user_id = ?",
                (target_model["id"], user_id),
            )
        return True


class PlanningService:
    @staticmethod
    def cash_flow_for_user(connection, user_id, income_cents, expenses_cents, today):
        settings = connection.execute(
            "SELECT monthly_income_cents FROM cash_flow_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        expected_income = settings["monthly_income_cents"] if settings else 0
        days_in_month = monthrange(today.year, today.month)[1]
        return {
            **CashFlowProjection.estimate(
                income_cents,
                expenses_cents,
                expected_income,
                today.day,
                days_in_month,
            ),
            "expected_income_cents": expected_income,
        }
