import re
from datetime import datetime, timezone

from flask import (Flask, flash, redirect, render_template, request, url_for)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

from models import URL, db


# --------------------------
# Base62 encoding utilities
# --------------------------
BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def base62_encode(num: int) -> str:
    """Encode a positive integer into Base62."""
    if num < 0:
        raise ValueError("Base62 encoding only supports non-negative integers")
    if num == 0:
        return BASE62_ALPHABET[0]

    encoded = []
    while num > 0:
        num, rem = divmod(num, 62)
        encoded.append(BASE62_ALPHABET[rem])
    return "".join(reversed(encoded))


def normalize_url(url: str) -> str:
    """Ensure the URL has a valid HTTP/HTTPS scheme."""
    url = url.strip()
    if not url:
        return ""

    # If a scheme is provided, only allow http/https.
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url):
        if not re.match(r"^https?://", url, re.IGNORECASE):
            return ""
        return url

    # Add http by default when scheme is missing.
    return "http://" + url


# --------------------------
# Validation helpers
# --------------------------

RESERVED_PATHS = {"stats", "static", "favicon.ico"}
ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{3,64}$")


def is_valid_alias(alias: str) -> bool:
    return bool(ALIAS_RE.fullmatch(alias))


def is_reserved_alias(alias: str) -> bool:
    return alias.lower() in RESERVED_PATHS


# --------------------------
# Flask application factory
# --------------------------

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shortener.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "change-me-to-a-secure-random-value"

    db.init_app(app)

# This creates the database tables automatically within the app context
    with app.app_context():
        db.create_all()
        # Add is_active column if it doesn't exist for older databases
        try:
            db.session.execute(db.text("ALTER TABLE urls ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    @app.route("/", methods=["GET", "POST"])
    def index():
        short_url = None
        if request.method == "POST":
            original_url = normalize_url(request.form.get("original_url", ""))
            custom_alias = request.form.get("custom_alias", "").strip() or None

            if not original_url:
                flash("Please enter a valid URL.", "error")
                return render_template("index.html", short_url=short_url)

            if custom_alias:
                if not is_valid_alias(custom_alias):
                    flash(
                        "Custom alias must be 3-64 characters and may only contain letters, numbers, '-' and '_'.",
                        "error",
                    )
                    return render_template("index.html", short_url=short_url)

                if is_reserved_alias(custom_alias):
                    flash(
                        "That alias is reserved. Please choose a different alias.",
                        "error",
                    )
                    return render_template("index.html", short_url=short_url)

                existing_alias = URL.query.filter_by(custom_alias=custom_alias).first()
                if existing_alias:
                    flash(
                        f"The custom alias '{custom_alias}' is already taken. Please choose another.",
                        "error",
                    )
                    return render_template("index.html", short_url=short_url)

                # Prevent collisions with generated Base62 codes
                existing_code = URL.query.filter_by(short_code=custom_alias).first()
                if existing_code:
                    flash(
                        "That alias conflicts with an automatically generated code. Please choose a different alias.",
                        "error",
                    )
                    return render_template("index.html", short_url=short_url)

            # Create record to obtain an ID for Base62 encoding
            url_obj = URL(original_url=original_url, custom_alias=custom_alias)
            db.session.add(url_obj)
            db.session.flush()  # populate url_obj.id without committing

            # Generate short code from the DB id.
            url_obj.short_code = base62_encode(url_obj.id)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(
                    "Unable to create the short URL right now. Please try again.",
                    "error",
                )
                return render_template("index.html", short_url=short_url)

            # Choose the canonical identifier (custom alias wins)
            short_key = custom_alias or url_obj.short_code
            short_url = url_for("redirect_short", code=short_key, _external=True)
            flash("Short URL created!", "success")

        return render_template("index.html", short_url=short_url)

    @app.route("/stats")
    def stats():
        urls = URL.query.order_by(URL.created_at.desc()).all()
        total_clicks = sum(url.clicks for url in urls)
        total_links = len(urls)
        most_active_link = max(urls, key=lambda u: u.clicks) if urls else None
        
        return render_template(
            "stats.html", 
            urls=urls, 
            total_clicks=total_clicks,
            total_links=total_links,
            most_active=most_active_link
        )

    @app.route("/toggle/<int:id>", methods=["POST"])
    def toggle_status(id):
        url_obj = URL.query.get_or_404(id)
        url_obj.is_active = not url_obj.is_active
        db.session.commit()
        
        status_text = "enabled" if url_obj.is_active else "disabled"
        flash(f"Link {status_text} successfully.", "success")
        return redirect(url_for("stats"))

    @app.route("/<path:code>")
    def redirect_short(code: str):
        # Prefer custom alias matches first to avoid ambiguity with auto-generated codes
        url_obj = URL.query.filter_by(custom_alias=code).first()
        if not url_obj:
            url_obj = URL.query.filter_by(short_code=code).first()

        if not url_obj:
            return render_template("404.html"), 404

        if not getattr(url_obj, 'is_active', True):
            return render_template("deactivated.html"), 403

        url_obj.clicks += 1
        url_obj.last_click_at = datetime.now(timezone.utc)
        db.session.commit()
        return redirect(url_obj.original_url, code=302)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
