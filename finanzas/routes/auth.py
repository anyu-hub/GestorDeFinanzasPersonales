import sqlite3

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from finanzas.database import get_db
from finanzas.decorators import login_required
from finanzas.models import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user is not None:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not full_name or not email or len(password) < 8:
            flash(
                "Completa todos los campos. La contraseña debe tener al menos 8 caracteres.",
                "error",
            )
        else:
            try:
                with get_db():
                    cursor = get_db().execute(
                        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                        (email, User.hash_password(password)),
                    )
                    get_db().execute(
                        "INSERT INTO profiles (user_id, display_name) VALUES (?, ?)",
                        (cursor.lastrowid, full_name),
                    )
                session.clear()
                session["user_id"] = cursor.lastrowid
                return redirect(url_for("onboarding.onboarding"))
            except sqlite3.IntegrityError:
                flash("Ya existe una cuenta con ese correo electrónico.", "error")
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        if user and _verify_password(password, user["password_hash"]):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("main.index"))
        flash("Correo o contraseña incorrectos.", "error")
    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def _verify_password(password, stored_hash):
    try:
        return User.verify_password(password, stored_hash)
    except (ValueError, TypeError):
        return False
