from functools import wraps

from flask import g, redirect, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def model_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        if g.user["model_id"] is None:
            return redirect(url_for("onboarding.onboarding"))
        return view(*args, **kwargs)

    return wrapped
