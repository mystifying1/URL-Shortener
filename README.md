# URL Shortener (Flask)

A simple URL shortener built with **Flask**, **SQLite**, and **Base62 encoding**.

## 🚀 Features

- Short URLs generated from database IDs using **Base62 (0-9, a-z, A-Z)**
- ✅ Custom aliases (unique back-half) support (only letters, numbers, '-' and '_', 3-64 chars)
- ✅ Click tracking (increments on every redirect)
- ✅ Analytics dashboard with total clicks and list of links
- ✅ 302 redirects (for tracking)

---

## 🧰 Setup (Windows)

### 1) Create and activate a virtual environment

```powershell
cd "e:\URL shortner"
python -m venv venv
venv\Scripts\activate
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Initialize the database

The database is auto-created the first time you run the app.

If you want to force a fresh database, you can delete `shortener.db` and restart the app.

---

## ▶️ Run the app

```powershell
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

---

## 🧩 Project Structure

- `app.py` — Main Flask application; routing and Base62 logic
- `models.py` — SQLAlchemy model + database configuration
- `templates/` — Jinja2 templates (`index.html`, `stats.html`, `404.html`)
- `static/style.css` — Modern UI styling
- `shortener.db` — Generated SQLite database file

---

## 🛠 How it works

1. Submitting a URL creates a database row.
2. The row ID is encoded with Base62 to form a short code.
3. If a custom alias is provided, it will be used instead.
4. Visiting `/yourcode` performs a 302 redirect and increments click count.

---

## 📌 Notes / Next steps

- You can change `app.config['SECRET_KEY']` in `app.py` to a secure random value for production.
- Consider adding rate limiting / abuse protection for public deployments.
