import sqlite3
from config.config import Config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_PATH)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица рассылок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mailings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT,
                message_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_count INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица отправленных рассылок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_mailings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mailing_id INTEGER,
                user_id INTEGER,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mailing_id) REFERENCES mailings (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.conn.commit()

    def add_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users')
        return cursor.fetchall()

    def get_user_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]

    def save_mailing(self, message_text, message_type='text'):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO mailings (message_text, message_type)
            VALUES (?, ?)
        ''', (message_text, message_type))
        self.conn.commit()
        return cursor.lastrowid

    def get_mailing_stats(self, mailing_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM sent_mailings 
            WHERE mailing_id = ?
        ''', (mailing_id,))
        return cursor.fetchone()[0]

    def record_sent_mailing(self, mailing_id, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sent_mailings (mailing_id, user_id)
            VALUES (?, ?)
        ''', (mailing_id, user_id))
        self.conn.commit()

    def get_all_mailings(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT m.*, COUNT(sm.id) as sent_count 
            FROM mailings m 
            LEFT JOIN sent_mailings sm ON m.id = sm.mailing_id 
            GROUP BY m.id 
            ORDER BY m.created_at DESC
        ''')
        return cursor.fetchall()

    def close(self):
        self.conn.close()