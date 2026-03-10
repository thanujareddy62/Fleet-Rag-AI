import re

def extract_driver_data(text):

    name = None
    username = None
    password = None
    phone = None

    name_match = re.search(r"named\s+([A-Za-z]+)", text)
    username_match = re.search(r"username\s+([A-Za-z0-9_]+)", text)
    password_match = re.search(r"password\s+([A-Za-z0-9_]+)", text)
    phone_match = re.search(r"phone\s+([0-9]+)", text)

    if name_match:
        name = name_match.group(1)

    if username_match:
        username = username_match.group(1)

    if password_match:
        password = password_match.group(1)

    if phone_match:
        phone = phone_match.group(1)

    return {
        "name": name,
        "username": username,
        "password": password,
        "phone": phone
    }