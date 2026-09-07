from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import db


def _utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(256), default='')
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )

    datasets = db.relationship(
        'Dataset', backref='owner', lazy='dynamic', cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'dataset_count': self.datasets.count(),
        }

    def __repr__(self):
        return f'<User {self.username}>'
