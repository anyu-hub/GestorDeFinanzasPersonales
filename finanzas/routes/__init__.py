from finanzas.routes.auth import auth_bp
from finanzas.routes.main import main_bp
from finanzas.routes.onboarding import onboarding_bp
from finanzas.routes.planning import planning_bp
from finanzas.routes.transactions import transactions_bp


def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(planning_bp)
