from flask import render_template
from app.errors import bp


@bp.errorhandler(404)
def not_found_error(error):
    """Return 404 page on 404 error."""
    return render_template('errors/404.html', error=error), 404


@bp.errorhandler(500)
def handle_500(error):
    """Return 500 page on 500 error."""
    return render_template('errors/500.html', error=error), 500
