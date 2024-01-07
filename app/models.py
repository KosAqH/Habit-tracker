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

    #journal_entries = db.relationship('JournalEntry', backref='user', cascade='all, delete, delete-orphan')

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey("User.id"))
    name = db.Column(db.Text)
    start_date = db.Column(db.Date)
    is_active = db.Column(db.Bool)

    habit_entries = db.relationship('Habit', backref='user', cascade='all, delete, delete-orphan')

class HabitEntry(db.Model):
    habit_id = db.Column(db.ForeignKey("Habit.id"))
    date = db.Column(db.Date)
    value = db.Column(db.Bool)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey("User.id"))
    date = db.Column(db.Date)
    note = db.Column(db.Text)
