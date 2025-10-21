import sqlite3
from datetime import datetime, timedelta
from config.config import Config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица рассылок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mailings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                message_text TEXT,
                message_type TEXT DEFAULT 'text',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_count INTEGER DEFAULT 0,
                audience_type TEXT DEFAULT 'all'
            )
        ''')
        
        # Таблица отправленных рассылок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_mailings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mailing_id INTEGER,
                user_id INTEGER,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'sent',
                FOREIGN KEY (mailing_id) REFERENCES mailings (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица активности пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

    def update_user_activity(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET last_activity = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()

    def record_user_activity(self, user_id, action_type="message"):
        """Записать активность пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO user_activity (user_id, action_type)
            VALUES (?, ?)
        ''', (user_id, action_type))
        self.conn.commit()

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY joined_date DESC')
        return cursor.fetchall()

    def get_user_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]

    def get_users_by_audience(self, audience_type):
        cursor = self.conn.cursor()
        
        if audience_type == 'all':
            cursor.execute('SELECT * FROM users')
        elif audience_type == 'active_week':
            cursor.execute('''
                SELECT DISTINCT u.* FROM users u
                JOIN user_activity ua ON u.user_id = ua.user_id
                WHERE ua.timestamp >= datetime('now', '-7 days')
            ''')
        elif audience_type == 'new_today':
            cursor.execute('''
                SELECT * FROM users 
                WHERE joined_date >= datetime('now', '-1 day')
            ''')
        elif audience_type == 'new_week':
            cursor.execute('''
                SELECT * FROM users 
                WHERE joined_date >= datetime('now', '-7 days')
            ''')
        else:
            return []
            
        return cursor.fetchall()

    def get_audience_count(self, audience_type):
        users = self.get_users_by_audience(audience_type)
        return len(users)

    def save_mailing(self, title, message_text, message_type='text', audience_type='all'):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO mailings (title, message_text, message_type, audience_type)
            VALUES (?, ?, ?, ?)
        ''', (title, message_text, message_type, audience_type))
        self.conn.commit()
        return cursor.lastrowid

    def update_mailing_stats(self, mailing_id, sent_count):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE mailings 
            SET sent_count = ? 
            WHERE id = ?
        ''', (sent_count, mailing_id))
        self.conn.commit()

    def get_mailing_stats(self, mailing_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM sent_mailings 
            WHERE mailing_id = ?
        ''', (mailing_id,))
        return cursor.fetchone()[0]

    def record_sent_mailing(self, mailing_id, user_id, status='sent'):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sent_mailings (mailing_id, user_id, status)
            VALUES (?, ?, ?)
        ''', (mailing_id, user_id, status))
        self.conn.commit()

    def get_all_mailings(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT m.*, COUNT(sm.id) as delivered_count 
            FROM mailings m 
            LEFT JOIN sent_mailings sm ON m.id = sm.mailing_id 
            GROUP BY m.id 
            ORDER BY m.created_at DESC
        ''')
        return cursor.fetchall()

    def get_mailing_by_id(self, mailing_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM mailings WHERE id = ?', (mailing_id,))
        return cursor.fetchone()

    def get_detailed_stats(self):
        cursor = self.conn.cursor()
        
        # Общее количество пользователей
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Новые пользователи за разные периоды
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE joined_date >= datetime('now', '-1 day')
        ''')
        new_users_today = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE joined_date >= datetime('now', '-7 day')
        ''')
        new_users_week = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE joined_date >= datetime('now', '-30 day')
        ''')
        new_users_month = cursor.fetchone()[0]
        
        # Активные пользователи (которые проявляли активность в последние 7 дней)
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM user_activity 
            WHERE timestamp >= datetime('now', '-7 day')
        ''')
        active_users_week = cursor.fetchone()[0]
        
        # Пользователи с активностью за последние 24 часа
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM user_activity 
            WHERE timestamp >= datetime('now', '-1 day')
        ''')
        active_users_today = cursor.fetchone()[0]
        
        # Статистика по рассылкам
        cursor.execute('SELECT COUNT(*) FROM mailings')
        total_mailings = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(sent_count) FROM mailings')
        total_sent_messages = cursor.fetchone()[0] or 0
        
        # Статистика доставки
        cursor.execute('SELECT COUNT(*) FROM sent_mailings WHERE status = "sent"')
        successful_deliveries = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sent_mailings WHERE status = "failed"')
        failed_deliveries = cursor.fetchone()[0]
        
        # Средняя активность пользователей
        cursor.execute('''
            SELECT COUNT(*) / COUNT(DISTINCT user_id) as avg_activity 
            FROM user_activity 
            WHERE timestamp >= datetime('now', '-7 day')
        ''')
        avg_activity_result = cursor.fetchone()
        avg_activity_per_user = avg_activity_result[0] if avg_activity_result[0] else 0

        return {
            'total_users': total_users,
            'new_users_today': new_users_today,
            'new_users_week': new_users_week,
            'new_users_month': new_users_month,
            'active_users_week': active_users_week,
            'active_users_today': active_users_today,
            'total_mailings': total_mailings,
            'total_sent_messages': total_sent_messages,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'avg_activity_per_user': round(avg_activity_per_user, 2)
        }

    def get_user_growth_data(self, days=30):
        """Получить данные о росте пользователей за период"""
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT date(joined_date) as date, COUNT(*) as count 
            FROM users 
            WHERE joined_date >= datetime('now', '-{days} day')
            GROUP BY date(joined_date)
            ORDER BY date
        ''')
        return cursor.fetchall()

    def get_activity_data(self, days=7):
        """Получить данные об активности пользователей за период"""
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT date(timestamp) as date, COUNT(*) as activity_count 
            FROM user_activity 
            WHERE timestamp >= datetime('now', '-{days} day')
            GROUP BY date(timestamp)
            ORDER BY date
        ''')
        return cursor.fetchall()

    def get_top_active_users(self, limit=10):
        """Получить самых активных пользователей"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.user_id, u.username, u.first_name, COUNT(ua.id) as activity_count
            FROM users u
            JOIN user_activity ua ON u.user_id = ua.user_id
            WHERE ua.timestamp >= datetime('now', '-30 day')
            GROUP BY u.user_id
            ORDER BY activity_count DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()

    def get_mailing_performance(self):
        """Получить статистику эффективности рассылок"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                m.id,
                m.title,
                m.created_at,
                m.sent_count,
                COUNT(sm.id) as delivered_count,
                ROUND((COUNT(sm.id) * 100.0 / m.sent_count), 2) as delivery_rate
            FROM mailings m
            LEFT JOIN sent_mailings sm ON m.id = sm.mailing_id AND sm.status = 'sent'
            GROUP BY m.id
            ORDER BY m.created_at DESC
        ''')
        return cursor.fetchall()

    def get_user_segments(self):
        """Получить сегменты пользователей для маркетинга"""
        cursor = self.conn.cursor()
        
        # Новые пользователи (последние 7 дней)
        cursor.execute('SELECT COUNT(*) FROM users WHERE joined_date >= datetime("now", "-7 days")')
        new_users = cursor.fetchone()[0]
        
        # Активные пользователи (активность в последние 7 дней)
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE timestamp >= datetime("now", "-7 days")')
        active_users = cursor.fetchone()[0]
        
        # Неактивные пользователи (нет активности 30+ дней)
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE user_id NOT IN (
                SELECT DISTINCT user_id FROM user_activity 
                WHERE timestamp >= datetime("now", "-30 days")
            )
        ''')
        inactive_users = cursor.fetchone()[0]
        
        # Пользователи с username
        cursor.execute('SELECT COUNT(*) FROM users WHERE username IS NOT NULL')
        users_with_username = cursor.fetchone()[0]
        
        return {
            'new_users': new_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'users_with_username': users_with_username,
            'users_without_username': self.get_user_count() - users_with_username
        }

    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()