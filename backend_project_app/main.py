from flask import Blueprint

main_bp = Blueprint("main", __name__)

@main_bp.route("/health", methods=["GET"])
def health():
    return "OK"
