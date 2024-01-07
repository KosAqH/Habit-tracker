from flask import Blueprint, render_template
from flask_login import login_required

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
@login_required
def index():
    habits = ["Wake up", "Eat breakfest"]
    states = ["Mood"]

    return render_template(
        'index.html',
        habits = habits,
        states = states,
        is_entry_empty = True)