# app/db/db.py
from datetime import datetime
import mysql.connector
import os

def connect_db():
    """Establish connection to MySQL database using environment variables."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "bookingsystem")
    )

# Authentication Functions
def register_user(username, password):
    """Registers a new user in the database."""
    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        db.commit()
        return "Registration successful!"
    except mysql.connector.IntegrityError:
        return "Error: Username already exists!"
    finally:
        cursor.close()
        db.close()

def login_user(username, password):
    """Logs in a user and returns their user_id if successful."""
    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT user_id, password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if result:
            user_id, stored_password = result
            if stored_password == password:
                return user_id  # Return user_id for successful login
            return None  # Incorrect password
        return None  # User not found
    finally:
        cursor.close()
        db.close()
        
def create_user(username, password, full_name):
    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Check if the username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False  # Username exists

        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, password, full_name) VALUES (%s, %s, %s)",
            (username, password, full_name)
        )
        connection.commit()
        return True

    except Exception as e:
        print(f"Error creating user: {e}")
        return False
    
def create_booking(user_id, event_name, event_date=None, start_date=None, end_date=None, check_in_time=None,
                   ticket_type="Standard", quantity=1, passenger_name=None, from_location=None, to_location=None,
                   start_time=None, end_time=None):
    """Create individual ticket bookings and reservations in the database, supporting both single-day and multi-day bookings, including transport events."""
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        conn.start_transaction()  # Start transaction to ensure atomicity

        # Ensure the user exists before making a reservation
        cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            return False, "❌ User does not exist in the system."

        # Use the user's full_name if passenger_name is not provided
        if passenger_name is None:
            passenger_name = result[0]

        ticket_ids = []  # Store ticket IDs for tracking

        # Ensure event_date is set; if it's a multi-day booking, use start_date as event_date
        if not event_date:
            if start_date:
                event_date = start_date
            else:
                return False, "❌ Event date must be specified with 'ON DATE'."

        # Handle both single-day and multi-day events
        for _ in range(quantity):
            # Insert ticket into `tickets` table
            cursor.execute("""
            INSERT INTO tickets 
            (user_id, event_name, event_date, ticket_type, status, from_location, to_location, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
            (user_id, event_name, event_date, ticket_type, 'Reserved', from_location, to_location, start_time, end_time ))


            ticket_id = cursor.lastrowid  # Get the ID of the inserted ticket
            ticket_ids.append(ticket_id)

            # If it's a multi-day booking, insert into `multi_day_bookings`
            if start_date and end_date and check_in_time:
                cursor.execute("""
                    INSERT INTO multi_day_bookings (user_id, ticket_id, start_date, end_date, check_in_time)
                    VALUES (%s, %s, %s, %s, %s) """,
                    (user_id, ticket_id, start_date, end_date, check_in_time))

            # Insert reservation for each ticket
            cursor.execute("""
                INSERT INTO reservations 
                (user_id, ticket_id, action, passenger_name)
                VALUES (%s, %s, %s, %s)""", 
                (user_id, ticket_id, 'Reserved', passenger_name))

        conn.commit()  # Commit transaction if everything is successful

        # Prepare success response
        if start_date and end_date:
            response = (f"✅ Successfully booked {quantity} ticket(s) for {event_name}\n"
                        f"Stay: {start_date} - {end_date} at {check_in_time}\n"
                        f"Ticket IDs: {', '.join(map(str, ticket_ids))}\n"
                        f"From: {from_location} to {to_location}")
        else:
            location_part = f"\nLocation: {from_location}" if from_location else ""
            response = (f"✅ Successfully booked {quantity} ticket(s) for {event_name}{location_part}\n"
                        f"Ticket IDs: {', '.join(map(str, ticket_ids))}")

        return True, response

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()  # Rollback transaction in case of failure
        return False, f"❌ Booking failed: {err}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
