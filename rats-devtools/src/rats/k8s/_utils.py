import re
from hashlib import sha1


def hash_value(value: str) -> str:
    return sha1(value.encode()).hexdigest()


def safe_value(value: str) -> str:
    """
    Convert a string to a safe value usable in Kubernetes labels.

    - Converts to lowercase
    - Replaces unsafe characters with dashes
    - Truncates to 63 characters max
    - Ensures it starts and ends with alphanumeric characters

    Raises:
        ValueError: If value is empty or does not contain at least one digit or letter
    """
    if not value:
        raise ValueError("Value must be at least 1 character long")

    # Check if value contains at least one digit or letter
    if not re.search(r"[a-zA-Z0-9]", value):
        raise ValueError("Value must contain at least one digit or letter")

    # Convert to lowercase
    safe = value.lower()

    # Replace unsafe characters (anything not alphanumeric, dash, underscore, or dot) with dashes
    safe = re.sub(r"[^a-z0-9\-]", "-", safe)

    # Replace multiple consecutive dashes with single dash
    safe = re.sub(r"-+", "-", safe)

    # Ensure it starts with alphanumeric character
    safe = re.sub(r"^[^a-z0-9]+", "", safe)

    # Truncate to 63 characters max
    if len(safe) > 63:
        safe = safe[:63]

    # Ensure it ends with alphanumeric character
    safe = re.sub(r"[^a-z0-9]+$", "", safe)

    return safe
