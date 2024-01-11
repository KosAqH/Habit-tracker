from functools import wraps
from flask import Blueprint, render_template, redirect, request, url_for, flash
from app import app, db
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from flask_login import login_user, logout_user, login_required
from flask_login import current_user

auth = Blueprint('auth', __name__)

def login_forbidden(f):
    @wraps(f)
    def decorated_view(*args, **kwargs): 
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        else:
            return f(*args, **kwargs)

    return decorated_view

@auth.route('/login', methods=['GET'])
@login_forbidden
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
@login_forbidden
def login_post():
    # login code goes here
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user)
    return redirect(url_for('main.index'))

@auth.route('/signup', methods=['GET'])
@login_forbidden
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
@login_forbidden
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    new_user = User(email=email, 
                    name=name, 
                    password=generate_password_hash(password)
                )
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))