from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from finanzas.catalog import FINANCIAL_MODELS, MODEL_EXPLANATIONS, QUESTION_OPTIONS
from finanzas.database import get_db
from finanzas.decorators import login_required
from finanzas.models import QuestionnaireRecommender
from finanzas.services import FinanceService


onboarding_bp = Blueprint("onboarding", __name__)


@onboarding_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    if g.user["model_id"] is not None:
        return redirect(url_for("transactions.dashboard"))
    if request.method == "POST":
        style = request.form.get("budgeting_style", "")
        stability = request.form.get("income_stability", "")
        savings = request.form.get("savings_priority", "")
        if (
            style not in QUESTION_OPTIONS["budgeting_style"]
            or stability not in QUESTION_OPTIONS["income_stability"]
            or savings not in QUESTION_OPTIONS["savings_priority"]
        ):
            flash("Selecciona una respuesta válida en cada pregunta.", "error")
        else:
            recommendation = QuestionnaireRecommender.recommend(style, stability, savings)
            model_row = get_db().execute(
                "SELECT id FROM financial_models WHERE code = ?", (recommendation,)
            ).fetchone()
            with get_db():
                get_db().execute(
                    """INSERT INTO questionnaires
                       (user_id, budgeting_style, income_stability, savings_priority,
                        recommended_model_id)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(user_id) DO UPDATE SET
                         budgeting_style = excluded.budgeting_style,
                         income_stability = excluded.income_stability,
                         savings_priority = excluded.savings_priority,
                         recommended_model_id = excluded.recommended_model_id,
                         completed_at = CURRENT_TIMESTAMP""",
                    (g.user["id"], style, stability, savings, model_row["id"]),
                )
            return redirect(url_for("onboarding.recommendation"))
    return render_template("onboarding.html", options=QUESTION_OPTIONS)


@onboarding_bp.route("/recommendation", methods=["GET", "POST"])
@login_required
def recommendation():
    questionnaire = get_db().execute(
        """SELECT fm.code, fm.name, fm.description
           FROM questionnaires q
           JOIN financial_models fm ON fm.id = q.recommended_model_id
           WHERE q.user_id = ?""",
        (g.user["id"],),
    ).fetchone()
    if questionnaire is None:
        return redirect(url_for("onboarding.onboarding"))
    if request.method == "POST":
        choice = request.form.get("choice")
        if choice == "accept":
            with get_db():
                FinanceService.set_user_model(get_db(), g.user["id"], questionnaire["code"])
            return redirect(url_for("transactions.dashboard"))
        if choice == "choose":
            return redirect(url_for("onboarding.choose_model"))
        abort(400)
    return render_template("recommendation.html", recommendation=questionnaire)


@onboarding_bp.route("/models", methods=["GET", "POST"])
@login_required
def choose_model():
    if request.method == "POST":
        model_code = request.form.get("model_code", "")
        if not any(model["code"] == model_code for model in FINANCIAL_MODELS):
            flash("Selecciona un método disponible.", "error")
        elif g.user["model_id"] is not None and get_db().execute(
            "SELECT 1 FROM transactions WHERE user_id = ? LIMIT 1",
            (g.user["id"],),
        ).fetchone():
            flash(
                "No puedes cambiar de método mientras tengas movimientos registrados.",
                "error",
            )
        else:
            with get_db():
                FinanceService.set_user_model(get_db(), g.user["id"], model_code)
            return redirect(url_for("transactions.dashboard"))
    return render_template(
        "models.html",
        models=FINANCIAL_MODELS,
        explanations=MODEL_EXPLANATIONS,
        current_model=FinanceService.model_for_user(get_db(), g.user["id"]),
    )