def create_multiple_bookings(user_id, event_name, start_date, end_date, check_in_time, ticket_type="Standard", quantity=1, passenger_name=None):
    """Create a single multi-day booking entry in the database without generating tickets for each day."""
    conn = None
    cursor = None
    ticket_ids = []  # Store ticket IDs for tracking

    try:
        conn = connect_db()
        cursor = conn.cursor()
        conn.start_transaction()  # Start transaction

        # Ensure the user exists before making a reservation
        cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            return False, "❌ User does not exist in the system."

        # Use the user's full_name if passenger_name is not provided
        if passenger_name is None:
            passenger_name = result[0]

        for _ in range(quantity):
            # Insert a single ticket into `tickets` table (using the start_date as event_date)
            cursor.execute(""" 
                INSERT INTO tickets 
                (user_id, event_name, event_date, ticket_type, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, event_name, start_date, ticket_type, 'Reserved'))  # Use start_date for event_date

            ticket_id = cursor.lastrowid  # Get the ID of the inserted ticket
            ticket_ids.append(ticket_id)

            # Insert into `multi_day_bookings` only once for the booking range
            cursor.execute(""" 
                INSERT INTO multi_day_bookings (user_id, ticket_id, start_date, end_date, check_in_time)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, ticket_id, start_date, end_date, check_in_time))

            # Insert reservation for the ticket
            cursor.execute(""" 
                INSERT INTO reservations 
                (user_id, ticket_id, action, passenger_name)
                VALUES (%s, %s, %s, %s)
            """, (user_id, ticket_id, 'Reserved', passenger_name))

        conn.commit()  # Commit transaction if everything is successful

        return True, (f"✅ Successfully booked {quantity} ticket(s) for {event_name}\n"
                      f"Stay: {start_date} - {end_date} at {check_in_time}\n"
                      f"Ticket ID(s): {', '.join(map(str, ticket_ids))}")

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()  # Rollback transaction in case of failure
        return False, f"❌ Booking failed: {err}"
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
def process_payment(passenger_name, reservation_name=None, quantity=None, pay_all=False):
    """
    Processes payment for confirmed reservations only.
    Updates reservation and ticket status, and logs transaction.
    """
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        # Step 1: Query confirmed but unpaid reservations for this passenger
        query = """
        SELECT r.ticket_id, t.event_name FROM reservations r
        JOIN tickets t ON r.ticket_id = t.ticket_id
        LEFT JOIN transactions tr ON r.ticket_id = tr.ticket_id
        WHERE r.passenger_name = %s
        AND r.action = 'Confirmed'
        AND (tr.transaction_id IS NULL OR tr.payment_status != 'Completed')
        """
        params = [passenger_name]

        # If reservation name is specific (not just the word "RESERVATION")
        if reservation_name and reservation_name.upper() != "RESERVATION":
            query += " AND t.event_name = %s"
            params.append(reservation_name)

        if not pay_all and quantity:
            query += " LIMIT %s"
            params.append(quantity)

        cursor.execute(query, params)
        confirmed_tickets = cursor.fetchall()

        if not confirmed_tickets:
            search_term = reservation_name if reservation_name else "any event"
            return False, f"❌ No confirmed reservations found under '{search_term}' for passenger '{passenger_name}'."

        ticket_ids = []
        event_names = set()

        for row in confirmed_tickets:
            ticket_id = row['ticket_id']
            event_name = row['event_name']
            event_names.add(event_name)
            ticket_ids.append(ticket_id)

            # Step 1: Update reservation action to Paid
            cursor.execute("""
                UPDATE reservations
                SET action = 'Paid'
                WHERE passenger_name = %s AND ticket_id = %s
            """, (passenger_name, ticket_id))

            # Step 2: Update ticket status
            cursor.execute("""
                UPDATE tickets
                SET status = 'Paid'
                WHERE ticket_id = %s
            """, (ticket_id,))

            # Step 3: Log in transactions table
            cursor.execute("""
                INSERT INTO transactions (user_id, ticket_id, payment_status, timestamp)
                VALUES (
                    (SELECT user_id FROM reservations WHERE ticket_id = %s LIMIT 1),
                    %s, 'Completed', NOW()
                )
            """, (ticket_id, ticket_id))

        conn.commit()

        response = (f"Payment completed for {len(ticket_ids)} ticket(s) for '{passenger_name}'.\n"
                    f"Events: {', '.join(event_names)}\n"
                    f"Ticket IDs: {', '.join(map(str, ticket_ids))}")
        return True, response

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"❌ Payment failed: {err}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_reservation(passenger_name, event_name):
    """Retrieve reservations for a specific passenger and event."""
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Updated SQL to match passenger_name instead of user_id
        cursor.execute("""
            SELECT r.ticket_id, t.event_name, r.passenger_name, r.action, t.event_date
            FROM reservations r
            JOIN tickets t ON r.ticket_id = t.ticket_id
            WHERE r.passenger_name = %s AND t.event_name = %s
        """, (passenger_name, event_name))

        reservations = cursor.fetchall()

        if not reservations:
            return False, "❌ No reservations found for this user and event."

        response = f"Reservations for event '{event_name}':\n"
        for res in reservations:
            ticket_id, event_name, passenger_name, action, event_date = res
            response += (f"• Ticket ID: {ticket_id}, "
                         f"Event: {event_name}, "
                         f"Passenger: {passenger_name}, "
                         f"Action: {action}, "
                         f"Date: {event_date}\n")

        return True, response

    except mysql.connector.Error as err:
        return False, f"❌ Failed to fetch reservations: {err}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
           
