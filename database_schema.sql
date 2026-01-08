-- Database Schema per Newsletter Marketing System
-- Simile a Mailchimp con gestione completa contatti e unsubscribe

-- Tabella Contatti/Subscribers
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    status TEXT NOT NULL DEFAULT 'subscribed', -- subscribed, unsubscribed, bounced, pending
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at TIMESTAMP,
    unsubscribe_token TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    source TEXT, -- web_form, import, api, manual
    tags TEXT, -- JSON array of tags
    custom_fields TEXT, -- JSON object for custom data
    last_email_sent TIMESTAMP,
    email_opens_count INTEGER DEFAULT 0,
    email_clicks_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indici per performance
CREATE INDEX idx_subscribers_email ON subscribers(email);
CREATE INDEX idx_subscribers_status ON subscribers(status);
CREATE INDEX idx_subscribers_token ON subscribers(unsubscribe_token);

-- Tabella Campagne Email
CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    from_name TEXT NOT NULL,
    from_email TEXT NOT NULL,
    reply_to TEXT,
    template_id INTEGER,
    html_content TEXT,
    plain_content TEXT,
    status TEXT NOT NULL DEFAULT 'draft', -- draft, scheduled, sending, sent, paused
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    total_recipients INTEGER DEFAULT 0,
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_opens INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_bounces INTEGER DEFAULT 0,
    total_unsubscribes INTEGER DEFAULT 0,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabella Template Email
CREATE TABLE IF NOT EXISTS email_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    html_content TEXT NOT NULL,
    plain_content TEXT,
    thumbnail_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    category TEXT, -- promotional, transactional, newsletter
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabella Invii (tracking)
CREATE TABLE IF NOT EXISTS email_sends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    subscriber_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, sent, delivered, bounced, failed
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    last_opened_at TIMESTAMP,
    opens_count INTEGER DEFAULT 0,
    clicked_at TIMESTAMP,
    last_clicked_at TIMESTAMP,
    clicks_count INTEGER DEFAULT 0,
    bounce_reason TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE
);

CREATE INDEX idx_sends_campaign ON email_sends(campaign_id);
CREATE INDEX idx_sends_subscriber ON email_sends(subscriber_id);
CREATE INDEX idx_sends_status ON email_sends(status);

-- Tabella Link Tracking
CREATE TABLE IF NOT EXISTS link_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    subscriber_id INTEGER NOT NULL,
    send_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
    FOREIGN KEY (send_id) REFERENCES email_sends(id) ON DELETE CASCADE
);

CREATE INDEX idx_clicks_campaign ON link_clicks(campaign_id);
CREATE INDEX idx_clicks_subscriber ON link_clicks(subscriber_id);

-- Tabella Liste/Segmenti
CREATE TABLE IF NOT EXISTS lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    subscriber_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabella relazione Liste-Subscribers (many-to-many)
CREATE TABLE IF NOT EXISTS list_subscribers (
    list_id INTEGER NOT NULL,
    subscriber_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (list_id, subscriber_id),
    FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE CASCADE,
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE
);

-- Tabella Log Unsubscribe
CREATE TABLE IF NOT EXISTS unsubscribe_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscriber_id INTEGER NOT NULL,
    campaign_id INTEGER,
    reason TEXT,
    feedback TEXT,
    unsubscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

CREATE INDEX idx_unsub_subscriber ON unsubscribe_log(subscriber_id);
CREATE INDEX idx_unsub_campaign ON unsubscribe_log(campaign_id);

-- Tabella API Keys (per accesso sicuro)
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT 1,
    permissions TEXT, -- JSON array: ['read', 'write', 'delete']
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_api_keys ON api_keys(api_key);

-- Trigger per aggiornare updated_at automaticamente
CREATE TRIGGER update_subscribers_timestamp 
AFTER UPDATE ON subscribers
FOR EACH ROW
BEGIN
    UPDATE subscribers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_campaigns_timestamp 
AFTER UPDATE ON campaigns
FOR EACH ROW
BEGIN
    UPDATE campaigns SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_templates_timestamp 
AFTER UPDATE ON email_templates
FOR EACH ROW
BEGIN
    UPDATE email_templates SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Inserisci template di esempio
INSERT INTO email_templates (name, description, html_content, plain_content, category) VALUES
('Welcome Email', 'Template di benvenuto per nuovi iscritti', 
'<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{font-family:Arial,sans-serif;line-height:1.6;color:#333}</style></head><body><h1>Benvenuto!</h1><p>Grazie per esserti iscritto alla nostra newsletter.</p><p><a href="{{unsubscribe_url}}">Cancella iscrizione</a></p></body></html>',
'Benvenuto! Grazie per esserti iscritto alla nostra newsletter. Per cancellarti: {{unsubscribe_url}}',
'transactional');

INSERT INTO lists (name, description) VALUES
('Main List', 'Lista principale di tutti i contatti');
