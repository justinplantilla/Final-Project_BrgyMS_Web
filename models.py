from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    full_name = db.Column(db.String(100))
    contact_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    role = db.Column(db.String(20), default='resident')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    certificate_requests = db.relationship('CertificateRequest', backref='user', lazy=True)
    complaints = db.relationship('Complaint', backref='user', lazy=True)

class Resident(db.Model):
    __tablename__ = 'residents'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resident_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    middle_initial = db.Column(db.String(10), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=False)
    purok = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    civil_status = db.Column(db.String(50), nullable=False)
    occupation = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Normal')
    image_url = db.Column(db.Text)
    posted_by = db.Column(db.String(100), default='Admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CertificateRequest(db.Model):
    __tablename__ = 'certificate_requests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    certificate_type = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    valid_id_file_url = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'processing', 'approved', 'ready for pickup', 'declined'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    incident_type = db.Column(db.String(100), nullable=False)
    incident_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    persons_involved = db.Column(db.Text)
    evidence_url = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'under investigation', 'resolved', 'dismissed'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BarangayOfficial(db.Model):
    __tablename__ = 'barangay_officials'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20))
    term_start = db.Column(db.Date)
    term_end = db.Column(db.Date)
    photo_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)  # e.g., "Added resident", "Updated complaint status"
    details = db.Column(db.Text)  # Additional details about the action
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to User (admin)
    admin = db.relationship('User', backref='activity_logs', lazy=True)

# Alias for backward compatibility
Official = BarangayOfficial
