# Validation Utility Functions.

import re
from typing import Tuple

def validate_kenyan_phone(phone: str) -> Tuple[bool, str]:
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check international format
    if cleaned.startswith('+254'):
        if len(cleaned) == 13 and cleaned[4] in '71':
            return True, cleaned
        return False, cleaned
    
    # Check local format
    if cleaned.startswith('0'):
        if len(cleaned) == 10 and cleaned[1] in '71':
            # Convert to international format
            normalized = '+254' + cleaned[1:]
            return True, normalized
        return False, cleaned
    
    return False, cleaned


def validate_national_id(national_id: str) -> Tuple[bool, str]:
    cleaned = re.sub(r'\s', '', national_id)
    
    # Standard 8-digit ID
    if len(cleaned) == 8 and cleaned.isdigit():
        return True, cleaned
    
    # Huduma Namba (may vary)
    if len(cleaned) >= 8 and cleaned.isdigit():
        return True, cleaned
    
    return False, cleaned

def validate_email_format(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_loan_amount(amount: float) -> Tuple[bool, Optional[str]]:
    if amount < 500:
        return False, "Minimum loan amount is KES 500"
    if amount > 500000:
        return False, "Maximum loan amount is KES 500,000"
    return True, None

# TODO: Add Huduma Namba validation
# TODO: Add business registration number validation
# TODO: Add Kenyan postal code validation