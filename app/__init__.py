"""15th Night Flask App."""

from email_client import send_email
from flask import (
    Flask, render_template, redirect, url_for, request, session, flash
)
from flask.ext.login import (
    login_user, current_user, login_required, LoginManager
)
from sqlalchemy import or_
from twilio_client import send_sms

from app import database
from app.database import db_session
from app.forms import RegisterForm, LoginForm, AlertForm
from app.models import User, Alert


flaskapp = Flask(__name__)


try:
    flaskapp.config.from_object('config')
except:
    flaskapp.config.from_object('configdist')

flaskapp.secret_key = flaskapp.config['SECRET_KEY']

login_manager = LoginManager()
login_manager.init_app(flaskapp)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    """User loading needed by Flask-Login."""
    return User.query.get(int(id))


@flaskapp.teardown_appcontext
def shutdown_session(response):
    """Database management."""
    database.db_session.remove()


@flaskapp.route('/')
def index():
    """Handle routing to the dashboard if logged in or the login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@flaskapp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register a user."""
    form = RegisterForm()
    data = ['Shelter', 'Clothes', 'Food', 'Other']
    if request.method == 'POST' and form.validate():
        user = User(
            email=form.email.data,
            password=form.password.data,
            phone_number=form.phone_number.data,
            other=form.other.data,
            shelter=form.shelter.data,
            food=form.food.data,
            clothes=form.clothes.data,
            role=form.role.data
        )
        user.save()

        session['logged_in'] = True
        login_user(user)
        flash("You have registered!")
        return redirect(url_for('dashboard'))

    return render_template('register.html', form=form, data=data)


@flaskapp.route('/login', methods=['GET', 'POST'])
def login():
    """Route for handling the login page logic."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    error = None
    # creates instance of form
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.get_by_email(request.form['email'].lower())
            passwd = request.form.get("password")
            if user is not None and user.check_password(passwd):
                # session cookie in browser
                session['logged_in'] = True
                login_user(user)
                flash('You were logged in.')
                return redirect(url_for('dashboard'))
                error = 'Invalid Credentials. Please try again.'
            else:
                error = 'Invalid Credentials. Please try again.'

    return render_template('login.html', form=form, error=error)


@flaskapp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Dashboard."""
    if current_user.role == 'admin':
        # Admin user, show register form
        form = RegisterForm()
        if request.method == 'POST' and form.validate_on_submit():
            user = User(
                email=form.email.data,
                password=form.password.data,
                phone_number=form.phone_number.data,
                other=form.other.data,
                shelter=form.shelter.data,
                food=form.food.data,
                clothes=form.clothes.data,
                role=form.role.data
            )
            user.save()
        return render_template('dashboard/admin.html', form=form)
    elif current_user.role == 'advocate':
        # Advocate user, show alert form
        form = AlertForm()
        if request.method == 'POST' and form.validate_on_submit():
            alert = Alert(
                description=form.description.data,
                other=form.other.data,
                shelter=form.shelter.data,
                food=form.food.data,
                clothes=form.clothes.data,
                # user.id
                user_id=current_user.id
            )
            alert.save()
            users_to_notify = User.query.filter(or_(
                User.food == alert.food,
                User.shelter == alert.shelter,
                User.clothes == alert.clothes,
                User.other == alert.other
            ))
            for user in users_to_notify:
                print("found user to notify {}".format(user))
                send_sms(
                    to_number=user.phone_number,
                    body=(
                        "There is a new 15th night alert. Go to <link> "
                        "to check it out."
                    )
                )
        return render_template('dashboard/advocate.html', form=form)
    else:
        # Provider user, show alerts
        return render_template('dashboard/provider.html', user=current_user)


@flaskapp.route("/logout")
@login_required
def logout():
    """User logout."""
    session.clear()
    flash('You have been logged out!')
    return redirect(url_for('register'))


@flaskapp.route('/health')
def healthcheck():
    """Low overhead health check."""
    return 'ok', 200


@flaskapp.route('/about')
def about():
    """Simple about page route."""
    return render_template('about.html')


@flaskapp.route('/respond_to/<int:alert_id>', methods=['POST'])
@login_required
def response_submitted(alert_id):
    """
    Action performed when a response is provided.

    Text the creator of the alert:
        - email, phone, and things able to help with of the responding user.
    """
    responding_user = current_user
    try:
        alert = db_session.query(Alert).filter(id=alert_id)
    except:
        return 'error', 404

    user_to_message = alert.user
    response_message = "%s" % responding_user.email
    if responding_user.phone_number:
        response_message += ", %s" % responding_user.phone_number

    response_message += " is availble for: "
    availble = {
        "shelter": responding_user.shelter,
        "clothes": responding_user.clothes,
        "food": responding_user.food,
        "other": responding_user.other,
    }
    response_message += "%s" % ", ".join(k for k, v in availble.items() if v)

    if user_to_message.phone_number:
        send_sms(
            user_to_message.phone_number,
            response_message
        )

    send_email(
        to=user_to_message.email,
        subject="Alert Response",
        body=response_message,
    )

    return "Your message has been sent.", 400

if __name__ == '__main__':
    flaskapp.run(debug=True)
