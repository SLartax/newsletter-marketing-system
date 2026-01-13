#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
import_contacts.py
Importa contatti da un CSV/TXT nella tabella subscribers del DB newsletter.

Uso:
  python import_contacts.py --file ./uploads/contatti.csv

Env:
  DB_PATH=/var/data/newsletter.db
"""

from __future__ import annotations

import argparse
import csv
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Tuple


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "newsletter.db")
DB_PATH = os.environ.get("DB_PATH", DEFAULT_DB_PATH)

ALLOWED_EXTENSIONS = {".csv", ".txt"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample).delimiter
    except Exception:
        if "\t" in sample:
            return "\t"
        if ";" in sample:
            return ";"
        return ","


def detect_columns(fieldnames) -> Tuple[Optional[str], Optional[str]]:
    email_col = None
    name_col = None

    for field in fieldnames:
        low = field.lower().strip()

        if email_col is None and ("email" in low or "mail" in low):
            email_col = field

        if name_col is None and low in {"name", "nome", "full_name", "fullname"}:
            name_col = field

    return email_col, name_col


def import_contacts_from_csv(filepath: str) -> Tuple[int, int, int]:
    """
    Ritorna: (imported, duplicates, skipped)
    """
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
            raise ValueError("CSV vuoto o senza intestazioni (header).")

        email_col, name_col = detect_columns(reader.fieldnames)
        if not email_col:
            raise ValueError(
                "Colonna email non trovata. Attese intestazioni tipo: email, mail."
            )

        for row in reader:
            email = (row.get(email_col) or "").strip().lower()
            if not email:
                skipped += 1
                continue

            name = (row.get(name_col) or "").strip() if name_col else ""

            existing = cur.execute(
                "SELECT id FROM subscribers WHERE email = ?",
                (email,),
            ).fetchone()

            if existing:
                duplicates += 1
                continue

            token = secrets.token_hex(32)
            now_iso = utc_now_iso()

            try:
                cur.execute(
                    """
                    INSERT INTO subscribers
                        (email, name, status, unsubscribe_token, subscribed_at)
                    VALUES
                        (?, ?, "subscribed", ?, ?)
                    """,
                    (email, name, token, now_iso),
                )
            except sqlite3.OperationalError:
                cur.execute(
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Percorso CSV/TXT contatti")
    args = parser.parse_args()

    path = args.file
    ext = os.path.splitext(path)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise SystemExit("Formato non supportato: usa .csv o .txt")

    if not os.path.exists(path):
        raise SystemExit(f"File non trovato: {path}")

    imported, duplicates, skipped = import_contacts_from_csv(path)
    print(
        f"OK - Importati: {imported} | Duplicati: {duplicates} | Saltati: {skipped}"
    )


if __name__ == "__main__":
    main()

