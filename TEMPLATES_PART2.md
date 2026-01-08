# 🎨 TEMPLATE HTML - PARTE 2

Template completi per upload CSV, campagne, subscribers e edit.
Copia ogni sezione nel file corrispondente nella cartella `templates/`.

---

## 📄 File: `templates/upload_csv.html`

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload CSV - Newsletter Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui; background: #f5f5f5; }
        nav { background: #2c3e50; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        nav a { color: white; text-decoration: none; margin: 0 15px; }
        nav a:hover { text-decoration: underline; }
        .container { max-width: 800px; margin: 30px auto; padding: 0 20px; }
        .upload-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { margin-bottom: 20px; }
        .file-input { margin: 20px 0; padding: 20px; border: 2px dashed #ddd; border-radius: 5px; text-align: center; }
        input[type="file"] { display: block; margin: 20px auto; }
        button { padding: 12px 30px; background: #667eea; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #764ba2; }
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #e7f3ff; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 4px solid #667eea; }
    </style>
</head>
<body>
    <nav>
        <div><strong>📧 Newsletter Dashboard</strong></div>
        <div>
            <a href="/">Home</a>
            <a href="/upload-csv">📥 Upload CSV</a>
            <a href="/campaigns">📧 Campagne</a>
            <a href="/campaigns/new">➕ Nuova</a>
            <a href="/subscribers">👥 Contatti</a>
            <a href="/logout">🚪 Logout</a>
        </div>
    </nav>
    <div class="container">
        <div class="upload-box">
            <h1>📥 Upload File CSV</h1>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endwith %}
            <form method="POST" enctype="multipart/form-data">
                <div class="file-input">
                    <p>📁 Seleziona un file CSV con gli indirizzi email</p>
                    <input type="file" name="file" accept=".csv" required>
                </div>
                <button type="submit">⬆️ Carica e Importa Contatti</button>
            </form>
            <div class="info">
                <strong>ℹ️ Info:</strong> Il file CSV deve contenere una colonna con "email" nel nome.
                Il sistema estrarre automaticamente solo gli indirizzi email validi e genererà token unsubscribe univoci.
            </div>
        </div>
    </div>
</body>
</html>
```

---

## 📄 File: `templates/subscribers.html`

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contatti - Newsletter Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui; background: #f5f5f5; }
        nav { background: #2c3e50; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        nav a { color: white; text-decoration: none; margin: 0 15px; }
        nav a:hover { text-decoration: underline; }
        .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
        .box { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f9f9f9; font-weight: 600; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-active { background: #d4edda; color: #155724; }
        .badge-inactive { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <nav>
        <div><strong>📧 Newsletter Dashboard</strong></div>
        <div>
            <a href="/">Home</a>
            <a href="/upload-csv">📥 Upload CSV</a>
            <a href="/campaigns">📧 Campagne</a>
            <a href="/campaigns/new">➕ Nuova</a>
            <a href="/subscribers">👥 Contatti</a>
            <a href="/logout">🚪 Logout</a>
        </div>
    </nav>
    <div class="container">
        <div class="box">
            <h1>👥 Lista Contatti (ultimi 100)</h1>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Email</th>
                    <th>Nome</th>
                    <th>Cognome</th>
                    <th>Stato</th>
                    <th>Data Iscrizione</th>
                </tr>
                {% for sub in subscribers %}
                    <tr>
                        <td>{{ sub['id'] }}</td>
                        <td>{{ sub['email'] }}</td>
                        <td>{{ sub['first_name'] or '-' }}</td>
                        <td>{{ sub['last_name'] or '-' }}</td>
                        <td>
                            {% if sub['status'] == 'subscribed' %}
                                <span class="badge badge-active">Attivo</span>
                            {% else %}
                                <span class="badge badge-inactive">Disiscritt}}o</span>
                            {% endif %}
                        </td>
                        <td>{{ sub['subscribed_at'][:16] if sub['subscribed_at'] else '' }}</td>
                    </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
```

Continua...
