from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from random import randint
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
from functools import wraps
from admin.routes import admin_bp
from models import db, User, Announcement, CertificateRequest, Complaint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cadaypogi')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# MySQL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:{os.environ.get('MYSQL_PASSWORD')}@{os.environ.get('MYSQL_HOST')}/{os.environ.get('MYSQL_DATABASE')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

# Debug: Print mail config (remove in production)
print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
print(f"MAIL_PASSWORD: {'*' * len(app.config['MAIL_PASSWORD']) if app.config['MAIL_PASSWORD'] else 'None'}")
print(f"MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")

# Register admin blueprint
app.register_blueprint(admin_bp, url_prefix="/admin")

# Upload folder for certificates
UPLOAD_FOLDER_CERTIFICATES = os.path.join(app.root_path, 'static', 'uploads', 'certificates')
os.makedirs(UPLOAD_FOLDER_CERTIFICATES, exist_ok=True)

# Upload folder for complaints evidence
UPLOAD_FOLDER_COMPLAINTS = os.path.join(app.root_path, 'static', 'uploads', 'complaints')
os.makedirs(UPLOAD_FOLDER_COMPLAINTS, exist_ok=True)

# Dummy admin credentials (in production, store in Supabase)
# ADMIN_USERNAME = "admin"
# ADMIN_PASSWORD = "cadaypogi"

# Sec_USERNAME = "adminsec"
# SEC_PASS = "adminsec"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def send_email(to, subject, body, html=None):
    """Send email using Flask-Mail"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            body=body,
            html=html
        )
        mail.send(msg)
        print(f"Email sent successfully to {to}")
        return True
    except Exception as e:
        print(f"Error sending email to {to}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def login_required(f):
    """Decorator to require login for resident routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Kailangan mag-login muna.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def splash():
    """Splash screen"""
    return render_template('splash.html')

