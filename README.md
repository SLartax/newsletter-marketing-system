# 📧 Newsletter Marketing System

Sistema completo di direct marketing con gestione newsletter, database contatti, template email responsive e funzione unsubscribe. **Simile a Mailchimp ma self-hosted e gratuito.**

## ✨ Caratteristiche Principali

- 📊 **Database SQLite** completo con gestione contatti
- 📧 **Sistema email** con tracking opens, clicks e bounces
- 🔗 **Token unsubscribe univoci** (GDPR compliant)
- 📝 **Template email** HTML responsive
- 🎯 **Campagne email** programmabili
- 📈 **Analytics dettagliati** per ogni campagna
- 🔐 **API sicure** con gestione chiavi
- 📋 **Liste e segmentazione** contatti
- 🚫 **Log disiscrizioni** con motivi e feedback

## 🚀 Come Usare

### 1️⃣ Installazione

```bash
# Clona il repository
git clone https://github.com/SLartax/newsletter-marketing-system.git
cd newsletter-marketing-system

# Installa le dipendenze Python
pip install -r requirements.txt
```

### 2️⃣ Inizializza il Database

```bash
# Crea il database SQLite dal schema
sqlite3 newsletter.db < database_schema.sql
```

Questo crea automaticamente:
- ✅ Tabella `subscribers` (contatti con token unsubscribe)
- ✅ Tabella `campaigns` (campagne email)
- ✅ Tabella `email_sends` (tracking invii)
- ✅ Tabella `link_clicks` (tracking click)
- ✅ Tabella `unsubscribe_log` (log disiscrizioni)
- ✅ Tabella `lists` (segmentazione)
- ✅ Template email di esempio

### 3️⃣ Aggiungi Contatti

**Metodo 1: Direttamente nel database**

```bash
sqlite3 newsletter.db
```

```sql
-- Genera un token univoco per l'unsubscribe
-- Usa questo comando Python per generare token:
-- python3 -c "import secrets; print(secrets.token_urlsafe(32))"

INSERT INTO subscribers (email, first_name, last_name, unsubscribe_token, status, source)
VALUES (
    'cliente@example.com',
    'Mario',
    'Rossi',
    'GENERA_TOKEN_UNIVOCO_QUI',  -- Usa il comando Python sopra
    'subscribed',
    'manual'
);
```

**Metodo 2: Importa da CSV** (TODO: implementare script)

### 4️⃣ Crea una Campagna Email

```sql
INSERT INTO campaigns (
    name,
    subject,
    from_name,
    from_email,
    reply_to,
    template_id,
    status
) VALUES (
    'Newsletter Gennaio 2026',
    'Le novità di questo mese',
    'Studio Legale Artax',
    'newsletter@studiolegaleartax.it',
    'info@studiolegaleartax.it',
    1,  -- ID del template
    'draft'
);
```

### 5️⃣ Invio Email (Python Script)

Crea un file `send_campaign.py`:

```python
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_campaign(campaign_id):
    # Connetti al database
    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    
    # Ottieni dettagli campagna
    cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    campaign = cursor.fetchone()
    
    # Ottieni tutti i subscribers attivi
    cursor.execute("SELECT * FROM subscribers WHERE status = 'subscribed'")
    subscribers = cursor.fetchall()
    
    # Configura SMTP
    smtp_server = "smtp.gmail.com"  # O il tuo server SMTP
    smtp_port = 587
    smtp_user = "tua-email@gmail.com"
    smtp_password = "tua-password"  # Usa App Password per Gmail
    
    for subscriber in subscribers:
        email = subscriber[1]  # Colonna email
        token = subscriber[7]  # Colonna unsubscribe_token
        
        # Crea email con link unsubscribe
        unsubscribe_url = f"https://tuosito.it/unsubscribe?token={token}"
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = campaign[2]  # subject
        msg['From'] = f"{campaign[3]} <{campaign[4]}>"  # from_name, from_email
        msg['To'] = email
        
        html_content = f"""
        <html>
          <body>
            <h1>Ciao!</h1>
            <p>Contenuto della tua newsletter qui.</p>
            <hr>
            <p style="font-size:12px;color:#666;">
              <a href="{unsubscribe_url}">Cancella iscrizione</a>
            </p>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Invia email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
                
                # Registra invio nel database
                cursor.execute(
                    "INSERT INTO email_sends (campaign_id, subscriber_id, status, sent_at) VALUES (?, ?, 'sent', datetime('now'))",
                    (campaign_id, subscriber[0])
                )
                print(f"Email inviata a {email}")
        except Exception as e:
            print(f"Errore invio a {email}: {e}")
    
    conn.commit()
    conn.close()

# Esempio: invia campagna ID 1
send_campaign(1)
```

