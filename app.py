#!/usr/bin/env python3
"""
Dashboard Web per Newsletter Marketing System
Piattaforma privata per gestire contatti e campagne.
Compatibile con Render (PORT env), inizializzazione DB automatica.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import secrets
from datetime import datetime
from functools import wraps
import csv

# =========================
# CONFIG
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
ALLOWED_EXTENSIONS = {"csv", "txt"}

# Su Render (con Disk montato su /var/data): DB_PATH=/var/data/newsletter.db
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "newsletter.db")
DB_PATH = os.environ.get("DB_PATH", DEFAULT_DB_PATH)

# Sicurezza sessioni: NON rigenerare a ogni avvio in produzione
SECRET_KEY = os.environ.get("SECRET_KEY", None)
if not SECRET_KEY:
    # fallback locale (ok per dev); su Render impostalo in Env
    SECRET_KEY = secrets.token_hex(32)

# Credenziali admin da env (consigliato)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
# Opzione 1: password in chiaro da env (Render) → hashata al boot
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# =========================
# APP
# =========================

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# Se usi /var/data su Render, crea la cartella
db_dir = os.path.dirname(DB_PATH)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)


# =========================
# DB HELPERS
# =========================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db_if_needed():
    """
    Crea le tabelle se mancano, leggendo database_schema.sql.
    Evita l'errore: sqlite3.OperationalError: no such table: subscribers
    """
    conn = get_db()
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='subscribers'"
        )
        exists = cur.fetchone() is not None
        if not exists:
            schema_path = os.path.join(BASE_DIR, "database_schema.sql")
            if not os.path.exists(schema_path):
                raise RuntimeError(
                    "database_schema.sql non trovato nella root del progetto."
                )
            with open(schema_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()
    finally:
        conn.close()


# inizializza DB all'avvio
init_db_if_needed()


# =========================
# UTILS
# =========================

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# =========================
# ROUTES
# =========================

@app.route("/")
@login_required
def dashboard():
    """Dashboard principale"""
    conn = get_db()

    # Statistiche rapide (con fallback a 0 se query fallisce)
    total_subscribers = conn.execute(
        'SELECT COUNT(*) as count FROM subscribers WHERE status="subscribed"'
    ).fetchone()["count"]

    total_campaigns = conn.execute(
        "SELECT COUNT(*) as count FROM campaigns"
    ).fetchone()["count"]

    recent_campaigns = conn.execute(
        "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_subscribers=total_subscribers,
        total_campaigns=total_campaigns,
        recent_campaigns=recent_campaigns,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["logged_in"] = True
            session["username"] = username
            flash("Login effettuato con successo!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenziali non valide", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logout effettuato", "info")
    return redirect(url_for("login"))


@app.route("/upload-csv", methods=["GET", "POST"])
@login_required
def upload_csv():
    """Upload CSV contatti"""
    if request.method == "POST":
        if "file" not in request.files:
            flash("Nessun file selezionato", "error")
            return redirect(request.url)

        file = request.files["file"]

        if not file or file.filename == "":
            flash("Nessun file selezionato", "error")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            try:
                imported, duplicates, skipped = import_contacts_from_csv(filepath)
                flash(
                    f"Importazione completata! Importati: {imported}, Duplicati: {duplicates}, Saltati: {skipped}",
                    "success",
                )
            except Exception as e:
                flash(f"Errore importazione: {str(e)}", "error")

            return redirect(url_for("subscribers"))

        flash("Formato file non supportato. Usa CSV o TXT.", "error")
        return redirect(request.url)

    return render_template("upload_csv.html")


def import_contacts_from_csv(filepath: str):
    """
    Importa contatti da file CSV nella tabella subscribers.
    Si aspetta una colonna 'email' (case-insensitive) e opzionalmente 'name' o 'nome'.
    """
    conn = get_db()
    cursor = conn.cursor()

    imported = 0
    duplicates = 0
    skipped = 0

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        sample = f.read(2048)
        f.seek(0)

        # prova sniff delimitatore; fallback a comma
        delimiter = ","
        try:
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
        except Exception:
            delimiter = ","

        reader = csv.DictReader(f, delimiter=delimiter)

        if not reader.fieldnames:
            raise ValueError("CSV vuoto o senza intestazioni (header).")

        # Trova colonna email e nome
        email_column = None
        name_column = None
        for field in reader.fieldnames:
            low = field.lower().strip()
            if email_column is None and "email" in low:
                email_column = field
            if name_column is None and (low in {"name", "nome", "full_name", "fullname"}):
                name_column = field

        if not email_column:
            raise ValueError("Nessuna colonna email trovata nel CSV (es. 'email').")

        for row in reader:
            email = (row.get(email_column) or "").strip().lower()
            name = (row.get(name_column) or "").strip() if name_column else ""

            if not email:
                skipped += 1
                continue

            existing = cursor.execute(
                "SELECT id FROM subscribers WHERE email = ?",
                (email,),
            ).fetchone()

            if existing:
                duplicates += 1
                continue

            token = secrets.token_hex(32)
            now_iso = datetime.utcnow().isoformat()

            # Inserimento robusto: prova prima con colonne comuni.
            # Se il tuo schema usa colonne diverse, dimmelo e lo adatto.
            try:
                cursor.execute(
                    """
                    INSERT INTO subscribers (email, name, status, unsubscribe_token, subscribed_at)
                    VALUES (?, ?, "subscribed", ?, ?)
                    """,
                    (email, name, token, now_iso),
                )
            except sqlite3.OperationalError:
                # fallback minimale se alcune colonne non esistono
                cursor.execute(
                    """
                    INSERT INTO subscribers (email, status)
                    VALUES (?, "subscribed")
                    """,
                    (email,),
                )

            imported += 1

    conn.commit()
    conn.close()
    return imported, duplicates, skipped


@app.route("/subscribers")
@login_required
def subscribers():
    """Lista contatti"""
    conn = get_db()
    subs = conn.execute(
        "SELECT * FROM subscribers ORDER BY subscribed_at DESC LIMIT 200"
    ).fetchall()
    conn.close()

    return render_template("subscribers.html", subscribers=subs)


@app.route("/campaigns")
@login_required
def campaigns():
    """Lista campagne"""
    conn = get_db()
    camps = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
    conn.close()

    return render_template("campaigns.html", campaigns=camps)


@app.route("/campaigns/new", methods=["GET", "POST"])
@login_required
def new_campaign():
    """Crea nuova campagna"""
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        from_name = (request.form.get("from_name") or "").strip()
        from_email = (request.form.get("from_email") or "").strip()
        content = (request.form.get("content") or "").strip()

        if not name or not subject or not from_email:
            flash("Compila almeno: nome campagna, oggetto, email mittente.", "error")
            return redirect(request.url)

        conn = get_db()
        conn.execute(
            """
            INSERT INTO campaigns (name, subject, from_name, from_email, content, status, created_at)
            VALUES (?, ?, ?, ?, ?, "draft", ?)
            """,
            (name, subject, from_name, from_email, content, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

        flash("Campagna creata con successo!", "success")
        return redirect(url_for("campaigns"))

    return render_template("create_campaign.html")


@app.route("/campaigns/<int:campaign_id>/edit", methods=["GET", "POST"])
@login_required
def edit_campaign(campaign_id):
    """Modifica campagna"""
    conn = get_db()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        from_name = (request.form.get("from_name") or "").strip()
        from_email = (request.form.get("from_email") or "").strip()
        content = (request.form.get("content") or "").strip()

        if not name or not subject or not from_email:
            flash("Compila almeno: nome campagna, oggetto, email mittente.", "error")
            return redirect(request.url)

        conn.execute(
            """
            UPDATE campaigns
               SET name=?, subject=?, from_name=?, from_email=?, content=?
             WHERE id=?
            """,
            (name, subject, from_name, from_email, content, campaign_id),
        )
        conn.commit()
        conn.close()

        flash("Campagna aggiornata!", "success")
        return redirect(url_for("campaigns"))

    campaign = conn.execute(
        "SELECT * FROM campaigns WHERE id=?",
        (campaign_id,),
    ).fetchone()
    conn.close()

    if not campaign:
        flash("Campagna non trovata.", "error")
        return redirect(url_for("campaigns"))

    return render_template("edit_campaign.html", campaign=campaign)


# =========================
# MAIN (local dev)
# =========================

if __name__ == "__main__":
    # In produzione (Render) avvia gunicorn con $PORT
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=True, host="0.0.0.0", port=port)
