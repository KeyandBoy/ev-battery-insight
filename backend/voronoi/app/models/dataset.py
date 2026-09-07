from datetime import datetime, timezone

from ..extensions import db


def _utcnow():
    return datetime.now(timezone.utc)


class Dataset(db.Model):
    __tablename__ = 'datasets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    filename = db.Column(db.String(256), nullable=False)
    original_filename = db.Column(db.String(256), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    node_count = db.Column(db.Integer, default=0)
    max_depth = db.Column(db.Integer, default=0)
    leaf_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_display': self._format_file_size(),
            'node_count': self.node_count,
            'max_depth': self.max_depth,
            'leaf_count': self.leaf_count,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_display': self._format_file_size(),
            'node_count': self.node_count,
            'max_depth': self.max_depth,
            'leaf_count': self.leaf_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def _format_file_size(self):
        size = self.file_size
        if size < 1024:
            return f'{size} B'
        for unit in ['KB', 'MB', 'GB']:
            size /= 1024
            if size < 1024:
                return f'{size:.1f} {unit}'
        return f'{size:.1f} TB'

    def __repr__(self):
        return f'<Dataset {self.name}>'
