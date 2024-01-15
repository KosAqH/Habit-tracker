from functools import wraps
from flask import Blueprint, render_template, redirect, request, url_for, flash
from app import app, db
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from flask_login import login_user, logout_user, login_required
from flask_login import current_user

auth = Blueprint('auth', __name__)

def only_anonymous_users(f):
    @wraps(f)
    def decorated_view(*args, **kwargs): 
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        else:
            return f(*args, **kwargs)

    return decorated_view

@auth.route('/login', methods=['GET'])
@only_anonymous_users
def login():
    """
    Render login page.
    """
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
@only_anonymous_users
def login_post():
    """
    Handle user's request to log in.
    """
    email = request.form.get('email')
    password = request.form.get('password')

    user = db.session.scalar(
        db.select(User).filter_by(email=email)
    )
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))

    # if the above check passes, then we know the user has the right credentials
    login_user(user)
    return redirect(url_for('main.index'))

@auth.route('/signup', methods=['GET'])
@only_anonymous_users
def signup():
    """
    Render signup page
    """
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
@only_anonymous_users
def signup_post():
    """
    Handle user's request to sign up. 
    """
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = db.session.scalar(
        db.select(User).filter_by(email=email)
    )
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
    """
    Handle user's request to log out.
    """
    logout_user()
    return redirect(url_for('auth.login'))