"""
Routes principales pour ChattuBottu
"""
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def home():
    """Page d'accueil"""
    return render_template("index.html")
