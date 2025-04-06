import re
import ply.lex as lex
from app.modules.main.utils.date_utils import validate_date, validate_time  # Updated import path
from app.modules.main.utils.country_list import COUNTRY_LIST

# List of token names
tokens = (
    # Commands
    'LIST', 'BOOK', 'CONFIRM', 'PAY', 'CANCEL', 'SHOW', 'HELP',
    # Prepositions and connectors
    'ALL', 'FOR', 'FROM', 'TO', 'ON', 'AT', 'IN', 'AVAILABLE',
    # Nouns
    'SCHEDULE', 'EVENTS', 'CLASS_TYPE', 'RESERVATION', 'TICKETS','STATUS',
    # Data types
    'DATE', 'TIME', 'STRING', 'QUANTITY',
)

# Regular expression rules for simple tokens
t_ignore = ' \t'

# Command tokens
def t_BOOK(t):
    r'BOOK\b'
    return t

def t_CONFIRM(t):
    r'CONFIRM\b'
    return t

def t_PAY(t):
    r'PAY\b'
    return t

def t_CANCEL(t):
    r'CANCEL\b'
    return t

def t_LIST(t):
    r'LIST\b'
    return t

def t_SHOW(t):
    r'SHOW\b'
    return t

def t_HELP(t):
    r'HELP\b'
    return t

# Prepositions and connectors
def t_ALL(t):
    r'ALL\b'
    return t

def t_FOR(t):
    r'FOR\b'
    return t

def t_FROM(t):
    r'FROM\b'
    return t

def t_TO(t):
    r'TO\b'
    return t

def t_ON(t):
    r'ON\b'
    return t

def t_AT(t):
    r'AT\b'
    return t

def t_MY(t):
    r'MY\b'
    return t

def t_IN(t):
    r'IN\b'
    return t

def t_AND(t):
    r'AND\b'
    return t

def t_WITH(t):
    r'WITH\b'
    return t

def t_AVAILABLE(t):
    r'AVAILABLE\b'
    return t


# Nouns
def t_SCHEDULE(t):
    r'SCHEDULE\b'
    return t

def t_EVENTS(t):
    r'EVENTS\b'  # Fixed: Using 'EVENTS' instead of 'EVENT'
    return t

def t_CLASS_TYPE(t):
    r'ECONOMY|BUSINESS|FIRST|VIP'
    t.value = t.value.upper()
    return t

def t_RESERVATION(t):
    r'RESERVATION\b'
    return t

def t_TICKETS(t):
    r'TICKETS'
    return t

def t_STATUS(t):
    r'RESERVED|CONFIRMED|PAID|CANCELLED|UNPAID'
    t.value = t.value.capitalize()  # Make it 'Reserved', 'Paid', etc.
    return t


# Date and time tokens
def t_DATE(t):
    r'([A-Za-z]+[\s]+[0-9]{1,2},[\s]*[0-9]{4})|([0-9]{4}-[0-9]{2}-[0-9]{2})|([0-9]{2}-[0-9]{2}-[0-9]{4})'
    t.value = t.value.strip()
    is_valid, normalized = validate_date(t.value)

    if not is_valid:
        print(f"Invalid date: {normalized}")
        t.lexer.skip(len(t.value))  # Skip the bad token
        return None

    t.value = normalized  # Set normalized "YYYY-MM-DD"
    return t



def t_TIME(t):
    r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm|A\.M\.|P\.M\.)?'
    is_valid, normalized_time = validate_time(t.value)
    if not is_valid:
        print(f"Invalid time: {normalized_time}")
        t.value = None
    else:
        t.value = normalized_time
    return t

def t_STRING(t):
    r'"[^"]+"'  # Matches anything between quotes
    t.value = t.value.strip('"')

    # Validate if this is a country
    if t.value.title() in COUNTRY_LIST:
        t.value = t.value.title()  
    return t

def t_QUANTITY(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Define the rule for handling newlines and ignoring extra spaces
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Handling errors
def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex(reflags=re.IGNORECASE)


def tokenize(input_text):
    """
    Tokenize the input text and return the list of tokens
    
    Args:
        input_text (str): The input string to tokenize
        
    Returns:
        list: List of token objects
    """
    lexer.input(input_text)
    tokens = list(lexer)
    return tokens


# Test function to demonstrate tokenization
def test_tokenizer(input_text):
    """
    Test function to display tokens from input
    
    Args:
        input_text (str): The input string to tokenize
    """
    print(f"\nTokenizing: '{input_text}'")
    lexer.input(input_text)
    
    print("\nTokens:")
    print("=======")
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(f"Type: {tok.type:<15} Value: '{tok.value}'")

# Example test cases
if __name__ == "__main__":
    test_cases = [
    
    'BOOK "Knutsford Express" FROM "Kingston" TO "Montego Bay" ON March 15, 2025 AT 9:00 AM FOR "John Doe"',
	'BOOK "Caribbean Cruise" ON 06-15-2025 AT 2:00 PM FOR "Jane Doe" FOR 4',
    'BOOK "Beach Resort Stay" FROM 07-01-2025 TO 07-07-2025 AT 3:00 PM FOR "Alex Smith" FOR 1',
    'BOOK "VIP Flight" AT "Sangster Airport" ON 07-01-2025 AT 8:00 AM FOR "Maria Johnson" IN FIRST FOR 3',
	'BOOK "VIP Flight" AT "Sangster Airport" ON 07-01-2025 AT 8:00 AM FOR "Maria Johnson" IN FIRST FOR 3',
    
    'CONFIRM 2 RESERVATION FOR "John Doe" FOR "VIP Flight"',
    'CONFIRM ALL RESERVATION FOR "Jane Smith"',

    'LIST "Knutsford Express" SCHEDULE FROM "Kingston" TO "Montego Bay" ON March 15, 2025 AT 9:00 AM',
    'LIST AVAILABLE "Jamaica Tours" IN Jamaica',
    'LIST AVAILABLE EVENTS IN Afghanistan',

    'PAY FOR 2 "American Airline Flight" RESERVATION FOR "John Doe"',
    'PAY FOR ALL RESERVATION FOR "Jane Smith"',

    'CANCEL 1 "VIP Flight" RESERVATION FOR "John Doe"',
    'CANCEL ALL RESERVATION FOR "Jane Smith"',

    'SHOW "JET BLUE" RESERVATION FOR "John Doe"',
    'SHOW ALL RESERVATION FOR "Jane Smith"',
    
    'SHOW TICKETS FOR "nba matches"',
    'SHOW TICKETS FOR "Reggae Fest" ON 03-02-2025',
    ]
    
    for test in test_cases:
        test_tokenizer(test)
        print("\n" + "-" * 50)
    
    # Interactive mode
    print("\nInteractive Tokenizer (Enter 'exit' to quit)")
    while True:
        try:
            user_input = input("\nEnter text to tokenize: ")
            if user_input.lower() == 'exit':
                break
            test_tokenizer(user_input)
        except EOFError:
            break
