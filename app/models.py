import datetime

from flask_login import UserMixin
from sqlalchemy.sql import func

from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    user = db.session.scalar(
        db.select(User).filter_by(id=int(user_id))
    )
    return user


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    journal_entries = db.relationship('JournalEntry', backref='user', cascade='all, delete, delete-orphan')
    habits = db.relationship('Habit', backref='user', cascade='all, delete, delete-orphan')
    states = db.relationship('State', backref='user', cascade='all, delete, delete-orphan')

    def get_min_date(
            self
        ) -> datetime.date:
        """
        Returns date of first ever user's entry

        If user doesn't have any entries then return today date.
        """
        min_date = db.session.scalar(
            func.min(
                db.select(JournalEntry.date).filter_by(user_id=self.id)
            )
        )

        if min_date is None:
            min_date = datetime.date.today()

        return min_date

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.Text)
    start_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean)

    habit_entries = db.relationship('HabitEntry', backref='habit', cascade='all, delete, delete-orphan')


class HabitEntry(db.Model):
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    value = db.Column(db.Boolean, nullable=False)


class JournalEntry(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    note = db.Column(db.Text)


class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.Text)
    start_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean)

    state_entries = db.relationship('StateEntry', backref='state', cascade='all, delete, delete-orphan')


class StateEntry(db.Model):
    state_id = db.Column(db.Integer, db.ForeignKey("state.id"), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    value = db.Column(db.Integer, nullable=True)