@app.route('/home')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            # Fetch user from MySQL
            user = User.query.filter_by(username=username).first()

            if not user:
                flash('Walang account na may ganyang username.', 'error')
                return redirect(url_for('login'))

            # Validate password
            if not check_password_hash(user.password, password):
                flash('Maling password.', 'error')
                return redirect(url_for('login'))

            # ✅ Store session info
            session['user_id'] = user.id
            session['email'] = user.email
            session['username'] = user.username
            session['role'] = user.role or 'resident'  # Default to resident
            session['first_name'] = user.first_name

            # ✅ Set admin_logged_in for admin role
            if session['role'] == 'admin':
                session['admin_logged_in'] = True

            # ✅ Redirect based on role
            if session['role'] == 'admin':
                flash(f"Welcome back, Admin {user.first_name}!", "success")
                return redirect(url_for('admin_bp.admindashboard'))  # replace with your admin dashboard route
            else:
                flash(f"Welcome, {user.first_name}!", "success")
                return redirect(url_for('dashboard'))  # resident dashboard

        except Exception as e:
            print("Login error:", e)
            flash(f"Login failed: {str(e)}", "error")
            return redirect(url_for('login'))

    return render_template('residents/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        if not session.get('email_verified'):
            flash('Please verify your email first.', 'error')
            return redirect(url_for('register'))

        username = request.form.get('username')
        email = session.get('pending_email')  # Use verified email from session
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        # Validate
        if password != confirm_password:
            flash('Hindi tugma ang mga password.', 'error')
            return redirect(url_for('register'))

        try:
            # Check if username exists
            existing = User.query.filter_by(username=username).first()
            if existing:
                flash('Username ay ginagamit na.', 'error')
                return redirect(url_for('register'))

            # Check if email exists
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Email ay ginagamit na.', 'error')
                return redirect(url_for('register'))

            # Create user
            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                role='resident'  # ✅ Default role
            )

            db.session.add(new_user)
            db.session.commit()

            # Optional: clear verification session
            session.pop('email_verified', None)
            session.pop('pending_email', None)

            flash('Registration completed successfully!', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            print("Registration error:", e)
            flash(f"Error: {str(e)}", "error")

    return render_template('residents/register.html')


@app.route('/send-verification-code', methods=['POST'])
def send_verification_code():
    """Send verification code via AJAX"""
    try:
        data = request.json
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if not email or not username or not password:
            return jsonify({'success': False, 'message': 'Email, username, and password are required'}), 400

        # Store registration data in session
        session['pending_username'] = username
        session['pending_email'] = email
        session['pending_password'] = password

        # Generate verification code
        verification_code = randint(100000, 999999)
        session['verification_code'] = verification_code

        # Send email
        email_sent = send_email(
    to=email,
    subject='Barangay Pulse – Email Verification Code',
    body=(
        "Magandang araw!\n\n"
        "Salamat sa iyong pagrehistro sa *Barangay Pulse* — ang opisyal na online system ng ating barangay.\n\n"
        "Upang kumpirmahin ang iyong email address, mangyaring gamitin ang verification code na nasa ibaba:\n\n"
        f"Verification Code: {verification_code}\n\n"
        "Kung hindi ikaw ang nagsimula ng prosesong ito, maaari mong balewalain ang mensaheng ito.\n\n"
        "Lubos na gumagalang,\n"
        "Barangay Pulse Support Team"
    ),
    html=(
        "<div style='font-family: Arial, sans-serif; color: #333;'>"
        "<h2 style='color: #007b5e;'>Barangay Pulse – Email Verification</h2>"
        "<p>Magandang araw!</p>"
        "<p>Salamat sa iyong pagrehistro sa <strong>Barangay Pulse</strong> — ang opisyal na online system ng ating barangay.</p>"
        "<p>Upang kumpirmahin ang iyong email address, mangyaring gamitin ang verification code na nasa ibaba:</p>"
        f"<p style='font-size: 22px; font-weight: bold; color: #007b5e;'>{verification_code}</p>"
        "<p>Kung hindi ikaw ang nagsimula ng prosesong ito, maaari mong balewalain ang mensaheng ito.</p>"
        "<br>"
        "<p>Lubos na gumagalang,<br><strong>Barangay Pulse Dev</strong></p>"
        "</div>"
    )
)

        # email_sent = send_email(
        #     to=email,
        #     subject='Email Verification Code',
        #     body=f"Your verification code is: {verification_code}",
        #     html=f"<h2>Your Verification Code</h2><p>Your code is: <strong>{verification_code}</strong></p>"
        # )

        if email_sent:
            return jsonify({'success': True, 'message': 'Verification code sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send verification code'}), 500

    except Exception as e:
        print(f"Error sending verification code: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/verify-code', methods=['POST'])
def verify_code():
    """Verify the entered code and set email verified flag"""
    try:
        data = request.json
        entered_code = data.get('code')

        if not entered_code:
            return jsonify({'success': False, 'message': 'Verification code is required'}), 400

        # Check if code matches
        stored_code = session.get('verification_code')
        if not stored_code or str(entered_code) != str(stored_code):
            return jsonify({'success': False, 'message': 'Invalid verification code'}), 400

        # Set email verified flag
        session['email_verified'] = True

        return jsonify({'success': True, 'message': 'Email verified successfully'})

    except Exception as e:
        print(f"Error verifying code: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# ============================================================================
# RESIDENT DASHBOARD ROUTES
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page"""
    try:
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(10).all()
    except Exception as e:
        announcements = []
        print(f"Error fetching announcements: {str(e)}")

    return render_template('residents/resident_dashboard.html', username=session.get('username'), announcements=announcements)

@app.route("/announcement")
@login_required
def announcement():
    """Announcements page"""
    try:
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(10).all()
    except Exception as e:
        announcements = []
        print(f"Error fetching announcements: {str(e)}")

    return render_template("residents/announcement.html", announcements=announcements)


# ============================================================================
# CERTIFICATES ROUTES
# ============================================================================

@app.route("/certificates", methods=['GET', 'POST'])
@login_required
def certificates():
    if request.method == 'POST':
        try:
            # --- Handle optional file upload ---
            valid_id_file = request.files.get('valid_id')
            valid_id_file_url = None

            if valid_id_file and valid_id_file.filename != '':
                filename = secure_filename(valid_id_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{session['user_id']}_{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER_CERTIFICATES, unique_filename)

                try:
                    valid_id_file.save(filepath)
                    valid_id_file_url = f"/static/uploads/certificates/{unique_filename}"
                except Exception as e:
                    print(f"File upload error: {e}")
                    flash('Error uploading file. Skipping file upload.', 'warning')

            # --- Create certificate request ---
            new_request = CertificateRequest(
                user_id=session['user_id'],
                full_name=request.form.get('full_name'),
                contact_number=request.form.get('contact_number'),
                certificate_type=request.form.get('certificate_type'),
                purpose=request.form.get('purpose'),
                valid_id_file_url=valid_id_file_url,
                status='pending'
            )

            db.session.add(new_request)
            db.session.commit()

            flash('Certificate request submitted successfully!', 'success')

        except Exception as e:
            db.session.rollback()
            print(f"Certificate request error: {e}")
            flash(f'Error submitting request: {str(e)}', 'error')

        return redirect(url_for('certificates'))

    # --- Fetch user's certificate requests ---
    try:
        requests = CertificateRequest.query.filter_by(user_id=session['user_id']).order_by(CertificateRequest.created_at.desc()).all()
        # Format dates for display
        for req in requests:
            req.formatted_date = req.created_at.strftime('%B %d, %Y')
    except Exception as e:
        requests = []
        print(f"Error fetching requests: {e}")

    return render_template("residents/certificates.html", requests=requests)

# ============================================================================
# COMPLAINTS/BLOTTER ROUTES
# ============================================================================


@app.route("/complaints", methods=["GET", "POST"])
@login_required
def complaints():
    """Complaints / Blotter page"""
    if request.method == "POST":
        try:
            # ✅ Get form inputs
            incident_type = request.form.get("incident_type")
            incident_date = request.form.get("incident_date")
            location = request.form.get("location")
            description = request.form.get("description")
            persons_involved = request.form.get("persons_involved")

            # ✅ Validate required fields
            if not all([incident_type, incident_date, location, description]):
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("complaints"))

            # ✅ Handle optional evidence file upload
            evidence_file = request.files.get('evidence')
            evidence_file_url = None

            if evidence_file and evidence_file.filename != '':
                filename = secure_filename(evidence_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{session['user_id']}_{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER_COMPLAINTS, unique_filename)

                try:
                    evidence_file.save(filepath)
                    evidence_file_url = f"/static/uploads/complaints/{unique_filename}"
                except Exception as e:
                    print(f"Evidence file upload error: {e}")
                    flash('Error uploading evidence file. Skipping file upload.', 'warning')

            # ✅ Create complaint
            new_complaint = Complaint(
                user_id=session["user_id"],
                incident_type=incident_type,
                incident_date=datetime.strptime(incident_date, '%Y-%m-%d').date(),
                location=location,
                description=description,
                persons_involved=persons_involved,
                evidence_url=evidence_file_url,
                status="pending"
            )

            db.session.add(new_complaint)
            db.session.commit()

            flash("Complaint submitted successfully!", "success")

        except Exception as e:
            db.session.rollback()
            print("Error submitting complaint:", str(e))
            flash(f"An error occurred while submitting your complaint: {str(e)}", "error")

        return redirect(url_for("complaints"))

    # ✅ GET: Fetch all complaints by the logged-in user
    try:
        complaints = Complaint.query.filter_by(user_id=session["user_id"]).order_by(Complaint.created_at.desc()).all()

    except Exception as e:
        print("Error fetching complaints:", e)
        complaints = []
        flash("Unable to fetch complaints at the moment.", "error")

    # ✅ Render template with user complaints
    return render_template("residents/complaint.html", complaints=complaints)


# ============================================================================
# SETTINGS ROUTE
# ============================================================================

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Settings page"""
    if request.method == 'POST':
        try:
            user = User.query.get(session['user_id'])
            if not user:
                flash('User not found.', 'error')
                return redirect(url_for('settings'))

            # Update fields
            if request.form.get('first_name'):
                user.first_name = request.form.get('first_name')
            if request.form.get('last_name'):
                user.last_name = request.form.get('last_name')
            if request.form.get('full_name'):
                user.full_name = request.form.get('full_name')
            if request.form.get('contact_number'):
                user.contact_number = request.form.get('contact_number')
            if request.form.get('address'):
                user.address = request.form.get('address')
            if request.form.get('email'):
                user.email = request.form.get('email')
            if request.form.get('date_of_birth'):
                user.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            if request.form.get('gender'):
                user.gender = request.form.get('gender')

            # Update password if provided
            if request.form.get('new_password'):
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')

                if new_password == confirm_password:
                    user.password = generate_password_hash(new_password)
                else:
                    flash('Passwords do not match.', 'error')
                    return redirect(url_for('settings'))

            db.session.commit()
            flash('Settings updated successfully!', 'success')

            # Update session data if email or name changed
            if request.form.get('email'):
                session['email'] = request.form.get('email')
            if request.form.get('first_name'):
                session['first_name'] = request.form.get('first_name')

        except Exception as e:
            db.session.rollback()
            flash('Error updating settings. Please try again.', 'error')
            print(f"Settings update error: {str(e)}")

    # Fetch user data from users table
    try:
        user = User.query.get(session['user_id'])
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'contact_number': user.contact_number,
            'address': user.address,
            'date_of_birth': user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else None,
            'gender': user.gender,
            'role': user.role,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        } if user else {}
    except Exception as e:
        user_data = {}
        print(f"Error fetching user data: {str(e)}")

    # Fetch total requests count
    try:
        total_requests_count = CertificateRequest.query.filter_by(user_id=session['user_id']).count()
    except Exception as e:
        print(f"Error fetching total requests count: {str(e)}")
        total_requests_count = 0

    # Fetch total complaints count
    try:
        total_complaints_count = Complaint.query.filter_by(user_id=session['user_id']).count()
    except Exception as e:
        print(f"Error fetching total complaints count: {str(e)}")
        total_complaints_count = 0

    # Fetch all certificate requests for the user
    try:
        certificate_requests = CertificateRequest.query.filter_by(user_id=session['user_id']).order_by(CertificateRequest.created_at.desc()).all()
        for req in certificate_requests:
            req.formatted_date = req.created_at.strftime('%B %d, %Y')
    except Exception as e:
        certificate_requests = []
        print(f"Error fetching certificate requests: {str(e)}")

    # Fetch all complaints for the user
    try:
        complaints = Complaint.query.filter_by(user_id=session['user_id']).order_by(Complaint.created_at.desc()).all()
        for comp in complaints:
            comp.formatted_date = comp.created_at.strftime('%B %d, %Y')
    except Exception as e:
        complaints = []
        print(f"Error fetching complaints: {str(e)}")

    return render_template('residents/settings.html',
                           user=user_data,
                           total_requests_count=total_requests_count,
                           total_complaints_count=total_complaints_count,
                           certificate_requests=certificate_requests,
                           complaints=complaints)

@app.route('/send-reset-code', methods=['POST'])
def send_reset_code():
    """Send reset code via AJAX for forgot password"""
    try:
        data = request.json
        email = data.get('email')

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'No account found with this email address'}), 404

        # Generate reset code
        reset_code = randint(100000, 999999)
        session['reset_code'] = reset_code
        session['reset_email'] = email

        # Send email
        email_sent = send_email(
            to=email,
            subject='Barangay Pulse – Password Reset Code',
            body=(
                "Magandang araw!\n\n"
                "Nakakuha kami ng kahilingan para sa pag-reset ng iyong password sa *Barangay Pulse*.\n\n"
                "Upang magpatuloy, mangyaring gamitin ang reset code na nasa ibaba:\n\n"
                f"Reset Code: {reset_code}\n\n"
                "Kung hindi ikaw ang nagsimula ng prosesong ito, maaari mong balewalain ang mensaheng ito.\n\n"
                "Lubos na gumagalang,\n"
                "Barangay Pulse Support Team"
            ),
            html=(
                "<div style='font-family: Arial, sans-serif; color: #333;'>"
                "<h2 style='color: #007b5e;'>Barangay Pulse – Password Reset</h2>"
                "<p>Magandang araw!</p>"
                "<p>Nakakuha kami ng kahilingan para sa pag-reset ng iyong password sa <strong>Barangay Pulse</strong>.</p>"
                "<p>Upang magpatuloy, mangyaring gamitin ang reset code na nasa ibaba:</p>"
                f"<p style='font-size: 22px; font-weight: bold; color: #007b5e;'>{reset_code}</p>"
                "<p>Kung hindi ikaw ang nagsimula ng prosesong ito, maaari mong balewalain ang mensaheng ito.</p>"
                "<br>"
                "<p>Lubos na gumagalang,<br><strong>Barangay Pulse Dev</strong></p>"
                "</div>"
            )
        )

        if email_sent:
            return jsonify({'success': True, 'message': 'Reset code sent successfully. Check your email.'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send reset code. Please try again.'}), 500

    except Exception as e:
        print(f"Error sending reset code: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using code"""
    try:
        data = request.json
        code = data.get('code')
        new_password = data.get('new_password')

        if not code or not new_password:
            return jsonify({'success': False, 'message': 'Code and new password are required'}), 400

        # Verify code
        stored_code = session.get('reset_code')
        stored_email = session.get('reset_email')

        if not stored_code or not stored_email or str(code) != str(stored_code):
            return jsonify({'success': False, 'message': 'Invalid or expired reset code'}), 400

        # Get user
        user = User.query.filter_by(email=stored_email).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Update password
        user.password = generate_password_hash(new_password)
        db.session.commit()

        # Clear session
        session.pop('reset_code', None)
        session.pop('reset_email', None)

        return jsonify({'success': True, 'message': 'Password reset successfully! You can now log in with your new password.'})

    except Exception as e:
        db.session.rollback()
        print(f"Error resetting password: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/forgot-password')
def forgot_password():
    """Forgot password page (legacy, can be removed if not needed)"""
    return render_template('residents/forgot_password.html')

# ============================================================================
# API ENDPOINTS FOR ADMIN
# ============================================================================

@app.route('/api/send-notification', methods=['POST'])
def send_notification():
    """API endpoint to send email notifications"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json
        result = send_email(
            to=data.get('email'),
            subject=data.get('subject'),
            body=data.get('body'),
            html=data.get('html')
        )

        if result:
            return jsonify({'success': True, 'message': 'Email sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send email'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity-history', methods=['GET'])
def get_activity_history():
    """API endpoint to get recent activities for Captain and Secretary"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from models import ActivityLog, User

        # Get recent activities (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Get Captain activities (assuming role='captain' or position='Captain')
        captain_activities = ActivityLog.query.join(User).filter(
            ActivityLog.created_at >= thirty_days_ago,
            db.or_(
                User.role == 'captain',
                User.role.ilike('%captain%')
            )
        ).order_by(ActivityLog.created_at.desc()).limit(10).all()

        # Get Secretary activities
        secretary_activities = ActivityLog.query.join(User).filter(
            ActivityLog.created_at >= thirty_days_ago,
            db.or_(
                User.role == 'secretary',
                User.role.ilike('%secretary%')
            )
        ).order_by(ActivityLog.created_at.desc()).limit(10).all()

        def format_activity(activity):
            return {
                'action': activity.action,
                'details': activity.details,
                'timestamp': activity.created_at.isoformat(),
                'admin_name': f"{activity.admin.first_name} {activity.admin.last_name}" if activity.admin else 'Unknown'
            }

        return jsonify({
            'captain_activities': [format_activity(activity) for activity in captain_activities],
            'secretary_activities': [format_activity(activity) for activity in secretary_activities]
        })

    except Exception as e:
        print(f"Error fetching activity history: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch activity history'}), 500

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)