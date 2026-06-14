from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'campus123secret'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
socketio = SocketIO(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bio TEXT,
            phone TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            seller TEXT NOT NULL,
            image TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER,
            buyer TEXT NOT NULL,
            seller TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    listings = conn.execute('SELECT * FROM listings ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', listings=listings, user=session['user'])

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        name = data['name']
        email = data['email']
        password = data['password']
        hashed = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            conn = get_db()
            conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                        (name, email, hashed))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            print('Signup error:', e)
            return jsonify({'error': 'Email already registered'}), 400
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data['email']
        password = data['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user'] = user['name']
            return jsonify({'success': True})
        return jsonify({'error': 'Invalid email or password'}), 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/post')
def post():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('post.html')

@app.route('/api/listings', methods=['POST'])
def create_listing():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    title = request.form.get('title')
    description = request.form.get('description')
    price = request.form.get('price')
    category = request.form.get('category')
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename
    conn = get_db()
    conn.execute(
        'INSERT INTO listings (title, description, price, category, seller, image) VALUES (?, ?, ?, ?, ?, ?)',
        (title, description, price, category, session['user'], image_filename)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/chat/start/<int:listing_id>')
def start_chat(listing_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    listing = conn.execute('SELECT * FROM listings WHERE id = ?', (listing_id,)).fetchone()
    if not listing:
        return redirect(url_for('home'))
    if listing['seller'] == session['user']:
        return redirect(url_for('home'))
    chat = conn.execute(
        'SELECT * FROM chats WHERE listing_id = ? AND buyer = ?',
        (listing_id, session['user'])
    ).fetchone()
    if not chat:
        conn.execute(
            'INSERT INTO chats (listing_id, buyer, seller) VALUES (?, ?, ?)',
            (listing_id, session['user'], listing['seller'])
        )
        conn.commit()
        chat = conn.execute(
            'SELECT * FROM chats WHERE listing_id = ? AND buyer = ?',
            (listing_id, session['user'])
        ).fetchone()
    conn.close()
    return redirect(url_for('chat', chat_id=chat['id']))

@app.route('/chat/<int:chat_id>')
def chat(chat_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    chat = conn.execute('SELECT * FROM chats WHERE id = ?', (chat_id,)).fetchone()
    if not chat:
        return redirect(url_for('inbox'))
    if session['user'] not in [chat['buyer'], chat['seller']]:
        return redirect(url_for('inbox'))
    messages = conn.execute(
        'SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC',
        (chat_id,)
    ).fetchall()
    listing = conn.execute('SELECT * FROM listings WHERE id = ?', (chat['listing_id'],)).fetchone()
    conn.close()
    other_user = chat['seller'] if session['user'] == chat['buyer'] else chat['buyer']
    return render_template('chat.html', chat=chat, messages=messages, listing=listing, user=session['user'], other_user=other_user)

@app.route('/inbox')
def inbox():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    chats = conn.execute('''
        SELECT chats.id, chats.buyer, chats.seller, chats.created_at,
               listings.title as listing_title,
               COUNT(messages.id) as message_count
        FROM chats
        LEFT JOIN listings ON chats.listing_id = listings.id
        LEFT JOIN messages ON chats.id = messages.chat_id
        WHERE (chats.buyer = ? OR chats.seller = ?)
        GROUP BY chats.id
        HAVING message_count > 0
        ORDER BY chats.created_at DESC
    ''', (session['user'], session['user'])).fetchall()
    conn.close()
    return render_template('inbox.html', chats=chats, user=session['user'])

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE name = ?', (session['user'],)).fetchone()
    listings = conn.execute('SELECT * FROM listings WHERE seller = ? ORDER BY id DESC', (session['user'],)).fetchall()
    conn.close()
    return render_template('profile.html', user=user, listings=listings)

@app.route('/api/profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    bio = data.get('bio', '')
    phone = data.get('phone', '')
    conn = get_db()
    conn.execute('UPDATE users SET bio = ?, phone = ? WHERE name = ?',
                (bio, phone, session['user']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@socketio.on('join')
def on_join(data):
    join_room(data['room'])

@socketio.on('message')
def on_message(data):
    conn = get_db()
    conn.execute(
        'INSERT INTO messages (chat_id, sender, message) VALUES (?, ?, ?)',
        (data['chat_id'], data['sender'], data['message'])
    )
    conn.commit()
    conn.close()
    emit('message', data, room=str(data['chat_id']))

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True)
