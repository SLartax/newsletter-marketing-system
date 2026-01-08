# 🎨 TUTTI I TEMPLATE HTML

Questo file contiene tutti i template HTML necessari per la dashboard.
Copia ogni sezione nel file corrispondente nella cartella `templates/`.

---

## 📄 File: `templates/login.html`

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Newsletter Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            width: 350px;
        }
        h2 { text-align: center; margin-bottom: 30px; color: #333; }
        input {
            width: 100%;
            padding: 12px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: 0.3s;
        }
        button:hover { background: #764ba2; }
        .alert { padding: 10px; margin-bottom: 15px; border-radius: 5px; font-size: 14px; }
        .alert-error { background: #fee; color: #c33; border: 1px solid #fcc; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔐 Login Dashboard</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required autofocus>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Accedi</button>
        </form>
    </div>
</body>
</html>
```

---

## 📄 File: `templates/dashboard.html`

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Newsletter System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui; background: #f5f5f5; }
        nav {
            background: #2c3e50;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        nav a { color: white; text-decoration: none; margin: 0 15px; }
        nav a:hover { text-decoration: underline; }
        .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; }
        .stat-card .number { font-size: 36px; font-weight: bold; color: #667eea; }
        .campaigns { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .campaigns h2 { margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f9f9f9; font-weight: 600; }
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
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
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        <div class="stats">
            <div class="stat-card">
                <h3>Iscritti Attivi</h3>
                <div class="number">{{ total_subscribers }}</div>
            </div>
            <div class="stat-card">
                <h3>Campagne Totali</h3>
                <div class="number">{{ total_campaigns }}</div>
            </div>
        </div>
        <div class="campaigns">
            <h2>Campagne Recenti</h2>
            {% if recent_campaigns %}
                <table>
                    <tr>
                        <th>Nome</th>
                        <th>Subject</th>
                        <th>Stato</th>
                        <th>Data Creazione</th>
                    </tr>
                    {% for campaign in recent_campaigns %}
                        <tr>
                            <td>{{ campaign['name'] }}</td>
                            <td>{{ campaign['subject'] }}</td>
                            <td>{{ campaign['status'] }}</td>
                            <td>{{ campaign['created_at'][:16] if campaign['created_at'] else '' }}</td>
                        </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>Nessuna campagna ancora creata.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
```

Continua nel prossimo commit...
