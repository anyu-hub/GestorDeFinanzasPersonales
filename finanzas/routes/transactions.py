import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from finanzas.database import get_db
from finanzas.decorators import model_required
from finanzas.services import FinanceService, PlanningService


transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/dashboard")
@model_required
def dashboard():
    today = date.today()
    month_start = today.replace(day=1)
    previous_month_end = month_start.fromordinal(month_start.toordinal() - 1)
    previous_month_start = previous_month_end.replace(day=1)
    row = get_db().execute(
        """SELECT
             COALESCE(SUM(CASE WHEN transaction_type = 'income'
                               AND transaction_date >= ? AND transaction_date <= ?
                               THEN amount_cents ELSE 0 END), 0) AS income,
             COALESCE(SUM(CASE WHEN transaction_type = 'expense'
                               AND transaction_date >= ? AND transaction_date <= ?
                               THEN amount_cents ELSE 0 END), 0) AS expenses,
             COALESCE(SUM(CASE WHEN transaction_type = 'expense'
                               AND transaction_date >= ? AND transaction_date <= ?
                               THEN amount_cents ELSE 0 END), 0) AS previous_expenses
           FROM transactions WHERE user_id = ?""",
        (
            month_start.isoformat(), today.isoformat(),
            month_start.isoformat(), today.isoformat(),
            previous_month_start.isoformat(), previous_month_end.isoformat(),
            g.user["id"],
        ),
    ).fetchone()
    expense_rows = get_db().execute(
        """SELECT c.name, SUM(t.amount_cents) AS amount
           FROM transactions t JOIN categories c ON c.id = t.category_id
           WHERE t.user_id = ? AND t.transaction_type = 'expense'
             AND t.transaction_date >= ? AND t.transaction_date <= ?
           GROUP BY c.id, c.name ORDER BY amount DESC, c.name""",
        (g.user["id"], month_start.isoformat(), today.isoformat()),
    ).fetchall()
    largest = max((item["amount"] for item in expense_rows), default=0)
    chart_rows = [
        {
            "name": item["name"],
            "amount": item["amount"],
            "width": max(2, round(item["amount"] * 100 / largest)),
        }
        for item in expense_rows
    ]
    budget_rows = get_db().execute(
        """SELECT b.id, b.amount_cents, c.name, c.group_name,
                  COALESCE(SUM(t.amount_cents), 0) AS spent_cents
           FROM monthly_budgets b
           JOIN categories c ON c.id = b.category_id
           JOIN profiles p ON p.user_id = b.user_id
           LEFT JOIN transactions t
             ON t.user_id = b.user_id
            AND t.category_id = b.category_id
            AND t.transaction_type = 'expense'
            AND t.transaction_date >= ? AND t.transaction_date <= ?
           WHERE b.user_id = ? AND p.model_id = c.model_id
             AND (c.owner_user_id IS NULL OR c.owner_user_id = b.user_id)
           GROUP BY b.id, b.amount_cents, c.name, c.group_name
           ORDER BY c.group_name, c.name""",
        (month_start.isoformat(), today.isoformat(), g.user["id"]),
    ).fetchall()
    budget_indicators = [
        {
            **dict(item),
            "percent": round(item["spent_cents"] * 100 / item["amount_cents"]),
            "bar_percent": min(
                100, round(item["spent_cents"] * 100 / item["amount_cents"])
            ),
            "status": (
                "over"
                if item["spent_cents"] >= item["amount_cents"]
                else "near"
                if item["spent_cents"] * 100 >= item["amount_cents"] * 80
                else "within"
            ),
        }
        for item in budget_rows
    ]
    expense_types = get_db().execute(
        """SELECT COALESCE(expense_kind, 'variable') AS expense_kind,
                  COALESCE(SUM(amount_cents), 0) AS amount_cents
           FROM transactions
           WHERE user_id = ? AND transaction_type = 'expense'
             AND transaction_date >= ? AND transaction_date <= ?
           GROUP BY COALESCE(expense_kind, 'variable')""",
        (g.user["id"], month_start.isoformat(), today.isoformat()),
    ).fetchall()
    fixed_variable = {"fixed": 0, "variable": 0}
    for item in expense_types:
        fixed_variable[item["expense_kind"]] = item["amount_cents"]
    total_classified_expenses = sum(fixed_variable.values())
    fixed_variable_percent = {
        kind: (
            round(amount * 100 / total_classified_expenses)
            if total_classified_expenses
            else 0
        )
        for kind, amount in fixed_variable.items()
    }
    cash_flow = PlanningService.cash_flow_for_user(
        get_db(), g.user["id"], row["income"], row["expenses"], today
    )
    spanish_months = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    )
    return render_template(
        "dashboard.html",
        model=FinanceService.model_for_user(get_db(), g.user["id"]),
        income=row["income"],
        expenses=row["expenses"],
        balance=row["income"] - row["expenses"],
        previous_expenses=row["previous_expenses"],
        month_name=f"{spanish_months[today.month - 1].capitalize()} {today.year}",
        chart_rows=chart_rows,
        budget_indicators=budget_indicators,
        cash_flow=cash_flow,
        fixed_variable=fixed_variable,
        fixed_variable_percent=fixed_variable_percent,
    )


