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

# backends.py

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .utils import is_valid_email_address

class WarehauserEmailOrUsernameAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print('core.backends.WarehauserEmailOrUsernameAuthBackend.authenticate(username,password) START.')
        if username is None or password is None:
            return None  # If either username or password is None, authentication cannot proceed
        
        # Check if the username is a valid email address
        is_email = is_valid_email_address(username)

        # Authenticate based on whether the username is an email or not
        if is_email:
            user = self.authenticate_with_email(username, password)
        else:
            user = self.authenticate_with_username(request, username, password)

        return user

    def authenticate_with_email(self, email, password):
        try:
            # Check if there are multiple users with the same email address
            users = get_user_model().objects.filter(email=email)
            if users.count() > 1:
                return None  # Return None if multiple users found with the same email

            # Get the user with the provided email address
            user = users.first()
        except get_user_model().DoesNotExist:
            return None

        # Check if the user's password is correct
        if user.check_password(password):
            return user  # Return the user if authentication succeeds
        else:
            return None  # Return None if authentication fails

    def authenticate_with_username(self, request, username, password):
        return super().authenticate(request=request, username=username, password=password)
