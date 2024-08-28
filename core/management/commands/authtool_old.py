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

# authtool.py

import json
import getpass

from datetime import datetime
from typing import Callable

from django.contrib.auth import authenticate
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.forms.models import model_to_dict
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext as _

class WarehauserJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Converts to ISO 8601 format string
        if isinstance(obj, Group):
            return model_to_dict(obj)
        if isinstance(obj, User):
            return model_to_dict(obj, exclude=['password'])
        return super().default(obj)

class OutputHandler:
    def _output(self, message:str, pipe = None, func:Callable[[str], str] = None):
        """
        Display all command results other than help message and prompts for input.

        Args:
            self    (BaseCommand): self object.
            message (str):         String message to display.
            func    (func):        if not None then defer to that function for formatting. Ignored if json input parameter is True. If None then default to self.style.SUCCESS.
        """
        if pipe is None:
            pipe = self.stdout

        # Provide a default function if none is provided
        if func is None:
            func = self.style.SUCCESS

        # Handle standard output
        pipe.write(func(message))

    def _output_err(self, message:str):
        self._output(message=message, pipe=self.stderr, func=self.style.ERROR)

    def _output_success(self, message:str):
        self._output(message=message, pipe=self.stdout, func=self.style.SUCCESS)

class Command(BaseCommand, OutputHandler):

    help = _('Tool to manage clients and users of Warehauser.')

    def add_arguments(self, parser):
        parser.add_argument('entity', choices=['client', 'user'], help=_('Specify whether to manage a client or a user.'))
        parser.add_argument('name', nargs='?', help=_('Name of the client or user.'))

        parser.add_argument('-c', '--create', type=str, help=_('Create a new Client or User.'))
        parser.add_argument('-u', '--username', type=str, help=_('Username of the superuser account to use.'))
        parser.add_argument('-n', '--rename', type=str, help=_('Rename the client group or username.'))

        # Client options
        parser.add_argument('-a', '--add', type=str, help=_('Comma-separated list of usernames to add to the client group.'))
        parser.add_argument('-r', '--remove', type=str, help=_('Comma-separated list of usernames to remove from the client group.'))
        parser.add_argument('-s', '--status', type=int, help=_('Set the client status.'))

        # User options
        parser.add_argument('-A', '--active', choices=['true', 'false', '1', '0'], help=_('Set the user\'s active status.'))
        parser.add_argument('-e', '--email', type=str, help=_('Set the email address for the user.'))
        parser.add_argument('-f', '--first', type=str, help=_('Set the first name for the user.'))
        parser.add_argument('-l', '--last', type=str, help=_('Set the last name for the user.'))
        parser.add_argument('-p', '--password', action='store_true', help=_('Prompt for a new password for the user.'))
        parser.add_argument('-t', '--token', action='store_true', help=_('Create or get the user\'s Auth Token.'))

    def handle(self, *args, **options):
        entity = options.pop('entity')

        # login with superuser account to access authtool
        username = options.pop('username')
        if not username:
            username = input(_('Enter superuser username: '))
        supassword = getpass.getpass(_('Enter superuser password: '))

        superuser = authenticate(username=username, password=supassword)

        if superuser is None or not superuser.is_superuser:
            self._output_err(_('Invalid superuser credentials'))
            return

        # Re-parse the arguments conditionally based on the entity
        if entity == 'client':
            self.handle_client(**options)
        elif entity == 'user':
            self.handle_user(**options)

    def handle_client(self, **options):
        pass

    def handle_user(self, **options):
        name = options.pop('name')

        if name is None:
            users = User.objects.filter(is_staff=False, is_superuser=False)
            usernames = ', '.join(user.username for user in users)
            self._output_success(usernames)
            return

        user = User.objects.filter(username=name, is_staff=False, is_superuser=False).first()
        if user:
            email = options.pop('email')
            password = options.pop('password')

            if email is None and not password:
                message = json.dumps(user, indent=4, cls=WarehauserJSONEncoder)
                self._output_success(message=message)
        else:
            self._output_err(_('User not found'))


