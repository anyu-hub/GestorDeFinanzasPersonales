from decimal import Decimal

from flask import Flask, g, render_template, session

from finanzas.config import Config
from finanzas.database import Database, close_db, get_db
from finanzas.routes import register_routes


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    Database.initialize(app.config["DATABASE"])
    register_routes(app)
    app.teardown_appcontext(close_db)

    @app.before_request
    def load_user():
        g.user = None
        user_id = session.get("user_id")
        if user_id is not None:
            g.user = get_db().execute(
                """SELECT u.id, u.email, p.display_name, p.model_id
                   FROM users u JOIN profiles p ON p.user_id = u.id WHERE u.id = ?""",
                (user_id,),
            ).fetchone()

    @app.template_filter("money")
    def money(amount_cents):
        value = Decimal(amount_cents or 0) / Decimal(100)
        return f"${value:,.2f}"

    return app
