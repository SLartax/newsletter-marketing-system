#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Newsletter Marketing System - Flask Web Application
Sistema completo per gestione newsletter con database SQLite.
"""

import csv
import os
import secrets
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from werkzeug.utils import secure_filename

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# ===== CONFIGURAZIONE =====
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "newsletter.db")
DB_PATH = os.environ.get("DB_PATH", DEFAULT_DB_PATH)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {".csv", ".txt"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Credenziali admin (da variabili d'ambiente)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password123")

# Configurazione SMTP
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "Newsletter System")


# ===== FUNZIONI HELPER =====
def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            flash("Devi effettuare il login.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def sniff_delimiter(sample):
    try:
        return csv.Sniffer().sniff(sample).delimiter
    except Exception:
        if "\t" in sample:
            return "\t"
        if ";" in sample:
            return ";"
        return ","


def detect_columns(fieldnames):
    email_col = None
    name_col = None
    for field in fieldnames:
        low = field.lower().strip()
        if email_col is None and ("email" in low or "mail" in low):
            email_col = field
        if name_col is None and low in {"name", "nome", "full_name", "fullname"}:
            name_col = field
    return email_col, name_col


def import_contacts_from_csv(filepath):
    conn = get_db()
    cur = conn.cursor()
    imported = 0
    duplicates = 0
    skipped = 0

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(2048)
        f.seek(0)
        delimiter = sniff_delimiter(sample)
        reader = csv.DictReader(f, delimiter=delimiter)

        if not reader.fieldnames:
            raise ValueError("CSV vuoto o senza intestazioni.")

        email_col, name_col = detect_columns(reader.fieldnames)
        if not email_col:
            raise ValueError("Colonna email non trovata.")

        for row in reader:
            email = (row.get(email_col) or "").strip().lower()
            if not email:
                skipped += 1
                continue

            name = (row.get(name_col) or "").strip() if name_col else ""

            existing = cur.execute(
                "SELECT id FROM subscribers WHERE email = ?", (email,)
            ).fetchone()

            if existing:
                duplicates += 1
                continue

            token = secrets.token_hex(32)
            now_iso = utc_now_iso()

            try:
                cur.execute(
                    """INSERT INTO subscribers
                       (email, name, status, unsubscribe_token, subscribed_at)
                       VALUES (?, ?, 'subscribed', ?, ?)""",
                    (email, name, token, now_iso),
                )
            except sqlite3.OperationalError:
                cur.execute(
                    'INSERT INTO subscribers (email, status) VALUES (?, "subscribed")',
                    (email,),
                )

            imported += 1

    conn.commit()
    conn.close()
    return imported, duplicates, skipped


def send_email(to_email, subject, html_body, text_body=""):
    """Invia una singola email tramite SMTP."""
    app.logger.info(f"🔧 SMTP Config: server={SMTP_SERVER}, port={SMTP_PORT}, user={SMTP_USERNAME}, from={SMTP_FROM_EMAIL}")
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise ValueError(f"Configurazione SMTP mancante: USER={SMTP_USERNAME}, PASS={'***' if SMTP_PASSWORD else 'EMPTY'}")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = to_email

    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


# ===== ROUTE =====
@app.route("/")
def index():
    if "logged_in" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            flash("Login effettuato con successo!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenziali non valide.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logout effettuato.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    total_subscribers = cur.execute(
        "SELECT COUNT(*) as count FROM subscribers WHERE status='subscribed'"
    ).fetchone()["count"]

    total_campaigns = cur.execute("SELECT COUNT(*) as count FROM campaigns").fetchone()[
        "count"
    ]

    conn.close()

    return render_template(
        "dashboard.html",
        total_subscribers=total_subscribers,
        total_campaigns=total_campaigns,
    )


@app.route("/campaigns")
@login_required
def campaigns():
    conn = get_db()
    cur = conn.cursor()

    campaigns_list = cur.execute(
        "SELECT * FROM campaigns ORDER BY created_at DESC"
    ).fetchall()

    conn.close()
    return render_template("campaigns.html", campaigns=campaigns_list)


@app.route("/campaigns/new", methods=["GET", "POST"])
@login_required
def new_campaign():
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()
        csv_file = request.files.get("csv_file")

        if not subject or not body:
            flash("Oggetto e corpo email sono obbligatori.", "error")
            return redirect(url_for("new_campaign"))

        if not csv_file or csv_file.filename == "":
            flash("Devi caricare un file CSV con i destinatari.", "error")
            return redirect(url_for("new_campaign"))

        if not allowed_file(csv_file.filename):
            flash("Formato file non supportato. Usa .csv o .txt", "error")
            return redirect(url_for("new_campaign"))

        filename = secure_filename(csv_file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        csv_file.save(filepath)

        try:
            imported, duplicates, skipped = import_contacts_from_csv(filepath)
            
            conn = get_db()
            cur = conn.cursor()
            recipients = cur.execute(
                "SELECT email, name FROM subscribers WHERE status='subscribed'"
            ).fetchall()
        except Exception as e:
            flash(f"Errore durante l'import: {str(e)}", "error")
            return redirect(url_for("new_campaign"))
        
        app.logger.info(f"📊 CSV Import: {imported} importati, {duplicates} duplicati, {skipped} saltati")
        flash(f"CSV Import: {imported} contatti importati, {duplicates} duplicati, {skipped} saltati", "info")
        
        if imported == 0:
            flash(f"⚠️ NESSUN CONTATTO IMPORTATO! Verifica il formato del CSV.", "error")
            app.logger.error(f"Zero contacts imported from {filepath}")
        
        sent_count = 0
        error_count = 0

        for recipient in recipients:
            email = recipient["email"]
            name = recipient["name"] or "Cliente"
            personalized_body = body.replace("{nome}", name).replace("{email}", email)

            try:
                send_email(email, subject, personalized_body)
                sent_count += 1
            except Exception as e:
                error_msg = f"Errore invio a {email}: {type(e).__name__}: {str(e)}"
                app.logger.error(error_msg)
                flash(error_msg, "error")
                error_count += 1

        conn.close()
        os.remove(filepath)

        flash(
            f"Campagna inviata! Email inviate: {sent_count}, Errori: {error_count}",
            "success",
        )
        return redirect(url_for("campaigns"))
        
    except Exception as e:
        error_msg = f"Errore durante l'invio della campagna: {type(e).__name__}: {str(e)}"
        app.logger.error(error_msg)
        app.logger.error(f"Traceback completo:", exc_info=True)
        flash(error_msg, "error")
        if os.path.exists(filepath):
            os.remove(filepath)
        return redirect(url_for("new_campaign"))

    return render_template("new_campaign.html")


@app.route("/subscribers")
@login_required
def subscribers():
    conn = get_db()
    cur = conn.cursor()

    subscribers_list = cur.execute(
        "SELECT * FROM subscribers ORDER BY subscribed_at DESC"
    ).fetchall()

    conn.close()
    return render_template("subscribers.html", subscribers=subscribers_list)


@app.route("/unsubscribe")
def unsubscribe():
    token = request.args.get("token", "")
    if not token:
        return "Token mancante", 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE subscribers SET status='unsubscribed', unsubscribed_at=? WHERE unsubscribe_token=?",
        (utc_now_iso(), token),
    )

    if cur.rowcount > 0:
        conn.commit()
        conn.close()
        return render_template("unsubscribe_success.html")
    else:
        conn.close()
        return "Token non valido", 404


# Initialize database on startup
try:
    from init_db import init_database
    init_database()
except Exception as e:
    print(f"Database initialization: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
