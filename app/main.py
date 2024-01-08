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

    today_raw = today.strftime(r"%Y%m%d")

    return render_template(
        'index.html',
        today_date = today_raw,
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
def day_date(date):
    uid = current_user.id

    try:
        parsed_date = datetime.datetime.strptime(date, r"%Y%m%d")
    except ValueError:
        abort(404)

    last_date = (parsed_date - datetime.timedelta(days=1)).strftime(r'%Y-%m-%d')
    next_date = (parsed_date + datetime.timedelta(days=1)).strftime(r'%Y-%m-%d')

    parsed_date = parsed_date.strftime(r'%Y-%m-%d')

    habits_entries = db.session.scalars(
        db.select(HabitEntry).filter_by(date=parsed_date)
        .join(Habit).filter_by(user_id=uid)
    ).all()

    state_entries = db.session.scalars(
        db.select(StateEntry).filter_by(date=parsed_date)
        .join(State).filter_by(user_id=uid)
    ).all()

    journal_entry = db.session.scalar(
        db.select(JournalEntry)
        .filter_by(user_id=uid, date=parsed_date)
    )

    note = journal_entry.note if journal_entry else ""

    return render_template(
        "day.html",
        current_date = parsed_date,
        current_date_link = parsed_date.replace("-", ""),
        last_date = last_date,
        last_date_link = last_date.replace("-", ""),
        next_date = next_date,
        next_date_link = next_date.replace("-", ""),
        note = note,
        habits = habits_entries,
        states = state_entries
    )

@main.route('/edit/<date>', methods = ['GET'])
@login_required
def edit(date):
    try:
        parsed_date = datetime.datetime.strptime(date, r"%Y%m%d")
    except ValueError:
        abort(404)

    uid = current_user.id
    date = parsed_date
    parsed_date = parsed_date.strftime(r'%Y-%m-%d')

    habits = User.query.filter_by(id=uid).first().habits
    states = User.query.filter_by(id=uid).first().states

    for habit in habits:
        if not habit.habit_entries:
            entry = HabitEntry(
                habit_id=habit.id,
                date=date,
                value=False
            )
            db.session.add(entry)
    db.session.commit()
        
    for state in states:
        if not state.state_entries:
            entry = StateEntry(
                state_id=state.id,
                date=date,
                value=False
            )
            db.session.add(entry)
    db.session.commit()

    habits_entries = db.session.scalars(
        db.select(HabitEntry).filter_by(date=parsed_date)
        .join(Habit).filter_by(user_id=uid)
    ).all()

    state_entries = db.session.scalars(
        db.select(StateEntry).filter_by(date=parsed_date)
        .join(State).filter_by(user_id=uid)
    ).all()

    journal_entry = db.session.scalar(
        db.select(JournalEntry)
        .filter_by(user_id=uid, date=parsed_date)
    )
    note = journal_entry.note if journal_entry else ""

    return render_template(
        "edit.html",
        habits = habits_entries,
        states = state_entries,
        journal_text = note
    )

@main.route('/update_day', methods = ['POST'])
@login_required
def edit_post():
    uid = current_user.id
    date = request.referrer.split("/")[-1]
    formated_data = datetime.datetime.strptime(date, r"%Y%m%d").strftime(r"%Y-%m-%d")

    user_habits = Habit.query.filter_by(user_id=uid).all()
    for habit in user_habits:
        if habit.name in request.form.keys():
            habit_value = True
        else:
            habit_value = False

        habit_entry = db.session.scalar(
            db.select(HabitEntry)
            .filter_by(habit_id=habit.id, date=formated_data)
        )
        habit_entry.value = habit_value

    user_states = State.query.filter_by(user_id=uid).all()
    for state in user_states:
        if state.name in request.form.keys():
            state_value = request.form.get(state.name)
        else:
            state_value = None

        state_entry = db.session.scalar(
            db.select(StateEntry)
            .filter_by(state_id=state.id, date=formated_data)
        )
        state_entry.value = state_value

    journal_entry = db.session.scalar(
        db.select(JournalEntry)
        .filter_by(user_id=uid, date=formated_data)
    )
    journal_entry.note = request.form.get("journal_entry")
    
    db.session.commit()
    return redirect(f"day/{date}")

@main.route('/settings', methods = ['GET'])
@login_required
def settings():
    uid = current_user.id
    return render_template(
        "settings.html",
        habits = User.query.filter_by(id=uid).first().habits,
        states = User.query.filter_by(id=uid).first().states
    )

@main.route('/add_habit', methods = ['POST'])
@login_required
def add_habit():
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

    return redirect("settings")

@main.route('/add_state', methods = ['POST'])
@login_required
def add_state():
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

    return redirect("settings")