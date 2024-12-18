from flask import Blueprint

main = Blueprint('customer', __name__)


from . import views, errors
