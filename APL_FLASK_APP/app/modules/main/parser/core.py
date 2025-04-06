import ply.yacc as yacc
from app.modules.main.lexer import core as lexer
from app.modules.main.lexer.core import tokens, tokenize
from app.modules.main.utils.date_utils import validate_time
from app.modules.main.utils.country_list import COUNTRY_LIST


start = 'command'
parsed_results = {}

def p_command(p):
    '''command : list_command
               | book_command
               | confirm_command
               | pay_command
               | cancel_command
               | show_command
               | help_command'''
    p[0] = p[1]

def p_help_command(p):
    '''help_command : HELP
                    | HELP STRING'''
    node = {'type': 'HELP_COMMAND'}
    node['Topic'] = p[2].upper() if len(p) == 3 and isinstance(p[2], str) else 'GENERAL'
    p[0] = node

def p_list_command(p):
    '''list_command : LIST STRING SCHEDULE FROM STRING TO STRING ON DATE AT TIME
                    | LIST AVAILABLE STRING IN STRING
                    | LIST AVAILABLE EVENTS IN STRING
                    | LIST TICKETS FOR STRING
                    | LIST TICKETS FOR STRING ON DATE'''
    node = {'type': 'LIST_COMMAND'}

    if len(p) == 12:
        node.update({
            'Schedule_Type': p[2],
            'From': p[5],
            'To': p[7],
            'Date': p[9],
            'Time': p[11]
        })
    elif len(p) == 6 and isinstance(p[3], str) and p[3].upper() != "EVENTS":
        node['Available'] = p[3]
        node['STRING'] = p[5]
    elif len(p) == 6 and isinstance(p[3], str) and p[3].upper() == "EVENTS":
        node['Available'] = 'EVENTS'
        node['STRING'] = p[5]
    elif len(p) == 5:
        node['Action'] = 'LIST_TICKETS'
        node['Event'] = p[4]
    elif len(p) == 7:
        node['Action'] = 'LIST_TICKETS_DATE'
        node['Event'] = p[4]
        node['Date'] = p[6]

    p[0] = node

def p_book_command(p):
    '''book_command : BOOK STRING FROM STRING TO STRING ON DATE AT TIME FOR STRING FOR QUANTITY
                    | BOOK STRING AT STRING ON DATE AT TIME FOR STRING IN CLASS_TYPE FOR QUANTITY
                    | BOOK STRING ON DATE AT TIME FOR STRING FOR QUANTITY
                    | BOOK STRING FROM DATE TO DATE AT TIME FOR STRING FOR QUANTITY
                    | BOOK QUANTITY STRING FROM TIME TO TIME ON DATE FOR STRING'''
    
    node = {'type': 'BOOK_COMMAND'}

    # CASE 1: BOOK STRING FROM STRING TO STRING ON DATE AT TIME FOR STRING FOR QUANTITY
    if len(p) == 15 and p[3].upper() == "FROM":
        node.update({
            'Booking': p[2],
            'From': p[4],
            'To': p[6],
            'Date': p[8],
            'Time': p[10],
            'Name': p[12],
            'Quantity': int(p[14])
        })

    # CASE 2: BOOK STRING AT STRING ON DATE AT TIME FOR STRING IN CLASS_TYPE FOR QUANTITY
    elif len(p) == 15 and p[3].upper() == "AT" and p[11].upper() == "IN":
        node.update({
            'Booking': p[2],
            'AT': p[4],
            'Date': p[6],
            'Time': p[8],
            'Name': p[10],
            'Class': p[12],
            'Quantity': int(p[14])
        })

    # CASE 3: BOOK STRING ON DATE AT TIME FOR STRING FOR QUANTITY
    elif len(p) == 11 and p[3].upper() == "ON":
        node.update({
            'Booking': p[2],
            'Date': p[4],
            'Time': p[6],
            'Name': p[8],
            'Quantity': int(p[10])
        })

    # CASE 4: BOOK STRING FROM DATE TO DATE AT TIME FOR STRING FOR QUANTITY
    elif len(p) == 13 and p[3].upper() == "FROM" and p[5].upper() == "TO":
        node.update({
            'Booking': p[2],
            'From': p[4],
            'To': p[6],
            'Time': p[8],
            'Name': p[10],
            'Quantity': int(p[12])
        })

    # CASE 5: BOOK QUANTITY STRING FROM TIME TO TIME ON DATE FOR STRING
    elif len(p) == 12 and p[4].upper() == "FROM" and p[6].upper() == "TO" and p[8].upper() == "ON":
        node.update({
            'Quantity': int(p[2]),
            'Event': p[3],
            'FROM' : p[5],
            'To' : p[7],
            'Date': p[9],
            'Name': p[11]
        })

    p[0] = node

