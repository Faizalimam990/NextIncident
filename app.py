from flask import Flask, render_template, redirect, url_for, request, flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,TextAreaField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user

# Flask App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Faizals_nxt_!ncident'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model (For User Authentication)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    usertype=db.Column(db.String(200), default='employee')

# Incident Model (For Reporting Incidents)
from datetime import datetime

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reported_by = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
# Register Form
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class IncidentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Report')

# Load User for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/delete-incident/<int:incident_id>', methods=['POST'])
def delete_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    db.session.delete(incident)
    db.session.commit()
    flash('Incident deleted successfully.', 'success')
    return redirect(url_for('view_incident'))


@app.route('/update-status/<int:incident_id>', methods=['POST'])
def update_status(incident_id):
    new_status = request.form.get('status')
    incident = Incident.query.get_or_404(incident_id)
    incident.status = new_status
    db.session.commit()
    flash('Incident status updated successfully.', 'success')
    return redirect(url_for('view_incident'))


# Home Route (Landing Page)
@app.route('/')
def home():
    return render_template('home.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            # Redirect based on usertype
            if user.usertype == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('report_incident_employee'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/report_incident_employee', methods=['GET', 'POST'])
@login_required
def report_incident_employee():
    form = IncidentForm()

    if form.validate_on_submit():
        incident = Incident(
            title=form.title.data,
            description=form.description.data,
            reported_by=current_user.username,
            status="Pending"
        )
        db.session.add(incident)
        db.session.commit()
        flash('Incident reported successfully.', 'success')
        return redirect(url_for('report_incident_employee'))

    # Get top 5 latest incidents by this user
    recent_incidents = Incident.query \
                            .order_by(Incident.created_at.desc()) \
                            .limit(5) \
                            .all()


    return render_template('report_incident_employee.html', form=form, recent_incidents=recent_incidents)



# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()

        if existing_user:
            if existing_user.username == form.username.data:
                flash('Username already exists. Please choose another.', 'danger')
            elif existing_user.email == form.email.data:
                flash('Email already registered. Please use a different one.', 'danger')
            return render_template('register.html', form=form)

        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    form = IncidentForm()

    # Count incidents by status
    total_incident=Incident.query.count()
    pending_count = Incident.query.filter_by(status='Pending').count()
    assigned_count = Incident.query.filter_by(status='Assigned').count()
    completed_count = Incident.query.filter_by(status='Completed').count()

    # Total registered users
    total_users = User.query.count()

    return render_template(
        'dashboard.html',
        form=form,
        pending=pending_count,
        assigned=assigned_count,
        completed=completed_count,
        total_users=total_users,
        total=total_incident
    )

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Report Incident Route
@app.route('/report', methods=['POST'])
@login_required
def report():
    form = IncidentForm()
    if form.validate_on_submit():
        new_incident = Incident(
            title=form.title.data,
            description=form.description.data,
            reported_by=current_user.username
        )
        db.session.add(new_incident)
        db.session.commit()
        flash("Incident reported successfully!", "success")
    return redirect(url_for('dashboard'))

@app.route('/view-incident')
def view_incident():
    incidents = db.session.query(Incident).all()  # Or Incident.query.all() if using Flask-SQLAlchemy
    return render_template('view_incidents.html', incidents=incidents)

@app.route('/api/create-admin', methods=['POST'])
def create_admin():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if user already exists
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 409

    hashed_password = generate_password_hash(password)
    admin_user = User(
        username=username,
        email=email,
        password=hashed_password,
        usertype='admin'
    )
    db.session.add(admin_user)
    db.session.commit()

    return jsonify({'message': 'Admin user created successfully'}), 201

if __name__ == '__main__':
    # Create the tables before the app starts
    with app.app_context():
        db.create_all()  # Creates all the tables
    app.run(debug=True)