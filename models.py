# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# This is what server.py imports
db = SQLAlchemy()

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Which page/event this comment belongs to
    thread = db.Column(db.String(120), index=True, nullable=False)

    # For replies (null for root comments)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    # Optional relationship to access children if needed
    children = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        lazy='joined'
    )

    name = db.Column(db.String(80), nullable=False)
    social_url = db.Column(db.String(255), nullable=True)
    text = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, nullable=False, default=True)
