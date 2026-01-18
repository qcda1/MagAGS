# Programme pour créer les bases de données utilisées par MagAGS.py
#
import sqlite3
from conf import getconf



def create_table(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS magags (
        dtm TEXT PRIMARY KEY,
        gencontrol TEXT,
        start_limit INTEGER,
        soc INTEGER,
        stop_limit INTEGER,
        expected_state TEXT,
        relay_state TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS magagss (
        seq INTEGER PRIMARY KEY,
        dtm TEXT,
        gencontrol TEXT,
        start_limit INTEGER,
        soc INTEGER,
        stop_limit INTEGER,
        expected_state TEXT,
        relay_state TEXT
    )
    """)

#DB_FILE = getconf('fSQLite')
DB_FILE = 'testags.db'
conn = sqlite3.connect(DB_FILE)
create_table(conn)

# Créer l'enregistrement de départ
conn.execute("""
INSERT OR REPLACE INTO magagss VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (1, '2025-01-01 00:00:00', 'OFF', 10, 10, 20, 'OFF', 'OFF'))
conn.commit()
conn.close()
