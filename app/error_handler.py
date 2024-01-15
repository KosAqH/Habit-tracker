from . import app

from flask import render_template
from flask_login import login_required

@app.errorhandler(404)
@login_required
def page_not_found(e):
    """
    Render custom 404 error page
    """
    return render_template('404.html'), 404