@transactions_bp.route("/transactions/new", methods=["GET", "POST"])
@model_required
def new_transaction():
    categories = FinanceService.categories_for_user(get_db(), g.user["id"])
    model = FinanceService.model_for_user(get_db(), g.user["id"])
    if request.method == "POST":
        response = _save_transaction(categories)
        if response is not None:
            return response
    return render_template(
        "transaction_form.html",
        categories=categories,
        model=model,
        available_balance_cents=FinanceService.balance_for_user(get_db(), g.user["id"]),
        today=date.today().isoformat(),
    )


@transactions_bp.route("/categories/new", methods=["POST"])
@model_required
def create_category():
    transaction_type = request.form.get("transaction_type", "")
    name = request.form.get("name", "").strip()
    if transaction_type not in ("income", "expense") or not name or len(name) > 60:
        flash("Ingresa un nombre de hasta 60 caracteres y un tipo válido.", "error")
        return redirect(url_for("transactions.new_transaction"))

    model = FinanceService.model_for_user(get_db(), g.user["id"])
    try:
        with get_db():
            get_db().execute(
                """INSERT INTO categories
                   (model_id, owner_user_id, transaction_type, group_name, name)
                   VALUES (?, ?, ?, 'Personalizadas', ?)""",
                (model["id"], g.user["id"], transaction_type, name),
            )
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed" not in str(error):
            raise
        flash("Ya tienes una categoría personalizada con ese nombre y tipo.", "error")
    else:
        flash("Categoría personalizada creada.", "success")
    return redirect(url_for("transactions.new_transaction"))


def _save_transaction(categories):
    transaction_type = request.form.get("transaction_type", "")
    category_id = request.form.get("category_id", "")
    raw_amount = request.form.get("amount", "").strip()
    transaction_date = request.form.get("transaction_date", "")
    description = request.form.get("description", "").strip()
    expense_kind = request.form.get("expense_kind", "")
    category = next(
        (
            item
            for item in categories
            if str(item["id"]) == category_id
            and item["transaction_type"] == transaction_type
        ),
        None,
    )
    try:
        amount_cents = int((Decimal(raw_amount) * 100).quantize(Decimal("1")))
        valid_date = date.fromisoformat(transaction_date)
    except (InvalidOperation, OverflowError, ValueError):
        amount_cents = 0
        valid_date = None

    if transaction_type not in ("income", "expense") or category is None:
        flash("Selecciona un tipo y una categoría válidos para tu método.", "error")
    elif transaction_type == "expense" and expense_kind not in ("fixed", "variable"):
        flash("Clasifica el gasto como fijo o variable.", "error")
    elif amount_cents <= 0 or amount_cents > 999_999_999_999 or valid_date is None:
        flash(
            "Ingresa un monto entre 0.01 y 9,999,999,999.99 USD y una fecha válida.",
            "error",
        )
    elif valid_date > date.today():
        flash("La fecha no puede estar en el futuro.", "error")
    else:
        connection = get_db()
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            available_balance = FinanceService.balance_for_user(connection, g.user["id"])
            if transaction_type == "expense" and amount_cents > available_balance:
                connection.rollback()
                missing_cents = amount_cents - available_balance
                flash(
                    "Saldo insuficiente. Disponible: "
                    f"${Decimal(available_balance) / Decimal(100):,.2f}. Registra primero un ingreso de "
                    f"al menos ${Decimal(missing_cents) / Decimal(100):,.2f} para mantener el balance en cero o más.",
                    "error",
                )
                return None
            connection.execute(
                """INSERT INTO transactions
                   (user_id, category_id, transaction_type, expense_kind, amount_cents,
                    transaction_date, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    g.user["id"], category["id"], transaction_type,
                    expense_kind if transaction_type == "expense" else None,
                    amount_cents, valid_date.isoformat(), description,
                ),
            )
        flash("Movimiento registrado.", "success")
        return redirect(url_for("transactions.history"))
    return None


@transactions_bp.route("/history")
@model_required
def history():
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    category_id = request.args.get("category_id", "").strip()
    conditions = ["t.user_id = ?"]
    parameters = [g.user["id"]]
    start_date = _add_date_filter(start_date, "t.transaction_date >= ?", conditions, parameters, "inicial")
    end_date = _add_date_filter(end_date, "t.transaction_date <= ?", conditions, parameters, "final")
    categories = FinanceService.categories_for_user(get_db(), g.user["id"])
    if category_id:
        if any(str(category["id"]) == category_id for category in categories):
            conditions.append("t.category_id = ?")
            parameters.append(category_id)
        else:
            flash("La categoría no pertenece a tu método; se ignoró ese filtro.", "error")
            category_id = ""
    transactions = get_db().execute(
        f"""SELECT t.id, t.transaction_type, t.expense_kind, t.amount_cents,
                   t.transaction_date, t.description, c.name AS category_name
            FROM transactions t JOIN categories c ON c.id = t.category_id
            WHERE {' AND '.join(conditions)}
            ORDER BY t.transaction_date DESC, t.id DESC""",
        parameters,
    ).fetchall()
    return render_template(
        "history.html",
        transactions=transactions,
        categories=categories,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
    )


def _add_date_filter(value, sql_condition, conditions, parameters, label):
    if not value:
        return value
    try:
        normalized_date = date.fromisoformat(value).isoformat()
    except ValueError:
        flash(f"La fecha {label} no es válida; se ignoró ese filtro.", "error")
        return ""
    conditions.append(sql_condition)
    parameters.append(normalized_date)
    return normalized_date
