
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'fadal_online_secret_key_2025'

# Initialize database
def init_db():
    conn = sqlite3.connect('fadal_online.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            transaction_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create admin user
    admin_password = hashlib.sha256('Fadal835'.encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password, is_admin)
        VALUES (?, ?, ?, ?)
    ''', ('fadal', 'admin@fadalonline.com', admin_password, 1))
    
    conn.commit()
    conn.close()

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_admin():
    return session.get('is_admin', False)

def check_login():
    return 'user_id' in session

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        conn = sqlite3.connect('fadal_online.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        ''', (name, email, subject, message))
        conn.commit()
        conn.close()
        
        flash('Fariintaada waa la diray! Waad ku mahadsan tahay.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('fadal_online.db')
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            flash('Username ama email ayaa horay loo isticmaalay!', 'error')
            conn.close()
            return render_template('register.html')
        
        # Create user
        hashed_password = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        ''', (username, email, hashed_password))
        conn.commit()
        conn.close()
        
        flash('Isdiiwaan galintaada waa guuleysatay! Hadda gal.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('fadal_online.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[3] == hash_password(password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[4]
            
            if user[4]:  # Admin user
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Username ama password qalad!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if not check_login():
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/admin')
def admin_panel():
    if not check_admin():
        flash('Ma laha ogolaansho in aad gasho admin panel!', 'error')
        return redirect(url_for('home'))
    
    conn = sqlite3.connect('fadal_online.db')
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    
    # Get all messages
    cursor.execute('SELECT * FROM messages ORDER BY created_at DESC')
    messages = cursor.fetchall()
    
    # Get all payments
    cursor.execute('SELECT * FROM payments ORDER BY created_at DESC')
    payments = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin.html', users=users, messages=messages, payments=payments)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/support', methods=['POST'])
def support():
    if request.method == 'POST':
        user_id = session.get('user_id')
        amount = 0.5
        payment_method = request.form.get('payment_method', 'general')
        
        if user_id:
            conn = sqlite3.connect('fadal_online.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (user_id, amount, payment_method)
                VALUES (?, ?, ?)
            ''', (user_id, amount, payment_method))
            conn.commit()
            conn.close()
        
        flash('Waad ku mahadsan tahay taageeradaada!', 'success')
        return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