def get_all_reservations(passenger_name):
    """Retrieve all reservations for a specific passenger."""
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.ticket_id, t.event_name, r.passenger_name, r.action, t.event_date, r.user_id
            FROM reservations r
            JOIN tickets t ON r.ticket_id = t.ticket_id
            WHERE r.passenger_name = %s
        """, (passenger_name,))

        reservations = cursor.fetchall()

        if not reservations:
            return False, f"❌ No reservations found for passenger '{passenger_name}'."

        response = f"All reservations for passenger '{passenger_name}':\n"
        for res in reservations:
            ticket_id, event_name, passenger_name, action, event_date, user_id = res
            response += (f"• Ticket ID: {ticket_id}, "
                         f"Event: {event_name}, "
                         f"Passenger: {passenger_name}, "
                         f"Action: {action}, "
                         f"Date: {event_date}, "
                         f"User ID: {user_id}\n")

        return True, response

    except mysql.connector.Error as err:
        return False, f"❌ Failed to fetch reservations: {err}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
def get_tickets_by_status(passenger_name, status):
    """Retrieve tickets for a specific passenger based on reservation status (e.g., 'Paid', 'Confirmed')."""
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Force lowercase matching to avoid case-sensitivity issues
        cursor.execute("""
            SELECT r.ticket_id, t.event_name, r.passenger_name, r.action, t.event_date, t.status
            FROM reservations r
            JOIN tickets t ON r.ticket_id = t.ticket_id
            WHERE LOWER(r.passenger_name) = LOWER(%s) AND LOWER(r.action) = LOWER(%s)
        """, (passenger_name, status))

        tickets = cursor.fetchall()

        if not tickets:
            return False, f"❌ No '{status.capitalize()}' tickets found for passenger '{passenger_name}'."

        response = f"{status.capitalize()} tickets for passenger '{passenger_name}':\n"
        for ticket_id, event_name, passenger, action, event_date, ticket_status in tickets:
            response += (f"• Ticket ID: {ticket_id}, "
                         f"Event: {event_name}, "
                         f"Date: {event_date}, "
                         f"Reservation Status: {action}, "
                         f"Ticket Status: {ticket_status}\n")

        return True, response

    except mysql.connector.Error as err:
        return False, f"❌ Failed to retrieve tickets: {err}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



def confirm_reservation(passenger_name, reservation_name=None, quantity=None, confirm_all=False):
    """
    Confirms reservations for a specific passenger and (optionally) event.
    """
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        conn.start_transaction()

        # Build base query
        query = """
            SELECT r.ticket_id 
            FROM reservations r
            JOIN tickets t ON r.ticket_id = t.ticket_id
            WHERE r.passenger_name = %s AND r.action = 'Reserved'
        """
        params = [passenger_name]

        # Add event filter if given
        if reservation_name:
            query += " AND t.event_name = %s"
            params.append(reservation_name)

        # Add quantity limit if not confirming all
        if not confirm_all and quantity:
            query += " LIMIT %s"
            params.append(quantity)

        cursor.execute(query, params)
        reserved_tickets = cursor.fetchall()

        if not reserved_tickets:
            return False, f"❌ No reservations found for passenger '{passenger_name}'" + \
                          (f" and event '{reservation_name}'." if reservation_name else ".")

        ticket_ids = [ticket[0] for ticket in reserved_tickets]

        for ticket_id in ticket_ids:
            # Update reservation action
            cursor.execute("""
                UPDATE reservations
                SET action = 'Confirmed'
                WHERE ticket_id = %s AND passenger_name = %s
            """, (ticket_id, passenger_name))

            # Update ticket status
            cursor.execute("""
                UPDATE tickets
                SET status = 'Confirmed'
                WHERE ticket_id = %s
            """, (ticket_id,))

        conn.commit()

        response = (f"✅ {len(ticket_ids)} reservation(s) confirmed for '{passenger_name}'" +
                    (f" under '{reservation_name}'." if reservation_name else ".") +
                    f"\nTicket IDs: {', '.join(map(str, ticket_ids))}")
        return True, response

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"❌ Confirmation failed: {err}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def cancel_reservation(passenger_name, reservation_name=None, quantity=None, cancel_all=False):
    """
    Cancels reservations for a given passenger and optional event.
    Affects reservations with action: 'Reserved', 'Paid', or 'Confirmed'.
    """
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        # Step 1: Find eligible reservations
        query = """
        SELECT r.ticket_id, t.event_name
        FROM reservations r
        JOIN tickets t ON r.ticket_id = t.ticket_id
        WHERE r.passenger_name = %s
        AND r.action IN ('Reserved', 'Paid', 'Confirmed')
        """
        params = [passenger_name]

        if reservation_name and reservation_name.upper() != "RESERVATION":
            query += " AND t.event_name = %s"
            params.append(reservation_name)

        if not cancel_all and quantity:
            query += " LIMIT %s"
            params.append(quantity)

        cursor.execute(query, params)
        tickets = cursor.fetchall()

        if not tickets:
            label = reservation_name if reservation_name else "any event"
            return False, f"❌ No eligible reservations found for '{passenger_name}' under '{label}'."

        ticket_ids = []
        event_names = set()

        for row in tickets:
            ticket_id = row['ticket_id']
            event_name = row['event_name']
            ticket_ids.append(ticket_id)
            event_names.add(event_name)

            # Update reservation
            cursor.execute("""
                UPDATE reservations
                SET action = 'Cancelled'
                WHERE passenger_name = %s AND ticket_id = %s
            """, (passenger_name, ticket_id))

            # Update ticket
            cursor.execute("""
                UPDATE tickets
                SET status = 'Cancelled'
                WHERE ticket_id = %s
            """, (ticket_id,))

        conn.commit()

        response = (f"✅ {len(ticket_ids)} reservation(s) cancelled for '{passenger_name}'.\n"
                    f"Events: {', '.join(event_names)}\n"
                    f"Ticket IDs: {', '.join(map(str, ticket_ids))}")
        return True, response

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return False, f"❌ Cancellation failed: {err}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def format_date(date_str):
    """
    Converts various date formats into "YYYY-MM-DD".
    Supports:
    - "March 15, 2025"
    - "15-03-2025"
    - "06-15-2025"
    - "2025-03-15"
    Returns None if parsing fails.
    """
    date_str = date_str.strip()  # Remove extra spaces
    date_formats = ["%B %d, %Y", "%d-%m-%Y", "%m-%d-%Y", "%Y-%m-%d"]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime("%Y-%m-%d")  # Convert to standard format
        except ValueError:
            continue
    
    raise ValueError(f"❌ Invalid date format: '{date_str}'. Expected formats: {date_formats}")

def is_date(date_string):
    """
    Check if a string can be parsed as a date in common formats.
    Supports formats like: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, etc.
    """
    date_formats = [
        '%Y-%m-%d',  # 2023-12-31
        '%d/%m/%Y',   # 31/12/2023
        '%m/%d/%Y',   # 12/31/2023
        '%d-%m-%Y',   # 31-12-2023
        '%m-%d-%Y',    # 12-31-2023
        # Add more formats as needed
    ]  
    for fmt in date_formats:
        try:
            datetime.strptime(date_string, fmt)
            return True
        except ValueError:
            continue
    return False

def to_sql_time(time_str):
    """Converts 'hh:mm AM/PM' to SQL TIME format 'HH:MM:SS'."""
    try:
        dt = datetime.strptime(time_str.strip(), "%I:%M %p")
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return None