def p_confirm_command(p):
    '''confirm_command : CONFIRM QUANTITY RESERVATION FOR STRING FOR STRING
                       | CONFIRM ALL RESERVATION FOR STRING'''
    
    node = {'type': 'CONFIRM_COMMAND'}

    # Case 1: CONFIRM <quantity> RESERVATION FOR "Name" FOR "Event"
    if len(p) == 8 and str(p[3]).upper() == 'RESERVATION' and str(p[4]).upper() == 'FOR':
        node['Quantity'] = int(p[2]) if isinstance(p[2], int) else p[2]
        node['Name'] = p[5]
        node['Event'] = p[7]

    # Case 2: CONFIRM ALL RESERVATION FOR "Name"
    elif len(p) == 6 and str(p[2]).upper() == 'ALL' and str(p[3]).upper() == 'RESERVATION':
        node['Quantity'] = 'ALL'
        node['Name'] = p[5]
        node['Event'] = None
    p[0] = node
    
def p_pay_command(p):
    '''pay_command : PAY FOR QUANTITY STRING RESERVATION FOR STRING
                   | PAY FOR ALL RESERVATION FOR STRING
                   | PAY ALL RESERVATION FOR STRING'''
    
    node = {'type': 'PAY_COMMAND'}

    # Case 1: PAY FOR 5 "String" RESERVATION FOR "Name"
    if len(p) == 8 and isinstance(p[3], int):
        node['Quantity'] = p[3]
        node['Reservation'] = p[4]
        node['Name'] = p[7]

    # Case 2: PAY FOR ALL RESERVATION FOR "Name"
    elif len(p) == 7 and p[3].upper() == 'ALL':
        node['Quantity'] = 'ALL'
        node['Reservation'] = None
        node['Name'] = p[6]

    # Case 3: PAY ALL RESERVATION FOR "Name"
    elif len(p) == 6 and p[2].upper() == 'ALL':
        node['Quantity'] = 'ALL'
        node['Reservation'] = None
        node['Name'] = p[5]

    p[0] = node

def p_cancel_command(p):
    '''cancel_command : CANCEL QUANTITY STRING RESERVATION FOR STRING
                      | CANCEL ALL RESERVATION FOR STRING'''
    
    node = {'type': 'CANCEL_COMMAND'}

    # Case 1: CANCEL <quantity> "Event" RESERVATION FOR "Name"
    if len(p) == 7 and str(p[4]).upper() == 'RESERVATION':
        node['Quantity'] = int(p[2]) if isinstance(p[2], int) else p[2]
        node['Reservation'] = p[3]  # Event name (STRING)
        node['Name'] = p[6]

    # Case 2: CANCEL ALL RESERVATION FOR "Name"
    elif len(p) == 6 and str(p[2]).upper() == 'ALL':
        node['Quantity'] = 'ALL'
        node['Reservation'] = None
        node['Name'] = p[5]

    p[0] = node

def p_show_command(p):
    '''show_command : SHOW ALL STATUS RESERVATION FOR STRING
                    | SHOW ALL RESERVATION FOR STRING
                    | SHOW STRING RESERVATION FOR STRING'''
    node = {'type': 'SHOW_COMMAND'}

    if len(p) == 7 and isinstance(p[3], str) and p[4].upper() == 'RESERVATION':
        node.update({'Quantity': 'ALL', 'Status': p[3].capitalize(), 'Name': p[6]})
    elif len(p) == 6 and isinstance(p[3], str) and p[3].upper() == 'RESERVATION':
        node.update({'Quantity': 'ALL', 'Status': None, 'Name': p[5]})
    elif len(p) == 6 and isinstance(p[3], str) and p[3].upper() == 'RESERVATION':
        node.update({'Reservation': p[2], 'Name': p[5], 'Status': None})

    p[0] = node

def p_error(p):
    if not p:
        print("Syntax error at EOF.")
        return

    error_message = f"Syntax error at '{p.value}', line {p.lineno}: "
    if p.type == "STRING":
        error_message += "Expected quotes around names."
    elif p.type == "DATE":
        error_message += "Invalid date format."
    elif p.type == "TIME":
        error_message += "Invalid time format."
    else:
        error_message += "Unexpected token."
    print(error_message)



def parse(input_text):
    return parser.parse(input_text)

def test_parser(input_text):
    print(f"\nParsing: '{input_text}'")
    try:
        lexer_tokens = tokenize(input_text)
        print("\nTokens:")
        for tok in lexer_tokens:
            print(f"Type: {tok.type:<15} Value: '{tok.value}'")
        result = parse(input_text)
        print("\nParsed Result:")
        print_parse_tree(result)
    except Exception as e:
        print(f"Error: {e}")

def print_parse_tree(node, level=0, first_call=True):
    if not isinstance(node, dict):
        print(f"{'    ' * level}|-- {node}")
        return
    if first_call:
        print(f"+-- {node.get('type', 'Root')}")
        level += 1
    for key, value in node.items():
        if key == 'type' and first_call:
            continue
        print(f"{'    ' * level}+-- {key}")
        if isinstance(value, dict):
            print_parse_tree(value, level + 1, False)
        elif isinstance(value, (list, tuple)):
            for item in value:
                print_parse_tree(item, level + 1, False)
        else:
            print(f"{'    ' * (level + 1)}|-- {value}")
            

# Build the parser
parser = yacc.yacc()
