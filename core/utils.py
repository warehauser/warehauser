# Copyright 2024 warehauser @ github.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# utils.py

from enum import IntEnum
import re
import random
import string

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError

def filter_owner_groups(groups:list):
    return groups.filter(name__startswith='client_')

def validate_password(password:str) -> bool:
    """
    Check if a password meets the strength requirements specified in Django's
    AUTH_PASSWORD_VALIDATORS setting.

    Parameters:
    - password (str): The password to be checked for strength.

    Returns:
    - bool: True if the password meets the strength requirements, False otherwise.
    """
    try:
        # This function will raise a ValidationError if the password doesn't meet the validators
        validate_password(password)
        return True  # Password is valid according to the validators
    except ValidationError as e:
        # Password is invalid according to the validators
        # You can handle the error here or just return False
        return False

def generate_otp_code(length=6) -> str:
    """
    Generate a random OTP code (security code to verify password reset requests).
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length)).upper()

def is_valid_email_address(email:str) -> bool:
    """
    Check if an email address is of a valid format.
    Args:
        email str: email address to check.
    Returns:
        bool: True if email is valid, False otherwise.
    """
    # Make a regular expression for validating an email address
    valid_email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

    # pass the regular expression and the string into the fullmatch() method
    return re.fullmatch(valid_email_regex, email)

class WarehauserErrorCodes(IntEnum):
    # Define your error codes here
    NONE_NOT_ALLOWED                    = 0
    NONE_REQUIRED                       = 1
    MODEL_NOT_SAVED                     = 2
    WAREHAUSE_IS_STORAGE_FALSE          = 3
    DFN_MISMATCH                        = 4
    WAREHAUSE_QUANTITY_LOW              = 5
    CANNOT_DEFINE_DFN                   = 6
    PRODUCT_EXPIRES_MISMATCH            = 7
    PRODUCT_ALREADY_IN_STOCK            = 8
    WAREHAUSE_EMPTY                     = 9
    WAREHAUSE_STOCK_TOO_LOW             = 10
    MUTEX_ERROR                         = 11
    MUTEX_TIMEOUT_ERROR                 = 12
    BAD_PARAMETER                       = 13
    WAREHAUSE_MISMATCH_DFN              = 14
    WAREHAUSE_OVERLOAD                  = 15
    WAREHAUSE_PRODUCTDEF_NOT_MAPPED     = 16
    WAREHAUSE_RECEIVE_CHAIN_NOT_ALLOWED = 17
    PRODUCT_IN_OTHER_WAREHUASE          = 18
    DFN_NOT_ALLOWED                     = 19
    WAREHAUSE_NOT_CONTAINS              = 21
    WAREHAUSE_STOCK_NOT_FOUND           = 22
    STATUS_ERROR                        = 23

class WarehauserError(Exception):
    def __init__(self, msg, code, extra=None):
        super().__init__(msg)
        self.code = code
        self.extra = extra if extra is not None else dict()

    def __str__(self):
        return f"[{self.code}]: {self.args[0]}\nExtra: {self.extra}"

def dict_recursive_sort(d):
    if isinstance(d, dict):
        sorted_dict = {}
        for key, value in sorted(d.items()):
            sorted_dict[key] = dict_recursive_sort(value)
        return sorted_dict
    elif isinstance(d, list):
        return [dict_recursive_sort(item) for item in d]
    else:
        return d

def dict_recursive_update(d1, d2):
    for k, v in d2.items():
        if isinstance(v, dict) and k in d1 and isinstance(d1[k], dict):
            dict_recursive_update(d1[k], v)
        else:
            d1[k] = v

def dict_compare(d1, d2):
    return (dict_recursive_sort(d1.items()) == dict_recursive_sort(d2.items()))

def dict_get_or_default(d:dict, k:str, v:any=None) -> any:
    return d[k] if k in d else v

def dict_copy_and_update(d:dict, u:dict) -> dict:
    result = d.copy() if d is not None else dict()
    result.update(u if u is not None else dict())
    return result
