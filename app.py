from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Connect to the SQLite database
def connect_db():
    conn = sqlite3.connect('rent_management.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database with room and tenant tables
def init_db():
    conn = connect_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT,
            rent_amount REAL,
            is_active INTEGER
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_name TEXT,
            room_id INTEGER,
            FOREIGN KEY (room_id) REFERENCES rooms(room_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS electricity (
            reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER,
            previous_reading REAL,
            current_reading REAL,
            rate_per_unit REAL,
            FOREIGN KEY (room_id) REFERENCES rooms(room_id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    conn = connect_db()
    rooms = conn.execute('SELECT * FROM rooms WHERE is_active=1').fetchall()
    conn.close()
    return render_template('index.html', rooms=rooms)

@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    if request.method == 'POST':
        room_number = request.form['room_number']
        rent_amount = request.form['rent_amount']
        conn = connect_db()
        conn.execute('INSERT INTO rooms (room_number, rent_amount, is_active) VALUES (?, ?, 1)', 
                     (room_number, rent_amount))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('add_room.html')

@app.route('/add_tenant', methods=['GET', 'POST'])
def add_tenant():
    room_id = request.args.get('room_id')  # Get the room_id from the query string if available
    conn = connect_db()
    rooms = conn.execute('SELECT * FROM rooms WHERE is_active=1').fetchall()
    conn.close()
    
    if request.method == 'POST':
        tenant_name = request.form['tenant_name']
        room_id = request.form['room_id']
        conn = connect_db()
        conn.execute('INSERT INTO tenants (tenant_name, room_id) VALUES (?, ?)', 
                     (tenant_name, room_id))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    
    return render_template('add_tenant.html', rooms=rooms, selected_room_id=room_id)


@app.route('/remove_room/<int:room_id>')
def remove_room(room_id):
    conn = connect_db()
    conn.execute('UPDATE rooms SET is_active=0 WHERE room_id=?', (room_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/room_details/<int:room_id>')
def room_details(room_id):
    conn = connect_db()
    room = conn.execute('SELECT * FROM rooms WHERE room_id=?', (room_id,)).fetchone()
    tenants = conn.execute('SELECT * FROM tenants WHERE room_id=?', (room_id,)).fetchall()
    conn.close()
    return render_template('room_details.html', room=room, tenants=tenants)

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)
