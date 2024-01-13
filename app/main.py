import datetime
import calendar

from flask import Blueprint
from flask import render_template, redirect, abort, url_for
from flask import request

from flask_login import login_required
from flask_login import current_user

from werkzeug.datastructures import ImmutableMultiDict

from sqlalchemy.sql import func

from . import db, app
from .models import User, JournalEntry, HabitEntry, Habit, State, StateEntry
from .plot_handler import PlotManager


main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
@main.route('/dashboard')
@login_required
def index():
    """
    Returning main page of logged in user.
    """
    uid = current_user.id
    today = datetime.date.today()
    today_raw = today.strftime(r"%Y%m%d")
    
    does_today_entry_exists = is_entry_empty(uid, today)
    
    habits = current_user.habits
    states = current_user.states

    pm = PlotManager(today, does_today_entry_exists )
    pm.make_plots(habits, "Habit")
    pm.make_plots(states, "State")

    return render_template(
        'index.html',
        today_date = today_raw,
        habits = habits,
        states = states,
        is_entry_empty = does_today_entry_exists
    )

def save_journal_entry(
        uid: int,
        date: datetime.date,
        note: str
    ) -> None:
    """
    Save journal entry to database.

    Arguments:
        uid -- user's id
        date -- date object
        note -- string containing journal entry
    """
    journal = JournalEntry(
            user_id = uid,
            date = date,
            note = note
        )
    
    db.session.add(journal)

def save_habit_entries(
        habits: list[Habit],
        fields: ImmutableMultiDict[str, str],
        date: datetime.date
    ) -> None:
    """
    Save all habit entries to database

    Arguments:
        habits -- collection containing all Habit objects, belonging
            to one user
        checked_values -- dict containing all names of entered form fields
        date -- date object
    """
    for habit in habits:
        if fields.get(habit.name, default=False):
            habit_value = True
        else:
            habit_value = False

        save_habit_entry(habit.id, date, habit_value)

def save_state_entries(
        states: list[State],
        fields: ImmutableMultiDict[str, str],
        date: datetime.date
    ) -> None:
    """
    Save all state entries to database

    Arguments:
        states -- collection containing all State objects, belonging
            to one user
        checked_values -- dict containing all names of entered form fields
        date -- date object
    """
    for state in states:
        state_value = fields.get(state.name, default=-1)

        save_state_entry(state.id, date, state_value)

def save_habit_entry(
        habit_id: int,
        date: datetime.date,
        value: bool
    ) -> None:
    """
    Add one habit entry to database.

    Arguments:
        habit_id -- id of habit
        date -- date object
        value -- value of entry
    """
    habit_entry = HabitEntry(
        habit_id = habit_id,
        date = date,
        value = value
    )
    
    db.session.add(habit_entry)

def save_state_entry(
        state_id,
        date,
        value
    ) -> None:
    """
    Add one state entry to database.

    Arguments:
        state_id -- id of state
        date -- date object
        value -- value of entry
    """
    state_entry = StateEntry(
        state_id = state_id,
        date = date,
        value = value
    )
    
    db.session.add(state_entry)

@main.route('/send_form', methods = ['POST'])
@login_required
def index_post():
    """
    Handle data entered by user on main page
    """
    if request.form:
        uid = current_user.id
        today = datetime.date.today()

        # handle journal
        journal_entry = request.form.get("journal_entry")
        save_journal_entry(uid, today, journal_entry)

        # handle habits
        user_habits = db.session.scalars(
            db.select(Habit).filter_by(user_id=uid)
        ).all()
        save_habit_entries(user_habits, request.form, today)
        
        # handle states
        user_states = db.session.scalars(
            db.select(State).filter_by(user_id=uid)
        ).all()
        save_state_entries(user_states, request.form, today)

        db.session.commit()

    return redirect(url_for("main.index"))

@main.route('/future', methods = ['GET'])
@login_required
def future():
    """
    View used when user try to see day page for future date
    """
    return render_template("future.html")

@main.route('/past', methods = ['GET'])
@login_required
def past():
    """
    View used when user try to see day page for day before
    this user was tracking any activity
    """
    return render_template("past.html")

@main.route('/day/', methods = ['GET'])
@login_required
def day_date_not_given():
    """
    View redirect user to today day page, if he enters url
    without specified date parameter.
    """
    current_day = datetime.date.today().strftime(r"%Y%m%d")
    return redirect(url_for("main.day_date", date=current_day))

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

def is_entry_empty(uid, date):
    cnt = JournalEntry.query.filter_by(user_id=uid).filter_by(date=date).count()
    cnt += HabitEntry.query.filter_by(date=date).join(Habit).filter(Habit.user_id=="uid").count()
    cnt += StateEntry.query.filter_by(date=date).join(State).filter(State.user_id=="uid").count()
    is_entry_empty = not cnt

    return is_entry_empty

