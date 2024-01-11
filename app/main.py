from flask import Blueprint
from flask import render_template, redirect, abort, url_for
from flask import request

from flask_login import login_required
from flask_login import current_user

from sqlalchemy.sql import func

from .models import User, JournalEntry, HabitEntry, Habit, State, StateEntry
from . import db, app

import datetime
import calendar

# plot
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import ListedColormap

import july
from july.utils import date_range

import io
import base64

##

main = Blueprint('main', __name__)

def prepare_habit_stats(habits, today, cnt):
    today_entry_exists = 1 if cnt else 0
    
    for habit in habits:
        days_of_tracking = (today - habit.start_date).days + today_entry_exists
        days_with_habit_done = sum(entry.value for entry in habit.habit_entries)
        
        ratio = days_with_habit_done/(days_of_tracking) if days_of_tracking else 0
        percentage = ratio * 100

        i = 0
        for entry in habit.habit_entries[::-1]:
            if entry.value == False:
                break
            i += 1
        streak = i

        habit.n_days = days_of_tracking
        habit.percentage = int(percentage)
        habit.streak = streak

def prepare_states_stats(states, today, cnt):
    today_entry_exists = 1 if cnt else 0
    
    for state in states:
        days_of_tracking = (today - state.start_date).days + today_entry_exists

        if state.state_entries:
            avg_value = sum((entry.value for entry in state.state_entries))/len(state.state_entries)
        else:
            avg_value = 0

        state.n_days = days_of_tracking
        state.avg_value = avg_value

def plot_habits(start_date, end_date, habits):
    dates = date_range(start_date, end_date)

    for habit in habits:
        habit.plot = plot_habit(dates, habit)

def plot_habit(dates, habit):
    data = [-1]*366

    for entry in habit.habit_entries:
        i = dates.index(entry.date)
        data[i] = entry.value

    mpl.use('agg') # to init

    cmap_habit = ListedColormap(["grey", "red", "green"]) # to init

    july.heatmap(dates, data, cmap=cmap_habit, cmin=-1, cmax=1)

    s = io.BytesIO()
    plt.savefig(s, format='png', transparent=True, bbox_inches="tight")
    plt.close()
    s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    return f'data:image/png;base64,{s}'

def plot_states(start_date, end_date, states):
    dates = date_range(start_date, end_date)

    for state in states:
        state.plot = plot_state(dates, state)

def plot_state(dates, state):
    data = [-1]*366

    for entry in state.state_entries:
        i = dates.index(entry.date)
        data[i] = entry.value

    mpl.use('agg') # to init

    cmap_state = ListedColormap(["grey", "grey", "darkred", "red", "orange", "yellowgreen", "darkgreen"]) # to init

    july.heatmap(dates, data, cmap=cmap_state, cmin=-1, cmax=5)

    s = io.BytesIO()
    plt.savefig(s, format='png', transparent=True, bbox_inches="tight")
    plt.close()
    s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    return f'data:image/png;base64,{s}'

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

    prepare_habit_stats(habits, today, cnt)
    prepare_states_stats(states, today, cnt)

    plot_habits(today - datetime.timedelta(days=365), today, habits)
    plot_states(today - datetime.timedelta(days=365), today, states)

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

@main.route('/future', methods = ['GET'])
@login_required
def future():
    return render_template("future.html")

@main.route('/past', methods = ['GET'])
@login_required
def past():
    return render_template("past.html")

@main.route('/day/<date>', methods = ['GET'])
@login_required
def day_date(date):
    uid = current_user.id

    try:
        parsed_date = datetime.datetime.strptime(date, r"%Y%m%d")
    except ValueError:
        abort(404)
    
    if parsed_date.date() > datetime.date.today():
        return redirect(url_for("main.future"))

    min_date = db.session.scalar(
        func.min(
            db.select(Habit.start_date).filter_by(user_id=uid)
        )   
    )
    
    is_last_day = False
    is_first_day = False
    if parsed_date.date() == datetime.date.today():
        is_last_day = True
    if parsed_date.date() <= min_date:
        is_first_day = True

    min_date = str(min_date).replace("-", "")
    if parsed_date.date() < datetime.datetime.strptime(min_date, r"%Y%m%d").date():
        return redirect(url_for("main.past"))

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
        states = state_entries,
        is_last_day = is_last_day,
        is_first_day = is_first_day
    )

@main.route('/day/', methods = ['GET'])
@login_required
def day_date_not_given():
    current_day = datetime.date.today().strftime(r"%Y%m%d")
    return redirect(f"/day/{current_day}")

def is_entry_empty(uid, date):
    cnt = JournalEntry.query.filter_by(user_id=uid).filter_by(date=date).count()
    cnt += HabitEntry.query.filter_by(date=date).join(Habit).filter(Habit.user_id=="uid").count()
    cnt += StateEntry.query.filter_by(date=date).join(State).filter(State.user_id=="uid").count()
    is_entry_empty = not cnt

    return is_entry_empty

@main.route('/new/<date>', methods = ['GET'])
@login_required
def new_entry(date):
    uid = current_user.id
    date = datetime.datetime.strptime(date, r"%Y%m%d").date()
    habits = db.session.scalars(
        db.select(Habit).filter_by(user_id=uid).filter(Habit.start_date<=date)
    )
    states = db.session.scalars(
        db.select(State).filter_by(user_id=uid).filter(State.start_date<=date)
    )
    return render_template(
        "new.html",
        habits = habits,
        states = states
    )

