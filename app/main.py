import datetime
import calendar

from flask import Blueprint, Response
from flask import render_template, redirect, abort, url_for
from flask import request

from flask_login import login_required
from flask_login import current_user

from . import db, app
from .models import User, JournalEntry, HabitEntry, Habit, State, StateEntry
from .plot_handler import PlotManager
from .utils import CalendarUtils, DataOperationUtils, DatetimeUtils


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
        DataOperationUtils.save_journal_entry(uid, today, journal_entry)

        # handle habits
        user_habits = db.session.scalars(
            db.select(Habit).filter_by(user_id=uid)
        ).all()
        DataOperationUtils.save_habit_entries(user_habits, request.form, today)
        
        # handle states
        user_states = db.session.scalars(
            db.select(State).filter_by(user_id=uid)
        ).all()
        DataOperationUtils.save_state_entries(user_states, request.form, today)

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
def day_date(date) -> str | Response:
    """
    View rendering page with tracked data about particular day

    Parameters:
        date -- date entered in format YYYYMMDD, where Y = Year,
            M = Month and D = Day. For example 20230220
    """
    uid = current_user.id

    try:
        parsed_date = datetime.datetime.strptime(date, r"%Y%m%d").date()
    except ValueError:
        abort(404)
    
    # redirect if date is future
    if parsed_date > datetime.date.today():
        return redirect(url_for("main.future"))

    min_date = current_user.get_min_date()
    # redirect if date is prior first user's entry
    if parsed_date < min_date:
        return redirect(url_for("main.past"))
    
    # determine if given date is first or the last day of user's entry 
    is_last_day = False
    is_first_day = False

    if parsed_date == datetime.date.today():
        is_last_day = True
    if parsed_date <= min_date:
        is_first_day = True

    last_day = (parsed_date - datetime.timedelta(days=1)).strftime(r'%Y-%m-%d')
    next_day = (parsed_date + datetime.timedelta(days=1)).strftime(r'%Y-%m-%d')

    # get all habit entries from this day
    habits_entries = db.session.scalars(
        db.select(HabitEntry).filter_by(date=parsed_date)
        .join(Habit).filter_by(user_id=uid)
    ).all()

    # get all state entries from this day
    state_entries = db.session.scalars(
        db.select(StateEntry).filter_by(date=parsed_date)
        .join(State).filter_by(user_id=uid)
    ).all()

    # get journal entry from this day
    journal_entry = db.session.scalar(
        db.select(JournalEntry)
        .filter_by(user_id=uid, date=parsed_date)
    )

    note = journal_entry.note if journal_entry else ""

    return render_template(
        "day.html",
        current_date = parsed_date,
        current_date_link = parsed_date.strftime(r"%Y%m%d"),
        last_date = last_day,
        last_date_link = last_day.replace("-", ""),
        next_date = next_day,
        next_date_link = next_day.replace("-", ""),
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
        DataOperationUtils.save_journal_entry(uid, date, journal_entry)

        # save_habits
        user_habits = db.session.scalars(
            db.select(Habit).filter_by(user_id=uid).filter(Habit.start_date <= date)
            # only habits that started not later than specified day
        ).all()
        DataOperationUtils.save_habit_entries(user_habits, request.form, date)

        # handle states
        user_states = db.session.scalars(
            db.select(State).filter_by(user_id=uid).filter(State.start_date <= date)
            # only states that started not later than specified day
        ).all()
        DataOperationUtils.save_state_entries(user_states, request.form, date)

        db.session.commit()
    
    return redirect(f"day/{raw_date}")

@main.route('/edit/<date>', methods = ['GET'])
@login_required
def edit(date):
    """
    Returning edit day form, that is filled with already
    entered values.

    Parameters:
        date -- date entered in format YYYYMMDD, where Y = Year,
                M = Month and D = Day. For example 20230220
    """
    uid = current_user.id
    date = DatetimeUtils.parse_data_parameter(date)

    # handle request for date in future
    # or in past, if it's before first user's entries
    oldest_date = current_user.get_min_date()
    page_to_redirect = DatetimeUtils.handle_requested_date_out_of_range(date, oldest_date)
    if page_to_redirect:
        return redirect(page_to_redirect)
    
    # handle attempt to edit null entry
    if is_entry_empty(uid, date):
        return redirect(url_for("main.new_entry", date=date.strftime(r"%Y%m%d")))
    
    habits = current_user.habits
    states = current_user.states

    # add missing entries if habit or state was created 
    # after some entries to this day was already entered
    DataOperationUtils.add_missing_entries(habits, states, date)

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
def edit_post() -> Response:
    """
    Handle data entered by user on edit page
    """
    uid = current_user.id

    try:
        date = request.referrer.split("/")[-1]
        formated_date = datetime.datetime.strptime(date, r"%Y%m%d").strftime(r"%Y-%m-%d")
    except:
        abort(404)

    user_habits = db.session.scalars(
        db.select(Habit).filter_by(user_id = uid).filter(Habit.start_date <= formated_date)
    ).all()
    DataOperationUtils.update_habits(user_habits, formated_date, request.form)

    user_states =  db.session.scalars(
        db.select(State).filter_by(user_id = uid).filter(State.start_date <= formated_date)
    ).all()
    DataOperationUtils.update_states(user_states, formated_date, request.form)
    
    DataOperationUtils.update_note(uid, request.form, formated_date)
    
    db.session.commit()
    return redirect(f"day/{date}")

@main.route('/calendar/', methods = ['GET'])
@login_required
def calendar_date_not_given() -> Response:
    """
    View redirect user to current month's page,
    if he enters url without specified mdate parameter.
    """
    current_month = datetime.date.today().strftime(r"%Y%m")
    return redirect(url_for("main.calendar_view", mdate=current_month))

@main.route('/calendar/<mdate>', methods = ['GET'])
@login_required
def calendar_view(mdate) -> str:
    """
    View renders calendar page for given month and year.
    
    Parameters:
        mdate -- date entered in format YYYYMM, where Y = Year,
            M = Month. For example 202302 
    """
    year = mdate[:4]
    month = mdate[4:]
    uid = current_user.id

    try:
        cal = calendar.monthcalendar(int(year), int(month))
    except:
        abort(404)

    last_month, next_month = CalendarUtils.get_next_and_previous_months(month, year)

    generated_calendar = CalendarUtils.generate_calendar_table(cal, uid, mdate)
    month_name = calendar.month_name[(int(month))]

    return render_template(
        "calendar.html",
        month=month_name,
        year=year,
        calendar=generated_calendar,
        last_month=url_for("main.calendar_view", mdate=last_month),
        next_month=url_for("main.calendar_view", mdate=next_month)
    )