@main.route('/new/<date>', methods = ['GET'])
@login_required
def new_entry(date):
    """
    Returning page with form, that user can use to enter
    data about particular day.

    parameters:
        date -- date entered in format YYYYMMDD, where Y = Year,
            M = Month and D = Day. For example 20230220
    """
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
    """
    Handle data entered by user on new_entry page
    """
    if request.form:
        uid = current_user.id
        raw_date = request.referrer.split("/")[-1]
        date = datetime.datetime.strptime(raw_date, r"%Y%m%d")

        # save_entry
        journal_entry = request.form.get("journal_entry")
        save_journal_entry(uid, date, journal_entry)

        # save_habits
        user_habits = db.session.scalars(
            db.select(Habit).filter_by(user_id=uid).filter(Habit.start_date <= date)
            # only habits that started not later than specified day
        ).all()
        save_habit_entries(user_habits, request.form, date)

        # handle states
        user_states = db.session.scalars(
            db.select(State).filter_by(user_id=uid).filter(State.start_date <= date)
            # only states that started not later than specified day
        ).all()
        save_state_entries(user_states, request.form, date)

        db.session.commit()
    
    return redirect(f"day/{raw_date}")

def parse_data_parameter(
        date: str
    ) -> datetime.date:
    """
    Try to parse date and return date object. If action fail, then
    raise 404 error.

    Argument:
        date -- date save as a string in format YYYYMMDD, where Y = Year,
            M = Month and D = Day. For example 20230220
    """
    try:
        parsed_date = datetime.datetime.strptime(date, r"%Y%m%d")
    except ValueError:
        abort(404)
    return parsed_date.date()

def add_missing_entries(
        habits: list[Habit],
        states: list[State],
        date: datetime.date
    ) -> None:
    """
    Create entries for habits and states with default value and with given
    date attribute.
    They are created only to be replaced by user input. They have to be created,
    so edit form will be displayed correctly.

    Arguments:
        habits -- collection containing all Habit objects, belonging
            to one user
        states -- collection containing all State objects, belonging
            to one user
        date -- date object
    """
    for habit in habits:
        if not habit.habit_entries and date <= habit.start_date:
            entry = HabitEntry(
                habit_id=habit.id,
                date=date,
                value=False
            )
            db.session.add(entry)
        
    for state in states:
        if not state.state_entries and date <= state.start_date:
            entry = StateEntry(
                state_id=state.id,
                date=date,
                value=-1
            )
            db.session.add(entry)
    db.session.commit()

def get_oldest_user_entry_date(
        uid: int
    ) -> datetime.date:
    """
    Do query to db to find the oldest user entry. Then return it.
    If user doesn't have any entries then return today date.

    Argument
        uid - user's id
    """
    min_date = db.session.scalar( 
        func.min(
            db.select(Habit.start_date).filter_by(user_id=uid)
        )   
    )

    if min_date is None:
        min_date = datetime.date.today().strftime(r"%Y%m%d")

    return min_date

def handle_requested_date_out_of_range(
        entered_date :datetime.date, 
        oldest_date: datetime.date
    ) -> str | None:
    """
    Return url to future view, if entered date is later than current.
    Return url to past view, if entered date is prior to first date
        containing any entries.
    Return None if given date is in range of user's entries.

    Arguments:
        entered_date -- requested date
        oldest_date -- the oldest found date of any current user's entry
    """
    if entered_date > datetime.date.today():
        return url_for("main.future")
    elif entered_date < datetime.datetime.strptime(oldest_date, r"%Y%m%d").date():
        return url_for("main.past")
    else:
        return None

@main.route('/edit/<date>', methods = ['GET'])
@login_required
def edit(date):
    """
    Returning edit day form, that is filled with already
    entered values.
    """
    uid = current_user.id
    date = parse_data_parameter(date)

    # handle request for date in future
    # or in past, if it's before first user's entries
    oldest_date = get_oldest_user_entry_date(uid)
    page_to_redirect = handle_requested_date_out_of_range(date, oldest_date)
    if page_to_redirect:
        return redirect(page_to_redirect)
    
    # handle attempt to edit null entry
    if is_entry_empty(uid, date):
        return redirect(url_for("main.new_entry", date=date.strftime(r"%Y%m%d")))
    
    habits = current_user.habits
    states = current_user.states

    # add missing entries if habit or state was created 
    # after some entries to this day was already entered
    add_missing_entries(habits, states, date)

    habits_entries = db.session.scalars(
        db.select(HabitEntry).filter_by(date=date)
        .join(Habit).filter_by(user_id=uid)
    ).all()

    state_entries = db.session.scalars(
        db.select(StateEntry).filter_by(date=date)
        .join(State).filter_by(user_id=uid)
    ).all()

    journal_entry = db.session.scalar(
        db.select(JournalEntry)
        .filter_by(user_id=uid, date=date)
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
    """
    Render settings page
    """
    uid = current_user.id
    return render_template(
        "settings.html",
        habits = User.query.filter_by(id=uid).first().habits,
        states = User.query.filter_by(id=uid).first().states
    )

@main.route('/add_habit', methods = ['POST'])
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

    return redirect(url_for("main.settings"))

@main.route('/add_state', methods = ['POST'])
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

    return redirect(url_for("main.settings"))

@main.route('/delete_habit', methods = ['POST'])
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
    return redirect(url_for("main.settings"))

@main.route('/delete_state', methods = ['POST'])
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
    return redirect(url_for("main.settings"))

@main.route('/calendar/', methods = ['GET'])
@login_required
def calendar_date_not_given():
    """
    View redirect user to current month's page,
    if he enters url without specified mdate parameter.
    """
    current_month = datetime.date.today().strftime(r"%Y%m")
    return redirect(url_for("main.calendar", mdate=current_month))

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
