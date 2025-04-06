import openai
import re


def web_search_response(prompt):
    """Uses GPT-4o Search Preview to perform a web search and return results."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-search-preview",
            messages=[{"role": "user", "content": prompt}],
            web_search_options={}
        )
        return response["choices"][0]["message"]["content"]  # Extract AI response
    except Exception as e:
        return f"System: Web Search Error - {str(e)}"
    
def is_search_command(user_input):
    """Checks if the user input matches search-triggering patterns."""
    patterns = [
        r"^LIST\s+STRING\s+SCHEDULE\s+FROM\s+.+\s+TO\s+.+\s+ON\s+.+\s+AT\s+.+$",  # LIST STRING SCHEDULE FROM <source> TO <destination> ON <date> AT <time>
        r"^LIST\s+AVAILABLE\s+.+\s+IN\s+.+$",  # LIST AVAILABLE <category> IN <region>
        r"^LIST\s+AVAILABLE\s+EVENTS\s+IN\s+.+$",  # LIST AVAILABLE EVENTS IN <region>
        r"^LIST\s+TICKETS\s+FOR\s+.+$",  # LIST TICKETS FOR <event>
        r"^LIST\s+TICKETS\s+FOR\s+.+\s+ON\s+.+$"  # LIST TICKETS FOR <event> ON <date>
    ]
    
    for pattern in patterns:
        if re.match(pattern, user_input, re.IGNORECASE):
            return True  # If input matches, trigger a web search
    return False
