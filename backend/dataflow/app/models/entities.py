from app.extensions import db


ID_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class TimestampMixin:
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )


class User(TimestampMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(ID_TYPE, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    status = db.Column(db.SmallInteger, nullable=False, server_default="1")

    datasets = db.relationship("Dataset", back_populates="user", cascade="all, delete")
    dashboards = db.relationship("Dashboard", back_populates="user", cascade="all, delete")
    profile = db.relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        profile = self.profile
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": profile.display_name if profile and profile.display_name else self.username,
            "avatar_url": profile.avatar_url if profile else None,
            "bio": profile.bio if profile else None,
            "status": int(self.status or 0),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserProfile(TimestampMixin, db.Model):
    __tablename__ = "user_profile"

    user_id = db.Column(
        ID_TYPE,
        db.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    display_name = db.Column(db.String(50), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", back_populates="profile")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Dataset(TimestampMixin, db.Model):
    __tablename__ = "dataset"

    id = db.Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = db.Column(
        ID_TYPE,
        db.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    name = db.Column(db.String(100), nullable=False)
    source_type = db.Column(db.Enum("csv", "excel", "json", name="dataset_source_type"), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    field_meta = db.Column(db.JSON, nullable=True)
    total_rows = db.Column(db.Integer, nullable=False, server_default="0")
    clean_status = db.Column(
        db.Enum("pending", "done", "failed", name="dataset_clean_status"),
        nullable=False,
        server_default="pending",
        index=True,
    )

    user = db.relationship("User", back_populates="datasets")
    records = db.relationship("DataRecord", back_populates="dataset", cascade="all, delete")
    components = db.relationship("Component", back_populates="dataset")

    __table_args__ = (
        db.UniqueConstraint("user_id", "name", name="uk_dataset_user_name"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "source_type": self.source_type,
            "file_path": self.file_path,
            "field_meta": self.field_meta,
            "total_rows": int(self.total_rows or 0),
            "clean_status": self.clean_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DataRecord(db.Model):
    __tablename__ = "data_record"

    id = db.Column(ID_TYPE, primary_key=True, autoincrement=True)
    dataset_id = db.Column(
        ID_TYPE,
        db.ForeignKey("dataset.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id = db.Column(
        ID_TYPE,
        db.ForeignKey("data_record.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    node_key = db.Column(db.String(120), nullable=False, index=True)
    node_name = db.Column(db.String(120), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    value_num = db.Column(db.Numeric(18, 4), nullable=False, server_default="0")
    raw_payload = db.Column(db.JSON, nullable=True)
    is_abnormal = db.Column(db.SmallInteger, nullable=False, server_default="0")
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    dataset = db.relationship("Dataset", back_populates="records")
    parent = db.relationship("DataRecord", remote_side=[id], uselist=False)

    __table_args__ = (
        db.Index("idx_data_record_dataset_level", "dataset_id", "level"),
        db.Index("idx_data_record_dataset_parent", "dataset_id", "parent_id"),
    )


class Dashboard(TimestampMixin, db.Model):
    __tablename__ = "dashboard"

    id = db.Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = db.Column(
        ID_TYPE,
        db.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    canvas_width = db.Column(db.Integer, nullable=False, server_default="1920")
    canvas_height = db.Column(db.Integer, nullable=False, server_default="1080")
    theme = db.Column(db.String(50), nullable=False, server_default="light")
    layout_json = db.Column(db.JSON, nullable=True)
    is_published = db.Column(db.SmallInteger, nullable=False, server_default="0", index=True)

    user = db.relationship("User", back_populates="dashboards")
    components = db.relationship("Component", back_populates="dashboard", cascade="all, delete")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "canvas_width": int(self.canvas_width or 0),
            "canvas_height": int(self.canvas_height or 0),
            "theme": self.theme,
            "layout_json": self.layout_json,
            "is_published": int(self.is_published or 0),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Component(TimestampMixin, db.Model):
    __tablename__ = "component"

    id = db.Column(ID_TYPE, primary_key=True, autoincrement=True)
    dashboard_id = db.Column(
        ID_TYPE,
        db.ForeignKey("dashboard.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_id = db.Column(
        ID_TYPE,
        db.ForeignKey("dataset.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    type = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=True)
    x = db.Column(db.Integer, nullable=False, server_default="0")
    y = db.Column(db.Integer, nullable=False, server_default="0")
    w = db.Column(db.Integer, nullable=False, server_default="400")
    h = db.Column(db.Integer, nullable=False, server_default="300")
    z_index = db.Column(db.Integer, nullable=False, server_default="1")
    config_json = db.Column(db.JSON, nullable=True)
    binding_json = db.Column(db.JSON, nullable=True)

    dashboard = db.relationship("Dashboard", back_populates="components")
    dataset = db.relationship("Dataset", back_populates="components")

    def to_dict(self):
        return {
            "id": self.id,
            "dashboard_id": self.dashboard_id,
            "dataset_id": self.dataset_id,
            "type": self.type,
            "title": self.title,
            "x": int(self.x or 0),
            "y": int(self.y or 0),
            "w": int(self.w or 0),
            "h": int(self.h or 0),
            "z_index": int(self.z_index or 0),
            "config_json": self.config_json,
            "binding_json": self.binding_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
