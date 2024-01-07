from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    journal_entries = db.relationship('JournalEntry', backref='user', cascade='all, delete, delete-orphan')
    habits = db.relationship('Habit', backref='user', cascade='all, delete, delete-orphan')

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
