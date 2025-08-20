import sqlite3
import json
from datetime import datetime, timedelta
from config import DB_FILE, REGULAR_SUB_PRICE, PREMIUM_SUB_PRICE, SUB_DURATION_DAYS, REFERRAL_REWARD

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                subscription_type TEXT DEFAULT 'none',
                subscription_end DATETIME,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица рефералов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                referrer_id INTEGER,
                referred_id INTEGER,
                reward_claimed BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (referrer_id, referred_id)
            )
        ''')
        
        # Таблица CD
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cooldowns (
                user_id INTEGER PRIMARY KEY,
                last_spam_time DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица админ рассылок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                message_text TEXT,
                sent_count INTEGER,
                failed_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
    def create_user(self, user_id, username, referral_code=None, referred_by=None):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, referral_code, referred_by)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, referral_code, referred_by))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()
    
    def get_balance(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def set_subscription(self, user_id, sub_type):
        cursor = self.conn.cursor()
        end_date = datetime.now() + timedelta(days=SUB_DURATION_DAYS)
        cursor.execute('''
            UPDATE users 
            SET subscription_type = ?, subscription_end = ?
            WHERE user_id = ?
        ''', (sub_type, end_date.isoformat(), user_id))
        self.conn.commit()
    
    def get_subscription(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT subscription_type, subscription_end FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result and result[1]:
            end_date = datetime.fromisoformat(result[1])
            if end_date > datetime.now():
                return result[0]  # active
        return 'none'
    
    def get_cooldown(self, user_id):
        """Получить время последнего спама"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT last_spam_time FROM cooldowns WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            try:
                return datetime.fromisoformat(result[0])
            except:
                return None
        return None
    
    def set_cooldown(self, user_id):
        """Установить время последнего спама"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO cooldowns (user_id, last_spam_time)
            VALUES (?, ?)
        ''', (user_id, now))
        self.conn.commit()
    
    def add_referral(self, referrer_id, referred_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id)
                VALUES (?, ?)
            ''', (referrer_id, referred_id))
            
            # Награда рефереру
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (REFERRAL_REWARD, referrer_id))
            
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_referral_stats(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND reward_claimed = TRUE', (user_id,))
        claimed = cursor.fetchone()[0]
        
        return total, claimed
    
    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, username, balance, subscription_type FROM users')
        return cursor.fetchall()
    
    def add_broadcast(self, admin_id, message_text, sent_count, failed_count):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO broadcasts (admin_id, message_text, sent_count, failed_count)
            VALUES (?, ?, ?, ?)
        ''', (admin_id, message_text, sent_count, failed_count))
        self.conn.commit()
        return cursor.lastrowid

db = Database()