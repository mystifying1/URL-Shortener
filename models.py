from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class URL(db.Model):
    __tablename__ = "urls"

    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False)
    short_code = db.Column(db.String(64), nullable=True, unique=True)
    custom_alias = db.Column(db.String(128), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_click_at = db.Column(db.DateTime, nullable=True)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<URL id={self.id} short_code={self.short_code} custom_alias={self.custom_alias}>"
