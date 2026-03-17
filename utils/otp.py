"""
utils/otp.py - One-Time Password helpers
"""
import random


def generate_otp(length: int = 6) -> int:
    """Generate a random numeric OTP of the given length."""
    start = 10 ** (length - 1)
    end   = (10 ** length) - 1
    return random.randint(start, end)
