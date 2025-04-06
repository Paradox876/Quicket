import difflib
import re
from datetime import datetime

VALID_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

def correct_month_name(word):
    """Auto-corrects misspelled month names (e.g., 'Febuary' → 'February')."""
    matches = difflib.get_close_matches(word.capitalize(), VALID_MONTHS, n=1, cutoff=0.8)
    return matches[0] if matches else None

def validate_date(date_str):
    """
    Validates and normalizes date strings.
    
    Args:
        date_str (str): The date string to validate
        
    Returns:
        tuple: (is_valid, normalized_date)
    """
    try:
        # Handle the existing format (yyyy-MMM-dd)
        if re.match(r'\d{4}-[A-Za-z]{3}-\d{2}', date_str):
            # Validate by attempting to parse
            try:
                datetime.strptime(date_str, '%Y-%b-%d')
                return True, date_str
            except ValueError:
                return False, f"Invalid date format '{date_str}'"
        
        # Handles "Month Day, Year" format (e.g., "April 15, 2025")
        elif date_str[0].isalpha():
            parts = date_str.replace(',', '').split()
            if len(parts) < 3:
                return False, f"Invalid date format '{date_str}'"
            
            month = parts[0].capitalize()
            corrected_month = correct_month_name(month)
            
            if corrected_month:
                # Try to validate as a date
                try:
                    day = int(parts[1])
                    year = int(parts[2])
                    # Basic validation
                    if not (1 <= day <= 31 and 1900 <= year <= 2100):
                        return False, f"Day or year out of reasonable range in '{date_str}'"
                    
                    # Create standardized format
                    month_num = datetime.strptime(corrected_month, "%B").month
                    return True, f"{year}-{month_num:02d}-{day:02d}"

                except ValueError:
                    return False, f"Invalid day or year in '{date_str}'"
            else:
                return False, f"'{month}' is not a valid month"
        
        # Handles numeric format (MM/DD/YYYY or MM-DD-YYYY)
        elif re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', date_str):
            separator = '/' if '/' in date_str else '-'
            parts = date_str.split(separator)
            try:
                month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                
                # Basic validation
                if not (1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100):
                    return False, f"Date values out of range in '{date_str}'"             
                # Convert to standard format
                return True, f"{year}-{month:02d}-{day:02d}"
            except (ValueError, IndexError):
                return False, f"Invalid date components in '{date_str}'"
        
        # Unrecognized format
        else:
            return False, f"Unrecognized date format '{date_str}'"
            
    except Exception as e:
        return False, f"Error validating date '{date_str}': {str(e)}"

def validate_time(time_str):
    """
    More flexible time validation that accepts:
    - "1:00 PM" (with or without space before AM/PM)
    - "13:00" (24-hour format)
    - "1:00PM" (no space)
    Returns (is_valid, normalized_time_or_error_message)
    """
    try:
        # Clean the input
        time_str = time_str.strip().upper()
        time_str = time_str.replace("A.M.", "AM").replace("P.M.", "PM")
        time_str = time_str.replace(".", "")
        
        # Check for AM/PM format
        if "AM" in time_str or "PM" in time_str:
            time_part = time_str.replace("AM", "").replace("PM", "").strip()
            period = "AM" if "AM" in time_str else "PM"
            
            if ":" in time_part:
                hours, mins = map(int, time_part.split(":"))
            else:
                hours = int(time_part)
                mins = 0
            
            # Validate ranges
            if not (1 <= hours <= 12 and 0 <= mins <= 59):
                return False, f"Invalid time range in '{time_str}'"
            
            # Normalize format
            return True, f"{hours}:{mins:02d} {period}"
        
        # Check 24-hour format
        elif ":" in time_str:
            hours, mins = map(int, time_str.split(":"))
            if 0 <= hours <= 23 and 0 <= mins <= 59:
                return True, f"{hours:02d}:{mins:02d}"
            return False, f"Invalid 24-hour time '{time_str}'"
        
        return False, f"Unrecognized time format '{time_str}'"
    
    except Exception as e:
        return False, f"Error parsing time '{time_str}': {str(e)}"