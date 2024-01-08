from flask import Blueprint
from flask import render_template, redirect, abort
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
    cnt += StateEntry.query.filter_by(date=today).join(State).filter(State.user_id=="uid").count()
    is_entry_empty = not cnt

    habits = User.query.filter_by(id=uid).first().habits
    states = User.query.filter_by(id=uid).first().states

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

        # save_states
        user_states = State.query.filter_by(user_id=uid).all()
        for state in user_states:
            if state.name in request.form.keys():
                state_value = request.form.get(state.name)
            else:
                state_value = None

            state_entry = StateEntry(
                state_id = state.id,
                date = today,
                value = state_value
            )
            
            db.session.add(state_entry)
        
        db.session.commit()



    return redirect("index")

@main.route('/day/<date>', methods = ['GET'])
@login_required
def day_data(date):
    uid = current_user.id

    try:
        parsed_date = datetime.datetime.strptime(date, r"%Y%m%d")
    except ValueError:
        abort(404)

    parsed_date = parsed_date.strftime(r'%Y-%m-%d')

    habits_entries = db.session.scalars(
        db.select(HabitEntry).filter_by(date=parsed_date)
        .join(Habit).filter_by(user_id=uid)
    ).all()

    journal_entry = db.session.scalar(
        db.select(JournalEntry)
        .filter_by(user_id=uid, date=parsed_date)
    )

    note = journal_entry.note if journal_entry else ""

    return render_template(
        "day.html",
        dates = parsed_date,
        note = note,
        habits = habits_entries,
        #states = state_entry
    )