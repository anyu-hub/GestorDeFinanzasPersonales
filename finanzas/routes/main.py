from flask import Blueprint, g, redirect, url_for


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if g.user is None:
        return redirect(url_for("auth.login"))
    if g.user["model_id"] is None:
        return redirect(url_for("onboarding.onboarding"))
    return redirect(url_for("transactions.dashboard"))