@main.route('/add_day', methods = ['POST'])
@login_required
def new_entry_post():
    if request.form:
        uid = current_user.id

        uid = current_user.id
        date = request.referrer.split("/")[-1]
        formated_data = datetime.datetime.strptime(date, r"%Y%m%d")

        print(uid)
        print(formated_data)
        print(request.form.get("journal_entry"))
        # save_journal
        journal = JournalEntry(
            user_id = uid,
            date = formated_data,
            note = request.form.get("journal_entry")
        )

        db.session.add(journal)
        db.session.commit()

        # save_habits
        user_habits = Habit.query.filter_by(user_id=uid).filter(Habit.start_date <= formated_data).all()
        for habit in user_habits:
            if habit.name in request.form.keys():
                habit_value = True
            else:
                habit_value = False

            habit_entry = HabitEntry(
                habit_id = habit.id,
                date = formated_data,
                value = habit_value
            )
            
            db.session.add(habit_entry)
        
        db.session.commit()

        # save_states
        user_states = State.query.filter_by(user_id=uid).filter(State.start_date <= formated_data).all()
        for state in user_states:
            if state.name in request.form.keys():
                state_value = request.form.get(state.name)
            else:
                state_value = None

            state_entry = StateEntry(
                state_id = state.id,
                date = formated_data,
                value = state_value
            )
            
            db.session.add(state_entry)
        
        db.session.commit()
    
    return redirect(f"day/{date}")

@main.route('/edit/<date>', methods = ['GET'])
@login_required
def edit(date):
    try:
        parsed_date = datetime.datetime.strptime(date, r"%Y%m%d")
    except ValueError:
        abort(404)

    if parsed_date.date() > datetime.date.today():
        return redirect(url_for("main.future"))
    
    uid = current_user.id

    min_date = db.session.scalar(
        func.min(
            db.select(Habit.start_date).filter_by(user_id=uid)
        )   
    )
    min_date = str(min_date).replace("-", "")
    if parsed_date.date() < datetime.datetime.strptime(min_date, r"%Y%m%d").date():
        return redirect(url_for("main.past"))
    
    if is_entry_empty(uid, parsed_date.date()):
        print("redirect")
        return redirect(url_for("main.new_entry", date=date))
    
    date = parsed_date
    parsed_date = parsed_date.strftime(r'%Y-%m-%d')

    habits = User.query.filter_by(id=uid).first().habits
    states = User.query.filter_by(id=uid).first().states

    for habit in habits:
        if not habit.habit_entries and date.date() <= habit.start_date:
            entry = HabitEntry(
                habit_id=habit.id,
                date=date,
                value=False
            )
            db.session.add(entry)
    db.session.commit()
        
    for state in states:
        if not state.state_entries and date.date() <= state.start_date:
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

    user_habits = Habit.query.filter_by(user_id=uid).filter(Habit.start_date <= formated_data).all()

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

    user_states = State.query.filter_by(user_id=uid).filter(State.start_date <= formated_data).all()
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

@main.route('/delete_habit', methods = ['POST'])
@login_required
def delete_habit():
    uid = current_user.id
    habit_id = request.form.get("habit_id")

    habit = db.session.scalar(
        db.select(Habit)
        .filter_by(user_id=uid, id=habit_id)
    )
    db.session.delete(habit)
    db.session.commit()
    return redirect("settings")

@main.route('/delete_state', methods = ['POST'])
@login_required
def delete_state():
    uid = current_user.id
    state_id = request.form.get("state_id")

    state = db.session.scalar(
        db.select(State)
        .filter_by(user_id=uid, id=state_id)
    )
    db.session.delete(state)
    db.session.commit()
    return redirect("settings")

@main.route('/calendar/', methods = ['GET'])
@login_required
def calendar_date_not_given():
    current_month = datetime.date.today().strftime(r"%Y%m")
    return redirect(f"/calendar/{current_month}")

@main.route('/calendar/<mdate>', methods = ['GET'])
@login_required
def calendar_view(mdate):
    year = mdate[:4]
    month = mdate[4:]
    uid = current_user.id

    try:
        cal = calendar.monthcalendar(int(year), int(month))
    except:
        abort(404)

    if int(month) == 1:
        last_m = "12"
        next_m = "02"
        last_y = f"{int(year)-1}".zfill(4)
        next_y = year

    elif int(month) == 12:
        last_m = "11"
        next_m = "01"
        last_y = year
        next_y = f"{int(year)+1}".zfill(4)
        
    else:
        last_m = f"{int(month)-1}".zfill(2)
        next_m = f"{int(month)+1}".zfill(2)
        last_y = year
        next_y = year

    last_month = f"{last_y}{last_m}"
    next_month = f"{next_y}{next_m}"

    today = datetime.date.today().strftime(r"%Y%m%d")

    min_date = db.session.scalar(
        func.min(
            db.select(Habit.start_date).filter_by(user_id=uid)
        )   
    )
    first_date = str(min_date).replace("-", "")

    month_name = calendar.month_name[(int(month))]

    generated_calendar = []
    for week in cal:
        generated_week = []
        for day in week:
            if day == 0:
                d = {}
            else:
                date = f"{mdate}{str(day).zfill(2)}"
                d = {
                    "link": url_for("main.day_date", 
                                    date=date), 
                    "day": day, 
                    "active": True if date <= today and date >= first_date else False
                }
            generated_week.append(d)
        generated_calendar.append(generated_week)

    return render_template(
        "calendar.html",
        month=month_name,
        year=year,
        calendar=generated_calendar,
        last_month=url_for("main.calendar_view", mdate=last_month),
        next_month=url_for("main.calendar_view", mdate=next_month)
    )

@app.errorhandler(404)
@login_required
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404