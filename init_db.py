#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Initialization Script
Initializes SQLite database with required tables for the newsletter system.
"""

import sqlite3
import os

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), 'newsletter.db')

def init_database(db_path=DEFAULT_DB_PATH):
    """Initialize database with all required tables"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read SQL schema file
    schema_path = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Execute schema
    cursor.executescript(schema_sql)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized successfully at: {db_path}")
    print("Tables created: subscribers, campaigns, unsubscribes")

if __name__ == "__main__":
    init_database()
