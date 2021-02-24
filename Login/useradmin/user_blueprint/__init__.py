from flask import Blueprint
from . import views

user = Blueprint("useradmin", __name__, url_prefix="/useradmin")