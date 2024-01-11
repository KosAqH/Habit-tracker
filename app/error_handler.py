from . import app

from flask import render_template
from flask_login import login_required

@app.errorhandler(404)
@login_required
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404