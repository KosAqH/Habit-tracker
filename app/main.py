from flask import Blueprint
from flask import render_template, redirect
from flask import request

from flask_login import login_required
from flask_login import current_user

from .models import User, JournalEntry, HabitEntry, Habit, State, StateEntry
from . import db

import datetime

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
@login_required
def index():
    uid = current_user.id
    today = datetime.date.today()

    cnt = JournalEntry.query.filter_by(user_id=uid).filter_by(date=today).count()
    cnt += HabitEntry.query.filter_by(date=today).join(Habit).filter(Habit.user_id=="uid").count()
    is_entry_empty = not cnt

    habits = User.query.filter_by(id=uid).first().habits

    states = ["Mood"]

    return render_template(
        'index.html',
        habits = habits,
        states = states,
        is_entry_empty = is_entry_empty
    )

@main.route('/send_form', methods = ['POST'])
@login_required
def index_post():
    if request.form:
        uid = current_user.id
        today = datetime.date.today()#.strftime(r"%Y-%m-%d")

        # save_journal
        journal = JournalEntry(
            user_id = uid,
            date = today,
            note = request.form.get("journal_entry")
        )

        db.session.add(journal)
        db.session.commit()

        # save_habits
        user_habits = Habit.query.filter_by(user_id=uid).all()
        for habit in user_habits:
            if habit.name in request.form.keys():
                habit_value = True
            else:
                habit_value = False

            habit_entry = HabitEntry(
                habit_id = habit.id,
                date = today,
                value = habit_value
            )
            
            db.session.add(habit_entry)
        
        db.session.commit()


    return redirect("index")