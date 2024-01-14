import datetime

from flask import url_for, abort

from werkzeug.datastructures import ImmutableMultiDict

from sqlalchemy.sql import func

from . import db
from .models import JournalEntry, HabitEntry, Habit, State, StateEntry


class GeneralUtils:
    @classmethod
    def get_min_date(
            cls,
            uid: int
        ) -> datetime.date:
        """
        Returns date of first ever user's entry

        If user doesn't have any entries then return today date.

        Argument
            uid - user's id
        """
        min_date = db.session.scalar(
            func.min(
                db.select(JournalEntry.date).filter_by(user_id=uid)
            )   
        )

        if min_date is None:
            min_date = datetime.date.today().strftime(r"%Y%m%d")

        return min_date


class CalendarUtils:
    @classmethod
    def get_next_and_previous_months(
            cls,
            month: str, 
            year: str
        ) -> (str, str):
        """
        Returns year and number of month for next and previous months
        for given current one.

        Arguments:
            month -- current month as a string eg. '01' or '12'
            year --  current year as a string
        """
        if month == "01":
            last_m = "12"
            next_m = "02"
            last_y = f"{int(year)-1}".zfill(4)
            next_y = year

        elif month == "12":
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

        return last_month, next_month

    @classmethod
    def generate_calendar_table(
            cls,
            cal: list[list[int]],
            uid: int,
            mdate: str
        ) -> list[list[dict]]:
        """
        Generate  and return table with calendar values, that will be used to
        render proper calendar for given month and given user.

        Arguments:
            cal -- calendar's object for given month
            uid -- current user's id
            mdate -- date entered in format YYYYMM, where Y = Year,
                M = Month. For example 202302 
        """
        
        today = datetime.date.today().strftime(r"%Y%m%d")

        min_date = GeneralUtils.get_min_date(uid)
        first_date = min_date.strftime(r"%Y%m%d")

        generated_calendar = []
        for week in cal:
            generated_week = []
            for day in week:
                if day == 0: 
                    # calendar's representation of month fills lacking days with zeros
                    d = {}
                else:
                    date = f"{mdate}{str(day).zfill(2)}"
                    d = {
                        "link": url_for("main.day_date",date=date), 
                        "day": day, 
                        "is_active": True if first_date <= date <= today else False
                    }
                generated_week.append(d)
            generated_calendar.append(generated_week)
        return generated_calendar


class DataOperationUtils:
    @classmethod
    def update_note(
            cls,
            uid: int,
            form: ImmutableMultiDict,
            date: datetime.date
        ) -> None:
        """
        Update journal note for given day, using data entered to form.
        """
        journal_entry = db.session.scalar(
            db.select(JournalEntry)
            .filter_by(user_id=uid, date=date)
        )
        journal_entry.note = form.get("journal_entry")

    @classmethod
    def get_habit_value(
            cls,
            habit: Habit,
            form: ImmutableMultiDict
        ) -> bool:
        """
        Get habit value from form.
        """
        if habit.name in form.keys():
            habit_value = True
        else:
            habit_value = False

        return habit_value

    @classmethod
    def get_state_value(
            cls,
            state: State,
            form: ImmutableMultiDict
        ) -> int:
        """
        Get state value from form.
        """
        if state.name in form.keys():
            state_value = form.get(state.name)
        else:
            state_value = None

        return state_value

    @classmethod
    def update_states(
            cls,
            states: list[State], 
            date: datetime.date, 
            form: ImmutableMultiDict
        ) -> None:
        """
        Update values for given states, using data entered to form.
        """

        for state in states:
            state_value = cls.get_state_value(state, form)

            state_entry = db.session.scalar(
                db.select(StateEntry)
                .filter_by(state_id=state.id, date=date)
            )
            state_entry.value = state_value

    @classmethod
    def update_habits(
            cls,
            habits: list[Habit], 
            date: datetime.date, 
            form: ImmutableMultiDict
        ) -> None:
        """
        Update values for given habits, using data entered to form.
        """

        for habit in habits:
            habit_value = cls.get_habit_value(habit, form)

            habit_entry = db.session.scalar(
                db.select(HabitEntry)
                .filter_by(habit_id=habit.id, date=date)
            )
            habit_entry.value = habit_value

    @classmethod
    def save_journal_entry(
            cls,
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

    @classmethod
    def save_habit_entries(
            cls,
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

            cls.save_habit_entry(habit.id, date, habit_value)

    @classmethod
    def save_state_entries(
            cls,
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

            cls.save_state_entry(state.id, date, state_value)

    @classmethod
    def save_habit_entry(
            cls,
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

    @classmethod
    def save_state_entry(
            cls,
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

    @classmethod
    def add_missing_entries(
        cls,
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

class DatetimeUtils:
    @classmethod
    def parse_data_parameter(
            cls,
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
    
    @classmethod
    def handle_requested_date_out_of_range(
            cls,
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