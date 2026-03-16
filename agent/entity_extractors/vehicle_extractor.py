import re

def detect_vehicle_id(text):

    pattern = r"[A-Z0-9]{3,}-[A-Z0-9]{3,}-[A-Z0-9]{3,}"

    match = re.search(pattern, text)

    if match:
        return match.group()

    return None