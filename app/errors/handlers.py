from flask import render_template
from app.errors import bp
from app.plugins.log_handler import LogHandler

@bp.errorhandler(401)
def handle_401(error):
    """Return 401 page on 401 error."""
    logger = LogHandler()
    logger.error(f'401 error: {error}')
    return render_template('errors/401.html', error=error), 401


@bp.errorhandler(403)
def handle_403(error):
    """Return 403 page on 403 error."""
    logger = LogHandler()
    logger.error(f'403 error: {error}')
    return render_template('errors/403.html', error=error), 403


@bp.errorhandler(404)
def handle_404(error):
    """Return 404 page on 404 error."""
    logger = LogHandler()
    logger.error(f'404 error: {error}')
    return render_template('errors/404.html', error=error), 404


@bp.errorhandler(500)
def handle_500(error):
    """Return 500 page on 500 error."""
    logger = LogHandler()
    logger.error(f'500 error: {error}')
    return render_template('errors/500.html', error=error), 500


@bp.errorhandler(502)
def handle_502(error):
    """Return 502 page on 502 error."""
    logger = LogHandler()
    logger.error(f'502 error: {error}')
    return render_template('errors/502.html', error=error), 502

