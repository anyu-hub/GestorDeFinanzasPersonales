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
