#!/usr/bin/env python3
"""
Dashboard Web per Newsletter Marketing System
Piattaforma privata per gestire campagne, caricare CSV e creare contenuti
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import secrets
from datetime import datetime
from functools import wraps
import csv
import io

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Cambia in produzione

# Configurazioni
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'txt'}
DB_PATH = 'newsletter.db'

# Credenziali admin (in produzione usa database o environment variables)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('changeme123')  # CAMBIA QUESTA PASSWORD!

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Crea cartella uploads se non esiste
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ROUTES

@app.route('/')
@login_required
def dashboard():
    """Dashboard principale"""
    conn = get_db()
    
    # Statistiche rapide
    total_subscribers = conn.execute('SELECT COUNT(*) as count FROM subscribers WHERE status="subscribed"').fetchone()['count']
    total_campaigns = conn.execute('SELECT COUNT(*) as count FROM campaigns').fetchone()['count']
    recent_campaigns = conn.execute('SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 5').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_subscribers=total_subscribers,
                         total_campaigns=total_campaigns,
                         recent_campaigns=recent_campaigns)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            session['username'] = username
            flash('Login effettuato con successo!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenziali non valide', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout effettuato', 'info')
    return redirect(url_for('login'))

@app.route('/upload-csv', methods=['GET', 'POST'])
@login_required
def upload_csv():
    """Upload CSV contatti"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nessun file selezionato', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Nessun file selezionato', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Importa contatti dal CSV
            try:
                imported, duplicates, skipped = import_contacts_from_csv(filepath)
                flash(f'Importazione completata! Importati: {imported}, Duplicati: {duplicates}, Saltati: {skipped}', 'success')
            except Exception as e:
                flash(f'Errore importazione: {str(e)}', 'error')
            
            return redirect(url_for('subscribers'))
    
    return render_template('upload_csv.html')

def import_contacts_from_csv(filepath):
    """Importa contatti da file CSV"""
    conn = get_db()
    cursor = conn.cursor()
    
    imported = 0
    duplicates = 0
    skipped = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        # Rileva delimitatore
        sample = f.read(1024)
        f.seek(0)
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter
        
        reader = csv.DictReader(f, delimiter=delimiter)
        
        # Trova colonna email
        email_column = None
        for field in reader.fieldnames:
            if 'email' in field.lower():
                email_column = field
                break
        
        if not email_column:
            raise ValueError('Nessuna colonna email trovata nel CSV')
        
        for row in reader:
            email = row.get(email_column, '').strip()
            
            if not email:
                skipped += 1
                continue
            
            # Controlla duplicati
            existing = cursor.execute('SELECT id FROM subscribers WHERE email = ?', (email,)).fetchone()
            if existing:
                duplicates += 1
                continue
            
            # Genera token unsubscribe
            token = secrets.token_hex(32)
            cursor.execute('''INSERT INTO campaigns (name, subject, from_name, from_email, status, created_at)
            VALUES (?, ?, ?, ?, "draft", ?)''',
            (name, subject, from_name, from_email, datetime.now().isoformat()))
            imported += 1
    
    conn.commit()
    conn.close()
    
    return imported, duplicates, skipped

@app.route('/subscribers')
@login_required
def subscribers():
    """Lista contatti"""
    conn = get_db()
    subscribers = conn.execute('SELECT * FROM subscribers ORDER BY subscribed_at DESC LIMIT 100').fetchall()
    conn.close()
    
    return render_template('subscribers.html', subscribers=subscribers)

@app.route('/campaigns')
@login_required
def campaigns():
    """Lista campagne"""
    conn = get_db()
    campaigns = conn.execute('SELECT * FROM campaigns ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('campaigns.html', campaigns=campaigns)

@app.route('/campaigns/new', methods=['GET', 'POST'])
@login_required
def new_campaign():
    """Crea nuova campagna"""
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        from_name = request.form.get('from_name')
        from_email = request.form.get('from_email')
        content = request.form.get('content')
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''INSERT INTO campaigns (name, subject, from_name, from_email, content, status, created_at)
                       VALUES (?, ?, ?, ?, ?, "draft", ?)''',
                    (name, subject, from_name, from_email, content, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        flash('Campagna creata con successo!', 'success')
        return redirect(url_for('campaigns'))
    
    return render_template('create_campaign.html')
@app.route('/campaigns/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    """Modifica campagna"""
    conn = get_db()
    
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        from_name = request.form.get('from_name')
        from_email = request.form.get('from_email')
       
        
        conn.execute('''UPDATE campaigns SET name=?, subject=?, from_name=?, from_email=?, content=?
                     WHERE id=?''',
                  (name, subject, from_name, from_email, content, campaign_id))
        conn.commit()
        flash('Campagna aggiornata!', 'success')
        return redirect(url_for('campaigns'))
    
    campaign = conn.execute('SELECT * FROM campaigns WHERE id=?', (campaign_id,)).fetchone()
    conn.close()
    
    return render_template('edit_campaign.html', campaign=campaign)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
