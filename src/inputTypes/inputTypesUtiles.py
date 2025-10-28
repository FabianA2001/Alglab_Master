import uuid


def generate_random_uid() -> int:
    # Use uuid4 and convert to an integer (truncated to 64 bits for practical use)
    return uuid.uuid4().int >> 64  # type: ignore
