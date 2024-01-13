import datetime

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import request

from flask_login import login_required
from flask_login import current_user

from . import db
from .models import Habit, State

settings = Blueprint('settings', __name__)

@settings.route('/settings', methods = ['GET'])
@login_required
def settings_index():
    """
    Render settings page
    """
    return render_template(
        "settings.html",
        habits = current_user.habits,
        states = current_user.states
    )

@settings.route('/add_habit', methods = ['POST'])
@login_required
def add_habit():
    """
    View handle adding new Habit to database
    """
    uid = current_user.id
    formated_data = datetime.date.today()

    habit = Habit(
        user_id=uid,
        name=request.form.get("habit"),
        start_date = formated_data,
        is_active = True
    )
    db.session.add(habit)
    db.session.commit()

    return redirect(url_for("settings.settings_index"))

@settings.route('/add_state', methods = ['POST'])
@login_required
def add_state():
    """
    View handle adding new State to database
    """
    uid = current_user.id
    formated_data = datetime.date.today()

    state = State(
        user_id=uid,
        name=request.form.get("state"),
        start_date = formated_data,
        is_active = True
    )
    db.session.add(state)
    db.session.commit()

    return redirect(url_for("settings.settings_index"))

@settings.route('/delete_habit', methods = ['POST'])
@login_required
def delete_habit():
    """
    View handle removing Habit from database.
    All associated HabitEntries will be removed automatically.
    """
    uid = current_user.id
    habit_id = request.form.get("habit_id")

    habit = db.session.scalar(
        db.select(Habit)
        .filter_by(user_id=uid, id=habit_id)
    )
    db.session.delete(habit)
    db.session.commit()
    return redirect(url_for("settings.settings_index"))

@settings.route('/delete_state', methods = ['POST'])
@login_required
def delete_state():
    """
    View handle removing State from database.
    All associated StateEntries will be removed automatically.
    """
    uid = current_user.id
    state_id = request.form.get("state_id")

    state = db.session.scalar(
        db.select(State)
        .filter_by(user_id=uid, id=state_id)
    )
    db.session.delete(state)
    db.session.commit()
    return redirect(url_for("settings.settings_index"))