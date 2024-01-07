from flask import Blueprint, render_template, redirect, request
from flask_login import login_required, current_user
from .models import User, JournalEntry, HabitEntry, Habit
from . import db

import datetime

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
@login_required
def index():
    uid = current_user.id
    habits = User.query.filter_by(id=uid).first().habits

    states = ["Mood"]

    return render_template(
        'index.html',
        habits = habits,
        states = states,
        is_entry_empty = True
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
        habits = [item for item in request.form.items() if item[0].startswith("habit")]
        print()
        for habit in habits:
            print(habit[0])
            habit_id = Habit.query.filter_by(user_id = uid).filter_by(name = habit[0][6:]).first().id
            print(habit_id)
            habit_entry = HabitEntry(
                habit_id = habit_id,
                date = today,
                value = True
            )
            db.session.add(habit_entry)
        db.session.commit()


    return redirect("index")