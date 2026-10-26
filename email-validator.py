import re


def is_valid_email(email: str) -> bool:
    r"""
    Validates an email address based on the following criteria:
    1. Ends with '@cto-bhaiya.com'.
    2. Username is at least 6 characters long.
    3. Username contains only alphanumeric characters (no special characters).
    4. Username does not start with a digit (must start with a letter).
    
    Regex breakdown:
      ^[a-zA-Z]          -> Starts with an alphabet letter (not a digit)
      [a-zA-Z0-9]{5,}    -> Followed by at least 5 alphanumeric characters (total length >= 6)
      @cto-bhaiya\.com$  -> Exactly matches the '@cto-bhaiya.com' domain
    """
    pattern = r"^[a-zA-Z][a-zA-Z0-9]{5,}@cto-bhaiya\.com$"
    return bool(re.match(pattern, email, re.IGNORECASE))


def validate_email_detailed(email: str) -> tuple[bool, str]:
    """
    Validates email and returns (is_valid, reason) explaining failures step-by-step.
    """
    if not isinstance(email, str):
        return False, "Email must be a string."

    domain = "@cto-bhaiya.com"
    if not email.lower().endswith(domain):
        return False, f"Email must end with '{domain}'."

    # Extract username part before domain
    username = email[:-len(domain)]

    if len(username) < 6:
        return False, f"Username must be at least 6 characters long (got {len(username)})."

    if username[0].isdigit():
        return False, "Username must not start with a digit."

    if not username[0].isalpha():
        return False, "Username must start with a letter."

    if not username.isalnum():
        return False, "Username must not contain special characters (only letters and numbers allowed)."

    return True, "Valid email."


# ==========================================
# Test Cases
# ==========================================
if __name__ == "__main__":
    test_emails = [
        # Valid cases
        ("rahul1@cto-bhaiya.com", True),       # 6 chars, starts with letter, ends with domain
        ("coderX12@cto-bhaiya.com", True),     # >6 chars, alphanumeric
        ("CTOBHAIYA@cto-bhaiya.com", True),    # uppercase letters

        # Invalid cases
        ("user1@cto-bhaiya.com", False),       # Username has only 5 characters (< 6)
        ("1rahul@cto-bhaiya.com", False),      # Starts with a digit
        ("rahul_1@cto-bhaiya.com", False),     # Contains special character '_'
        ("rahul.1@cto-bhaiya.com", False),     # Contains special character '.'
        ("rahul@gmail.com", False),            # Incorrect domain
        ("rahul12@cto-bhaiya.com.org", False), # Extra characters after domain
        ("@cto-bhaiya.com", False),            # Empty username
    ]

    print("--- Running Email Validation Tests ---\n")
    for email, expected in test_emails:
        valid_regex = is_valid_email(email)
        valid_detailed, reason = validate_email_detailed(email)
        
        status = "PASSED" if (valid_regex == expected and valid_detailed == expected) else "FAILED"
        print(f"[{status}] Email: {email}")
        print(f"   -> Result: {'Valid' if valid_regex else 'Invalid'} | Reason: {reason}\n")

