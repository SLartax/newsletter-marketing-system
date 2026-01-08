#!/usr/bin/env python3
"""
Script per importare contatti da CSV Mailchimp nel database newsletter.
Estrae SOLO gli indirizzi email validi e genera token unsubscribe univoci.

Uso:
    python import_contacts.py contatti_mailchimp_con_nome.csv
"""

import csv
import sqlite3
import secrets
import re
import sys
from datetime import datetime

def is_valid_email(email):
    """Valida formato email con regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_unsubscribe_token():
    """Genera token sicuro per unsubscribe (32 bytes hex)"""
    return secrets.token_hex(32)

def import_contacts(csv_file, db_path='newsletter.db'):
    """Importa contatti dal CSV nel database"""
    
    # Connessione al database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    imported = 0
    skipped = 0
    duplicates = 0
    
    print(f"Apertura file CSV: {csv_file}")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        # Rileva automaticamente il delimitatore
        sample = f.read(1024)
        f.seek(0)
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter
        
        reader = csv.DictReader(f, delimiter=delimiter)
        
        print(f"Colonne rilevate: {reader.fieldnames}")
        
        # Trova colonna email (case-insensitive)
        email_column = None
        for field in reader.fieldnames:
            if 'email' in field.lower():
                email_column = field
                break
        
        if not email_column:
            print("ERRORE: Nessuna colonna email trovata nel CSV")
            return
        
        print(f"Colonna email: {email_column}")
        print("\nInizio importazione...\n")
        
        for row in reader:
            email = row.get(email_column, '').strip()
            
            # Salta righe vuote
            if not email:
                skipped += 1
                continue
            
            # Valida email
            if not is_valid_email(email):
                print(f"⚠️  Email non valida: {email}")
                skipped += 1
                continue
            
            # Controlla se esiste già
            cursor.execute('SELECT id FROM subscribers WHERE email = ?', (email,))
            if cursor.fetchone():
                print(f"⚠️  Duplicato: {email}")
                duplicates += 1
                continue
            
            # Genera token unsubscribe
            token = generate_unsubscribe_token()
            
            # Inserisci nel database
            try:
                cursor.execute('''
                    INSERT INTO subscribers (email, unsubscribe_token, subscribed_at)
                    VALUES (?, ?, ?)
                ''', (email, token, datetime.now().isoformat()))
                
                imported += 1
                print(f"✓ Importato: {email}")
                
            except sqlite3.IntegrityError as e:
                print(f"⚠️  Errore inserimento {email}: {e}")
                skipped += 1
    
    # Commit delle modifiche
    conn.commit()
    conn.close()
    
    # Riepilogo
    print("\n" + "="*50)
    print("RIEPILOGO IMPORTAZIONE")
    print("="*50)
    print(f"✓ Importati: {imported}")
    print(f"⚠️  Duplicati: {duplicates}")
    print(f"⚠️  Saltati: {skipped}")
    print(f"TOTALE: {imported + duplicates + skipped}")
    print("="*50)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python import_contacts.py <file_csv>")
        print("Esempio: python import_contacts.py contatti_mailchimp_con_nome.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    import_contacts(csv_file)
