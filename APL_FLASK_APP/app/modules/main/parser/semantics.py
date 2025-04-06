import mysql.connector
from datetime import datetime
from app.db.db import connect_db
from app.modules.main.utils.web_utils import web_search_response

# Constants for reservation states
RESERVED = "RESERVED"
PAID = "PAID"
CONFIRMED = "CONFIRMED"
CANCELLED = "CANCELLED"

class BookingSystem:
    def __init__(self, lexer, parser):
        self.lexer = lexer
        self.parser = parser
        self.db_connector = connect_db  # Use your existing database connection

    def format_date(self, date_str):
        try:
            date_formats = [
                "%B %d, %Y",  # March 15, 2025
                "%b %d, %Y",  # Mar 15, 2025
                "%d-%m-%Y", 
                "%m-%d-%Y", 
                "%Y-%m-%d", 
                "%Y-%b-%d"   # ← ADD THIS!
            ]
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            raise ValueError(f"Invalid date format: '{date_str}'")
        except Exception as e:
            raise ValueError(f"Date formatting error: {str(e)}")

    def format_time(self, time_str):
        """
        Convert various time formats to standardized HH:MM (24-hour) format
        Supported formats:
        - 3:30 PM
        - 3:30PM
        - 3:30 P.M.
        - 15:30
        - 9:00am
        - 9 AM
        - 9:00 (assumed to be AM if no period specified)
        
        Returns:
        - Standardized time string (HH:MM) if valid
        - None if invalid format
        """
        time_str = str(time_str).strip().upper()
        
        # Clean the input string
        time_str = (time_str.replace("A.M.", "AM")
                        .replace("P.M.", "PM")
                        .replace(".", "")
                        .replace(" ", ""))
        
        try:
            # Handle 24-hour format (e.g., 15:30)
            if "AM" not in time_str and "PM" not in time_str:
                if ":" in time_str:
                    hours, mins = map(int, time_str.split(":"))
                    if 0 <= hours <= 23 and 0 <= mins <= 59:
                        return f"{hours:02d}:{mins:02d}"
                return None
            
            # Handle 12-hour format
            period = "AM" if "AM" in time_str else "PM"
            time_num = time_str.replace("AM", "").replace("PM", "")
            
            if ":" in time_num:
                hours, mins = map(int, time_num.split(":"))
            else:
                hours = int(time_num)
                mins = 0
                
            # Convert to 24-hour format
            if period == "PM" and hours != 12:
                hours += 12
            elif period == "AM" and hours == 12:
                hours = 0
                
            return f"{hours:02d}:{mins:02d}"
            
        except (ValueError, AttributeError):
            return None

    def process_input(self, user_input, user_id=None):
        """Processes user input exactly like your original function"""
        if not user_input.strip():
            return None, None

        try:
            print("\n--- Lexer Debug ---")
            tokens = self.lexer.tokenize(user_input)
            for tok in tokens:
                print(f"{tok.type}: {tok.value}")
            print("--- End Lexer Debug ---\n")
            # Parse the input using your parser
            parsed_command = self.parser.parse(user_input)
            print("Parsed Command:", parsed_command)
            if not parsed_command:
                return False, "Invalid command syntax"

            # Handle LIST command
            if parsed_command.get('type') == 'LIST_COMMAND':
                print(f"Parsed LIST command: {parsed_command}")
                return True, "Searching for relevant information..."  # Actual search would happen in GUI

            # Handle CONFIRM command
            elif parsed_command.get('type') == 'CONFIRM_COMMAND':
                print(f"Parsed CONFIRM command: {parsed_command}")
                return self.process_confirm(parsed_command)

            # Handle HELP command
            elif parsed_command.get('type') == 'HELP_COMMAND':
                return self.process_help(parsed_command)

            # Handle SHOW command
            elif parsed_command.get('type') == 'SHOW_COMMAND':
                print(f"Parsed SHOW command: {parsed_command}")
                return self.process_show(parsed_command)

            # Handle PAY command
            elif parsed_command.get('type') == 'PAY_COMMAND':
                print(f"Parsed PAY command: {parsed_command}")
                return self.process_pay(parsed_command)

            # Handle CANCEL command
            elif parsed_command.get('type') == 'CANCEL_COMMAND':
                print(f"Parsed CANCEL command: {parsed_command}")
                return self.process_cancel(parsed_command)

            # Handle BOOK command
            elif parsed_command.get('type') == 'BOOK_COMMAND':
                print(f"Parsed BOOK command: {parsed_command}")
                return self.process_book(parsed_command, user_id)

            else:
                return False, "Unsupported command type"

        except Exception as e:
            return False, f"Error - {str(e)}"

    # Individual command processors
    def process_confirm(self, parsed):
        """Process confirm reservation command"""
        from app.db.db import confirm_reservation  # Import your existing function
        passenger_name = parsed.get("Name")
        event_name = parsed.get("Event")
        quantity = str(parsed.get("Quantity", "")).upper()

        confirm_all = quantity == "ALL"
        quantity = None if confirm_all else int(quantity)
        return confirm_reservation(passenger_name, event_name, quantity, confirm_all)

    def process_help(self, parsed):
        """Process help command"""
        topic = parsed.get('Topic', 'GENERAL')
        help_messages = {
            'GENERAL': (
                "Help Categories:\n"
                '• HELP \"BOOK\": Booking options and formats\n'
                '• HELP \"CANCEL\": How to cancel a reservation\n'
                '• HELP \"CONFIRM\": How to confirm reservations\n'
                '• HELP \"SHOW\": How to display reservations\n'
                '• HELP \"PAY\": How to pay for tickets\n'
                '• HELP \"LIST\": How to list available events and schedules\n\n'
                'Tips:\n'
                '• Always wrap names and event titles in quotation marks (\" \")\n'
                '• Use actual numbers where <number> appears\n'
                '• Date formats: April 15, 2025 or 15-04-2025\n'
                '• Time format: HH:MM AM/PM (e.g., 9:00 AM)'
            ),

            'BOOK': (
                "Booking Commands:\n"
                '• BOOK \"Event\" ON DATE AT TIME FOR \"Name\" FOR <number>\n'
                '• BOOK \"Event\" AT \"Location\" ON DATE AT TIME FOR \"Name\" IN CLASS FOR <number>\n'
                '• BOOK \"Event\" FROM \"Location1\" TO \"Location2\" ON DATE AT TIME FOR \"Name\" FOR <number>\n'
                '• BOOK \"Event\" FROM DATE TO DATE AT TIME FOR \"Name\" FOR <number>\n'
                '• BOOK <number> \"Event\" FROM TIME TO TIME ON DATE FOR \"Name\"'
            ),

            'CANCEL': (
                "Cancellation Commands:\n"
                '• CANCEL <number> \"Event\" RESERVATION FOR \"Name\"\n'
                '• CANCEL ALL RESERVATION FOR \"Name\"'
            ),

            'CONFIRM': (
                "Confirmation Commands:\n"
                '• CONFIRM ALL RESERVATION FOR \"Name\"\n'
                '• CONFIRM <number> RESERVATION FOR \"Name\" FOR \"Event\"'
            ),

            'SHOW': (
                "Viewing Reservations:\n"
                '• SHOW \"Event\" RESERVATION FOR \"Name\"\n'
                '• SHOW ALL RESERVATION FOR \"Name\"\n'
                '• SHOW ALL PAID RESERVATION FOR \"Name\"\n'
                '• SHOW ALL CONFIRMED RESERVATION FOR \"Name\"\n'
                '• SHOW ALL CANCELLED RESERVATION FOR \"Name\"\n'
                '• SHOW ALL RESERVED RESERVATION FOR \"Name\"'
            ),

            'PAY': (
                "Payment Commands:\n"
                '• PAY ALL RESERVATION FOR \"Name\"\n'
                '• PAY FOR <number> \"Event\" RESERVATION FOR \"Name\"'
            ),

            'LIST': (
                "Listing Available Options:\n"
                '• LIST \"Event\" SCHEDULE FROM \"Location1\" TO \"Location2\" ON DATE AT TIME\n'
                '• LIST AVAILABLE \"Event\" IN \"Country\"\n'
                '• LIST AVAILABLE EVENTS IN \"Country\"\n'
                '• LIST TICKETS FOR \"Event\"\n'
                '• LIST TICKETS FOR \"Event\" ON DATE'
            )
        }
        return True, help_messages.get(topic, "No help available for this topic.")

    def process_show(self, parsed):
        """Process show reservation command"""
        from app.db.db import (get_tickets_by_status, 
                             get_all_reservations, 
                             get_reservation)
        
        passenger_name = parsed.get('Name')
        status = parsed.get('Status')
        reservation = parsed.get('Reservation')
        quantity = parsed.get('Quantity')

        if quantity == 'ALL':
            if status:
                return get_tickets_by_status(passenger_name, status)
            else:
                return get_all_reservations(passenger_name)
        else:
            return get_reservation(passenger_name, reservation)

    def process_pay(self, parsed):
        """Process payment command"""
        from app.db.db import process_payment
        passenger_name = parsed.get("Name")
        reservation_name = parsed.get("Reservation")
        quantity = str(parsed.get("Quantity", "")).upper()


        pay_all = str(quantity).upper() == "ALL" if quantity else False
        quantity = None if pay_all else int(quantity) if quantity else None

        return process_payment(
            passenger_name=passenger_name,
            reservation_name=reservation_name,
            quantity=quantity,
            pay_all=pay_all
        )

    def process_cancel(self, parsed):
        """Process cancel reservation command"""
        from app.db.db import cancel_reservation
        passenger_name = parsed.get("Name")
        reservation_name = parsed.get("Reservation")
        quantity = str(parsed.get("Quantity", "")).upper()


        cancel_all = str(quantity).upper() == "ALL" if quantity else False
        quantity = None if cancel_all else int(quantity) if quantity else None

        return cancel_reservation(
            passenger_name=passenger_name,
            reservation_name=reservation_name,
            quantity=quantity,
            cancel_all=cancel_all
        )

    def process_book(self, parsed, user_id):
        """Process booking command"""
        from app.db.db import create_booking, create_multiple_bookings
        
        if not user_id:
            return False, "You must be logged in to make bookings"

        event_name = parsed['Booking']
        quantity = int(parsed['Quantity'])
        passenger_name = parsed.get('Name')
        ticket_type = parsed.get('Class', 'Standard')

        # Case 1: Transport booking with FROM/TO
        if 'From' in parsed and 'To' in parsed and 'Date' in parsed and 'Time' in parsed:
            from_location = parsed['From']
            to_location = parsed['To']
            event_date = self.format_date(parsed['Date']) 
            check_in_time = parsed['Time']
            event_datetime = f"{event_date} {check_in_time}"

            return create_booking(
                user_id=user_id,
                event_name=event_name,
                event_date=event_datetime,
                check_in_time=check_in_time,
                ticket_type=ticket_type,
                quantity=quantity,
                passenger_name=passenger_name,
                from_location=from_location,
                to_location=to_location
            )

        # Case 2: Venue booking with AT
        elif 'AT' in parsed and 'Date' in parsed and 'Time' in parsed:
            event_date = self.format_date(parsed['Date']) 
            check_in_time = parsed['Time']
            event_datetime = f"{event_date} {check_in_time}"
            at_location = parsed['AT']

            return create_booking(
                user_id=user_id,
                event_name=event_name,
                event_date=event_datetime,
                check_in_time=check_in_time,
                ticket_type=ticket_type,
                quantity=quantity,
                passenger_name=passenger_name,
                from_location=at_location,
                to_location=None
            )

        # Case 3: Simple event booking
        elif 'Date' in parsed and 'Time' in parsed:
            event_date = self.format_date(parsed['Date']) 
            check_in_time = parsed['Time']
            event_datetime = f"{event_date} {check_in_time}"

            return create_booking(
                user_id=user_id,
                event_name=event_name,
                event_date=event_datetime,
                check_in_time=check_in_time,
                ticket_type=ticket_type,
                quantity=quantity,
                passenger_name=passenger_name
            )

        # Case 4: Multi-day booking
        elif 'From' in parsed and 'To' in parsed and 'Time' in parsed and isinstance(parsed['From'], str) and isinstance(parsed['To'], str):
            try:
                start_date = self.format_date(parsed['From'])
                end_date = self.format_date(parsed['To'])
                check_in_time = parsed['Time']
                return create_multiple_bookings(
                    user_id=user_id,
                    event_name=event_name,
                    start_date=start_date,
                    end_date=end_date,
                    check_in_time=check_in_time,
                    ticket_type=ticket_type,
                    quantity=quantity,
                    passenger_name=passenger_name
                )
            except ValueError as e:
                return False, str(e)

        # Case 5: Time range booking (FROM TIME TO TIME ON DATE)
        elif 'FROM' in parsed and 'To' in parsed and 'Date' in parsed:
            try:
                # Override event_name since it comes from 'Event' (not 'Booking')
                event_name = parsed.get('Event', '').strip()  # <-- Fix: Use 'Event' instead of 'Booking'
                passenger_name = parsed.get('Name', '').strip()
                
                # Format date and time
                start_time = self.format_time(parsed['FROM'])  # 'FROM' is uppercase from parser
                end_time = self.format_time(parsed['To'])     # e.g., "01:00 PM"
                event_date = self.format_date(parsed['Date']) # e.g., "2025-04-15"
                event_datetime = f"{event_date} {start_time}"
                
                # Validate presence of key fields
                if not all([event_name, passenger_name, start_time, end_time, event_date]):
                    return False, "❌ Missing required booking details (name, event, or time)."

                success, result = create_booking(
                    user_id=user_id,
                    event_name=event_name,       # <-- Now correctly using 'Event'
                    event_date=event_datetime,
                    check_in_time=start_time,    # Using check_in_time for consistency
                    end_time=end_time,           # Additional parameter (if needed)
                    ticket_type=ticket_type,     # Include ticket_type like other cases
                    quantity=quantity,
                    passenger_name=passenger_name
                )
                return success, result

            except ValueError as e:
                return False, f"❌ Data formatting error: {str(e)}"
            except Exception as e:
                return False, f"❌ Booking error: {str(e)}"
                                
    def process_list(self, parsed):
        """Process LIST command using web search"""
        print(f"Parsed LIST command: {parsed}")
        
        # Get search query based on command type
        if 'Schedule_Type' in parsed:  # LIST "Event" SCHEDULE FROM...TO...
            query = f"{parsed['Schedule_Type']} from {parsed['From']} to {parsed['To']} on {parsed['Date']}"
        elif 'Available' in parsed:  # LIST AVAILABLE...
            if parsed['Available'] == 'EVENTS':
                query = f"events in {parsed['Region']}"
            else:
                query = f"{parsed['Available']} in {parsed['Region']}"
        
        # Use your web search function
        try:
            results = web_search_response(query)
            return True, f"Search results for '{query}':\n{results}"
        except Exception as e:
            return False, f"Search failed: {str(e)}"
    
    def validate_syntax(self, parsed, user_input):
        """Validate command structure"""
        if not parsed:
            if '"' in user_input and user_input.count('"') % 2 != 0:
                return False, 'Error: Unclosed quotation marks'
            return False, 'Invalid command syntax'
        return True, ""

    def validate_reservation_state(self, reservation_name, passenger_name, allowed_states):
        """Check if reservation is in allowed state"""
        reservation = self.db.get_reservation(passenger_name, reservation_name)
        if not reservation:
            return False, "Reservation not found"
        
        if reservation.status not in allowed_states:
            state_descriptions = {
                RESERVED: "reserved but not paid",
                PAID: "already paid",
                CONFIRMED: "already confirmed",
                CANCELLED: "already cancelled"
            }
            return False, f"Cannot proceed - reservation is {state_descriptions[reservation.status]}"
        return True, ""