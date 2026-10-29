from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from finanzas.database import get_db
from finanzas.decorators import model_required
from finanzas.services import FinanceService


planning_bp = Blueprint("planning", __name__)
MAX_AMOUNT_CENTS = 999_999_999_999


@planning_bp.route("/cash-flow", methods=["POST"])
@model_required
def update_cash_flow():
    amount_cents = _amount_cents(request.form.get("monthly_income", ""), allow_zero=True)
    if amount_cents is None:
        flash("Ingresa un ingreso mensual esperado válido.", "error")
    else:
        with get_db():
            get_db().execute(
                """INSERT INTO cash_flow_settings (user_id, monthly_income_cents)
                   VALUES (?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                     monthly_income_cents = excluded.monthly_income_cents""",
                (g.user["id"], amount_cents),
            )
        flash("Ingreso recurrente mensual actualizado.", "success")
    return redirect(url_for("transactions.dashboard"))


@planning_bp.route("/budgets", methods=["GET", "POST"])
@model_required
def budgets():
    connection = get_db()
    if request.method == "POST":
        category_id = request.form.get("category_id", "")
        amount_cents = _amount_cents(request.form.get("amount", ""))
        category = next(
            (
                item for item in FinanceService.categories_for_user(
                    connection, g.user["id"], "expense"
                )
                if str(item["id"]) == category_id
            ),
            None,
        )
        if category is None:
            flash("Selecciona una categoría de gasto válida para tu método.", "error")
        elif amount_cents is None:
            flash("Ingresa un límite mensual mayor que cero y válido.", "error")
        else:
            with connection:
                connection.execute(
                    """INSERT INTO monthly_budgets (user_id, category_id, amount_cents)
                       VALUES (?, ?, ?)
                       ON CONFLICT(user_id, category_id) DO UPDATE SET
                         amount_cents = excluded.amount_cents""",
                    (g.user["id"], category["id"], amount_cents),
                )
            flash("Límite mensual guardado.", "success")
            return redirect(url_for("planning.budgets"))

    categories = FinanceService.categories_for_user(
        connection, g.user["id"], "expense"
    )
    budget_rows = connection.execute(
        """SELECT b.id, b.category_id, b.amount_cents, c.name, c.group_name
           FROM monthly_budgets b
           JOIN categories c ON c.id = b.category_id
           JOIN profiles p ON p.user_id = b.user_id
           WHERE b.user_id = ? AND p.model_id = c.model_id
             AND (c.owner_user_id IS NULL OR c.owner_user_id = b.user_id)
           ORDER BY c.group_name, c.name""",
        (g.user["id"],),
    ).fetchall()
    return render_template(
        "budgets.html",
        categories=categories,
        budget_rows=budget_rows,
    )


@planning_bp.route("/budgets/<int:budget_id>/delete", methods=["POST"])
@model_required
def delete_budget(budget_id):
    with get_db():
        cursor = get_db().execute(
            "DELETE FROM monthly_budgets WHERE id = ? AND user_id = ?",
            (budget_id, g.user["id"]),
        )
    if cursor.rowcount:
        flash("Límite mensual eliminado.", "success")
    else:
        flash("No se encontró ese límite mensual.", "error")
    return redirect(url_for("planning.budgets"))


@planning_bp.route("/goals", methods=["GET", "POST"])
@model_required
def goals():
    connection = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        target_cents = _amount_cents(request.form.get("target_amount", ""))
        if not name or len(name) > 80:
            flash("El nombre de la meta debe tener entre 1 y 80 caracteres.", "error")
        elif target_cents is None:
            flash("Ingresa un monto objetivo válido mayor que cero.", "error")
        else:
            with connection:
                connection.execute(
                    """INSERT INTO savings_goals (user_id, name, target_cents)
                       VALUES (?, ?, ?)""",
                    (g.user["id"], name, target_cents),
                )
            flash("Meta de ahorro creada.", "success")
            return redirect(url_for("planning.goals"))

    goals_list = connection.execute(
        """SELECT id, name, target_cents, current_cents
           FROM savings_goals WHERE user_id = ? ORDER BY created_at, id""",
        (g.user["id"],),
    ).fetchall()
    goal_rows = [
        {
            **dict(goal),
            "progress": min(
                100, round(goal["current_cents"] * 100 / goal["target_cents"])
            ),
            "remaining_cents": max(
                0, goal["target_cents"] - goal["current_cents"]
            ),
        }
        for goal in goals_list
    ]
    return render_template("goals.html", goals=goal_rows)


@planning_bp.route("/goals/<int:goal_id>/contributions", methods=["POST"])
@model_required
def contribute_to_goal(goal_id):
    amount_cents = _amount_cents(request.form.get("amount", ""))
    if amount_cents is None:
        flash("Ingresa un monto de aportación válido mayor que cero.", "error")
        return redirect(url_for("planning.goals"))

    connection = get_db()
    with connection:
        goal = connection.execute(
            """SELECT current_cents FROM savings_goals
               WHERE id = ? AND user_id = ?""",
            (goal_id, g.user["id"]),
        ).fetchone()
        if goal is None:
            flash("No se encontró esa meta de ahorro.", "error")
            return redirect(url_for("planning.goals"))
        if goal["current_cents"] > MAX_AMOUNT_CENTS - amount_cents:
            flash("La aportación supera el monto máximo permitido.", "error")
            return redirect(url_for("planning.goals"))
        connection.execute(
            """UPDATE savings_goals SET current_cents = current_cents + ?
               WHERE id = ? AND user_id = ?""",
            (amount_cents, goal_id, g.user["id"]),
        )
        connection.execute(
            "INSERT INTO goal_contributions (goal_id, amount_cents) VALUES (?, ?)",
            (goal_id, amount_cents),
        )
    flash("Aportación registrada en tu meta.", "success")
    return redirect(url_for("planning.goals"))


def _amount_cents(value, allow_zero=False):
    try:
        amount = Decimal(value.strip())
        if not amount.is_finite():
            return None
        cents = int((amount * 100).quantize(Decimal("1")))
    except (InvalidOperation, OverflowError, ValueError):
        return None
    if cents > MAX_AMOUNT_CENTS or cents < (0 if allow_zero else 1):
        return None
    return cents
