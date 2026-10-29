import hashlib
import hmac
import secrets


class User:
    @staticmethod
    def hash_password(password):
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
        return f"{salt.hex()}${digest.hex()}"

    @staticmethod
    def verify_password(password, stored_hash):
        salt_hex, digest_hex = stored_hash.split("$", 1)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 310_000
        )
        return hmac.compare_digest(digest.hex(), digest_hex)


class QuestionnaireRecommender:
    @staticmethod
    def recommend(budgeting_style, income_stability, savings_priority):
        scores = {"503020": 0, "zero_based": 0, "envelopes": 0, "pay_yourself": 0}
        if budgeting_style == "detailed":
            scores["zero_based"] += 2
        elif budgeting_style == "flexible":
            scores["envelopes"] += 2
        else:
            scores["503020"] += 2

        if income_stability == "stable":
            scores["503020"] += 1
            scores["zero_based"] += 1
        else:
            scores["zero_based"] += 1
            scores["envelopes"] += 1

        if savings_priority == "high":
            scores["pay_yourself"] += 2
        elif savings_priority == "balanced":
            scores["503020"] += 1
        else:
            scores["zero_based"] += 1
            scores["envelopes"] += 1

        highest_score = max(scores.values())
        return next(code for code in scores if scores[code] == highest_score)


class CashFlowProjection:
    @staticmethod
    def estimate(
        actual_income_cents,
        actual_expenses_cents,
        expected_monthly_income_cents,
        day_of_month,
        days_in_month,
    ):
        projected_income = max(actual_income_cents, expected_monthly_income_cents)
        projected_expenses = round(
            actual_expenses_cents * days_in_month / max(day_of_month, 1)
        )
        projected_balance = projected_income - projected_expenses
        savings_rate = (
            projected_balance / projected_income * 100 if projected_income else None
        )
        return {
            "income_cents": projected_income,
            "expenses_cents": projected_expenses,
            "balance_cents": projected_balance,
            "savings_rate": savings_rate,
        }
