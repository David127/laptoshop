from string import ascii_uppercase, digits
from random import choices

def random_code(value):
    return ''.join(
        choices(ascii_uppercase + digits, k=value)
    )
