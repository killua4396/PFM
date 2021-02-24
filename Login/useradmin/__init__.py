from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect
from flask_bootstrap import Bootstrap
from config import config
import flask_login
from flask import Blueprint, redirect, url_for, flash
from flask_login import  current_user, login_required
from functools import wraps

login_manager = flask_login.LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message = "请登录再进行操作！"


def login_required_with_level(levels):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated:
                if int(current_user.level) in levels:
                    return func(*args, **kwargs)
            flash("你无权访问该页面！")
            return redirect(url_for("user.index"))
        return login_required(wrapper)
    return decorator


db = SQLAlchemy()
bootstrap = Bootstrap()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    bootstrap.init_app(app)
    db.init_app(app)

    CsrfProtect(app)

    from .auth_blueprint import auth
    app.register_blueprint(auth)

    from .user_blueprint import user
    app.register_blueprint(user)

    login_manager.init_app(app)

    return app