Esegui:
```bash
python send_campaign.py
```

### 6️⃣ Gestione Unsubscribe

**Crea pagina web unsubscribe** (Flask esempio):

```python
from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)

@app.route('/unsubscribe')
def unsubscribe():
    token = request.args.get('token')
    
    if not token:
        return "Token mancante", 400
    
    conn = sqlite3.connect('newsletter.db')
    cursor = conn.cursor()
    
    # Trova subscriber con questo token
    cursor.execute(
        "UPDATE subscribers SET status='unsubscribed', unsubscribed_at=datetime('now') WHERE unsubscribe_token=?",
        (token,)
    )
    
    if cursor.rowcount > 0:
        # Log unsubscribe
        cursor.execute(
            """INSERT INTO unsubscribe_log (subscriber_id, ip_address)
               SELECT id, ? FROM subscribers WHERE unsubscribe_token=?""",
            (request.remote_addr, token)
        )
        conn.commit()
        conn.close()
        
        return render_template_string("""
        <html>
          <body style="font-family:Arial;text-align:center;padding:50px">
            <h1>✅ Disiscrizione Completata</h1>
            <p>Sei stato rimosso dalla nostra mailing list.</p>
            <p>Non riceverai più email da noi.</p>
          </body>
        </html>
        """)
    else:
        conn.close()
        return "Token non valido", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Esegui:
```bash
python unsubscribe_server.py
```

## 📊 Statistiche e Analytics

### Visualizza statistiche campagna:

```sql
SELECT 
    c.name,
    c.subject,
    c.total_sent,
    c.total_opens,
    c.total_clicks,
    c.total_unsubscribes,
    ROUND(c.total_opens * 100.0 / c.total_sent, 2) AS open_rate,
    ROUND(c.total_clicks * 100.0 / c.total_sent, 2) AS click_rate
FROM campaigns c
WHERE c.status = 'sent'
ORDER BY c.sent_at DESC;
```

### Esporta contatti attivi:

```sql
SELECT email, first_name, last_name, subscribed_at
FROM subscribers
WHERE status = 'subscribed'
ORDER BY subscribed_at DESC;
```

## 🔐 Sicurezza e GDPR

✅ **Token unsubscribe univoci** - Ogni subscriber ha un token sicuro  
✅ **Log completo disiscrizioni** - Traccia chi e quando si disiscritto  
✅ **Consenso esplicito** - Campo `status` traccia lo stato iscrizione  
✅ **IP tracking** - Registra IP per compliance  
✅ **Right to be forgotten** - Facile eliminare completamente un utente

## 📝 TODO / Sviluppi Futuri

- [ ] API REST completa con Flask
- [ ] Dashboard web di amministrazione
- [ ] Import/Export CSV contatti
- [ ] Editor WYSIWYG per email
- [ ] A/B testing campagne
- [ ] Automazioni (welcome series, drip campaigns)
- [ ] Integrazione con webhook
- [ ] Rate limiting e anti-spam

## 📄 Licenza

MIT License - Usa liberamente per progetti commerciali e personali.

## 🤝 Contributi

Contributi, issues e feature requests sono benvenuti!

---

**Creato da SLartax** - Sistema self-hosted alternativa a Mailchimp 🚀
