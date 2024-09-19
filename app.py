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
def index():
    conn = connect_db()
    # Fetch all rooms with the balance field
    rooms = conn.execute('SELECT * FROM rooms').fetchall()

    # Fetch payment history for each room
    room_payment_history = {}
    for room in rooms:
        payments = conn.execute('SELECT * FROM payments WHERE room_id=? ORDER BY payment_date DESC', (room['room_id'],)).fetchall()
        room_payment_history[room['room_id']] = payments

    # Use direct indexing for sqlite3.Row
    for room in rooms:
        balance = room['balance'] if 'balance' in room else 0

    conn.close()

    return render_template('index.html', rooms=rooms, room_payment_history=room_payment_history)


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

    # Electricity rate per unit
    electricity_rate = 10  # Example rate per unit

    # Calculate electricity bill
    previous_reading = room['previous_meter_reading']
    current_reading = room['current_meter_reading']
    units_used = current_reading - previous_reading
    electricity_bill = units_used * electricity_rate

    # Assuming rent_amount is stored in the room and balance is previously stored
    rent_amount = room['rent_amount']
    balance = room['balance']

    conn.close()

    return render_template('room_details.html', 
                           room=room, 
                           tenants=tenants, 
                           previous_reading=previous_reading, 
                           current_reading=current_reading,
                           electricity_bill=electricity_bill,
                           balance=balance)


@app.route('/pay_rent/<int:room_id>', methods=['GET', 'POST'])
def pay_rent(room_id):
    conn = connect_db()
    room = conn.execute('SELECT * FROM rooms WHERE room_id=?', (room_id,)).fetchone()

    if request.method == 'POST':
        payment = int(request.form['payment_amount'])
        new_balance = room['balance'] - payment

        conn.execute('UPDATE rooms SET balance=? WHERE room_id=?', (new_balance, room_id))
        conn.commit()
        conn.close()

        return redirect(url_for('room_details', room_id=room_id))

    return render_template('pay_rent.html', room=room)


@app.route('/toggle_room/<int:room_id>', methods=['POST'])
def toggle_room(room_id):
    conn = connect_db()
    room = conn.execute('SELECT is_active FROM rooms WHERE room_id=?', (room_id,)).fetchone()

    # Toggle the room status
    new_status = 0 if room['is_active'] == 1 else 1
    conn.execute('UPDATE rooms SET is_active=? WHERE room_id=?', (new_status, room_id))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))


@app.route('/update_reading/<int:room_id>', methods=['GET', 'POST'])
def update_reading(room_id):
    conn = connect_db()
    room = conn.execute('SELECT * FROM rooms WHERE room_id=?', (room_id,)).fetchone()
    
    if request.method == 'POST':
        previous_reading = room['current_meter_reading']
        current_reading = request.form['current_meter_reading']
        electricity_rate = 10  # Example rate per unit of electricity

        # Calculate electricity bill
        units_used = int(current_reading) - previous_reading
        electricity_bill = units_used * electricity_rate

        # Update the meter readings and electricity bill in the database
        conn.execute('UPDATE rooms SET previous_meter_reading=?, current_meter_reading=? WHERE room_id=?',
                     (previous_reading, current_reading, room_id))
        conn.commit()
        conn.close()

        return redirect(url_for('room_details', room_id=room_id))

    return render_template('update_reading.html', room=room)

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)
