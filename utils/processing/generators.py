import random
import string


def generate_password(length: int = 12) -> str:
    characters = {
        "lower": string.ascii_lowercase,
        "upper": string.ascii_uppercase,
        "digits": string.digits,
        "symbols": "!@#&*"
    }

    password = [
        random.choice(characters["lower"]),
        random.choice(characters["upper"]),
        random.choice(characters["digits"]),
        random.choice(characters["symbols"]),
    ]

    all_chars = "".join(characters.values())
    password += random.choices(all_chars, k=length - 4)

    random.shuffle(password)
    return ''.join(password)
