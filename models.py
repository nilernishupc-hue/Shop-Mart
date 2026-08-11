import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = 'ecommerce.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        dob TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT NOT NULL,
        rating REAL NOT NULL,
        image_url TEXT NOT NULL
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        interaction_type TEXT NOT NULL, -- 'view', 'purchase', 'rate'
        rating INTEGER, -- 1-5, null if not a rating
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        review_text TEXT NOT NULL,
        review_image_url TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id),
        UNIQUE(user_id, product_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_products_df():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()
    return df

def get_interactions_df():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM interactions", conn)
    conn.close()
    return df
