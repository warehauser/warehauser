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

import getpass
import sys

from datetime import datetime
from argparse import ArgumentTypeError
from typing import Callable

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.forms.models import model_to_dict
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext as _

from ...models import Client

class Command(BaseCommand):
    def _add_client_subparser(self, parser):
        # Add your client-specific subcommands here
        client_subparsers = parser.add_subparsers(dest='action', help=_('Client actions.'))

        # Create subparser
        create_parser = client_subparsers.add_parser('create', aliases=['c'], help=_('Create a new client.'))
        create_parser.add_argument('clientname', type=str, help=_('The name of the client to create.'))
        create_parser.add_argument('-e', '--email', type=str, required=True, help=_('Email address for the client\'s group admin user account.'))
        create_parser.set_defaults(func=self._handle_client_create)

        # Read subparser
        read_parser = client_subparsers.add_parser('read', aliases=['r'], help=_('Display information about an existing client.'))
        read_parser.add_argument('clientname', type=str, nargs='?', help=_('The name of the client to read.'))
        read_parser.set_defaults(func=self._handle_client_read)

        # Update subparser
        update_parser = client_subparsers.add_parser('update', aliases=['u'], help=_('Update an existing client.'))
        update_parser.add_argument('clientname', type=str, help=_('The name of the client to update.'))
        update_parser.add_argument('-e', '--email', type=str, help=_('Update user\'s email address.'))
        update_parser.add_argument('-t', '--token', type=self.str_to_bool, nargs='?', const=True, default=None, help=_('If False delete the User\s Auth Token, if True then create the Auth Token (if it does not exist) and display it.'))
        update_parser.add_argument('-n', '--name', type=str, nargs='?', help=_('Update client\'s group name.'))
        update_parser.set_defaults(func=self._handle_client_update)

    def _add_user_subparser(self, parser):
        # Subparsers for user commands
        user_subparsers = parser.add_subparsers(dest='action', help=_('User actions.'))

        # Create subparser
        create_parser = user_subparsers.add_parser('create', aliases=['c'], help=_('Create a new user.'))
        create_parser.add_argument('username', type=str, help=_('The username of the user to create.'))
        create_parser.add_argument('-c', '--clientname', type=str, help=_('Join user to a client.'))
        create_parser.add_argument('-e', '--email', type=str, help=_('Update user\'s email address.'))
        create_parser.add_argument('-t', '--token', type=self.str_to_bool, nargs='?', const=True, default=None, help=_('If False delete the User\s Auth Token, if True then create the Auth Token (if it does not exist) and display it.'))
        create_parser.add_argument('-a', '--is_active', type=self.str_to_bool, nargs='?', const=True, default=None, help=_('Set user\'s is_active status. If True, the user is active; if False, the user is inactive.'))
        create_parser.add_argument('-f', '--first', type=str, nargs='?', help=_('Update user\'s first name. Use \\blank to set to empty string.'))
        create_parser.add_argument('-l', '--last', type=str, nargs='?', help=_('Update user\'s last name. Use \\blank to set to empty string.'))
        create_parser.add_argument('-j', '--join', type=str, nargs='?', help=_('Join user to a comma separated list of groups.'))
        create_parser.set_defaults(func=self._handle_user_create)

        # Read subparser
        read_parser = user_subparsers.add_parser('read', aliases=['r'], help=_('Display information about an existing user.'))
        read_parser.add_argument('username', type=str, nargs='?', help=_('The username of the user to read.'))
        read_parser.add_argument('-c', '--clientname', type=str, nargs='?', help=_('Find User(s) which are members of client.'))
        read_parser.set_defaults(func=self._handle_user_read)

        # Update subparser
        update_parser = user_subparsers.add_parser('update', aliases=['u'], help=_('Update an existing user.'))
        update_parser.add_argument('username', type=str, help=_('The username of the user to update.'))
        update_parser.add_argument('-t', '--token', type=self.str_to_bool, nargs='?', const=True, default=None, help=_('If False delete the User\s Auth Token, if True then create the Auth Token (if it does not exist) and display it.'))
        update_parser.add_argument('-a', '--is_active', type=self.str_to_bool, nargs='?', const=True, default=None, help=_('Set user\'s is_active status. If True, the user is active; if False, the user is inactive.'))
        update_parser.add_argument('-n', '--name', type=str, nargs='?', help=_('Update user\'s username.'))
        update_parser.add_argument('-f', '--first', type=str, nargs='?', help=_('Update user\'s first name. Use \\blank to set to empty string.'))
        update_parser.add_argument('-l', '--last', type=str, nargs='?', help=_('Update user\'s last name. Use \\blank to set to empty string.'))
        update_parser.add_argument('-e', '--email', type=str, nargs='?', help=_('Update user\'s email address.'))
        update_parser.add_argument('-j', '--join', type=str, nargs='?', help=_('Join user to a comma separated list of groups.'))
        update_parser.add_argument('-r', '--revoke', type=str, nargs='?', help=_('Revoke user from a comma separated list of groups.'))
        update_parser.set_defaults(func=self._handle_user_update)

    def add_arguments(self, parser):
        # Main subparser for client and user commands
        subparsers = parser.add_subparsers(dest='entity', help=_('Specify whether to manage a client or a user.'))

        # Add subparsers for client and user
        client_parser = subparsers.add_parser('client', aliases=['c'], help=_('Manage clients.'))
        self._add_client_subparser(client_parser)

        user_parser = subparsers.add_parser('user', aliases=['u'], help=_('Manage users.'))
        self._add_user_subparser(user_parser)

    def handle(self, *args, **options):
        try:
            func = options.get('func')
            if func:
                func(options)
            else:
                self.print_help('manage.py', sys.argv[2])
        except KeyboardInterrupt:
            return

    def _get_user(self, username:str):
        return User.objects.get(username=username, is_staff=False, is_superuser=False)

    def _get_client(self, clientname:str):
        return Client.objects.get(group__name=clientname)

    def _dict_to_message(self, dct):
        if dct is None:
            return

        max_key_width = max(len(str(key)) for key in dct.keys()) + 1

        for key, val in dct.items():
            key = key.replace('_', ' ').title() + ':'
            if val is None:
                val = self.style.WARNING('None')
            elif isinstance(val, bool):
                if val:
                    val = self.style.SUCCESS('True')
                else:
                    val = self.style.ERROR('False')
            elif isinstance(val, int):
                val = self.style.HTTP_SUCCESS(f'{val}')
            elif isinstance(val, datetime):
                val = self.style.SUCCESS(val.isoformat())
            elif isinstance(val, Group):
                val = _(f'{val.name} (id: {self.style.HTTP_SUCCESS(val.id)}') + self.style.SUCCESS(')')

            self._output_success(f'{key:{max_key_width}} {val}')

    def _display_client(self, client):
        info = model_to_dict(client, exclude='group')
        info.update({'group': client.group})
        self._output_success(self._dict_to_message(info))

    def _display_user(self, user, token):
        info = model_to_dict(user, exclude=['password'])
        if token:
            info.update({'Authorization': f'Token {token.key}'})

        self._output_success(self._dict_to_message(info))

    # Client handlers
    def _handle_client_create(self, options):
        clientname = options.get('clientname')
        email = options.get('email')

        try:
            with transaction.atomic():
                group = Group(name=clientname)
                client = Client(group=group)
                user = User(username=clientname, email=email, first_name='admin', last_name=clientname, is_superuser=False, is_staff=False, is_active=True)

                # Prompt for password and confirmation
                password = getpass.getpass(prompt=_('Enter admin user\'s password: '))
                password_confirm = getpass.getpass(prompt=_('Confirm admin user\'s password: '))

                if password != password_confirm:
                    self._output_err(_('Passwords do not match.'))
                    return

                # Set the password securely
                user.set_password(password)
                self._output_success(message=_(f'Creating client \'{clientname}\'.'))
                group.save()
                client.save()

                self._output_success(message=_(f'Creating client \'{clientname}\' admin user \'{user.username}\'.'))
                options['token'] = True
                user, token = self._set_user_data(clientname, user, options)

                user.groups.add(group)

                self._output_success('\n' + _(f'Client Admin User:'))
                self._display_user(user, token)
        except Exception as e:
            self._output_err(_(f'Failed to create client. Error occurred: {str(e).strip()}'))
            self._output_err(message=_(f'Rolling back changes.'))

    def _handle_client_read(self, options):
        clientname = options.get('clientname')

        if clientname is None:
            self._output_success(_(f'Clients: {", ".join([client.group.name for client in Client.objects.all()])}'))
        else:
            try:
                client = Client.objects.get(group__name=clientname)
                self._display_client(client)
            except Client.DoesNotExist:
                self._output_err(_(f'Client \'{clientname}\' does not exist.'))

    def _handle_client_update(self, options):
        clientname = options.get('clientname')

        try:
            with transaction.atomic():
                client = self._get_client(clientname=clientname)
                name = options.get('name')

                if name is not None:
                    client.group.name = name
                client.group.save()
                self._display_client(client)
        except Client.DoesNotExist:
            self._output_err(_(f'Client \'{clientname}\' does not exist.'))
        except Exception as e:
            self._output_err(_(f'Failed due to previous error: {str(e).strip()}'))

    # User handlers
    def _set_user_data(self, username, user, options):
        # Process updating name...
        name = options.get('name')
        if name is not None:
            self._output_success(_(f'Setting username of \'{username}\' to \'{name}\'.'))
            user.username = name

        # Process updating email address...
        email = options.get('email')
        if email is not None:
            self._output_success(_(f'Setting email address of user \'{username}\' to \'{email}\'.'))
            user.email = email

        # Process updating first name...
        first_name = options.get('first')
        if first_name is not None:
            if first_name == '\\blank':
                self._output_success(_(f'Setting first name of \'{username}\' to \'\'.'))
                user.first_name = ''
            else:
                self._output_success(_(f'Setting first name of \'{username}\' to \'{first_name}\'.'))
                user.first_name = first_name

        # Process updating first name...
        last_name = options.get('last')
        if last_name is not None:
            if last_name == '\\blank':
                self._output_success(_(f'Setting last name of \'{username}\' to \'\'.'))
                user.last_name = ''
            else:
                self._output_success(_(f'Setting last name of \'{username}\' to \'{last_name}\'.'))
                user.last_name = last_name

        # Process is_active update...
        is_active = options.get('is_active')
        if is_active is not None:
            self._output_success(_(f'Setting user \'{username}\' is_active to {is_active}.'))
            user.is_active = is_active

        # Process joining user to groups...
        groups = options.get('join')
        if groups:
            groups_to_join = [g.strip() for g in groups.split(',')]
            self._output_success(_(f'Joining user \'{username}\' to groups: {", ".join(groups_to_join)}'))
            for group_name in groups_to_join:
                group, created = Group.objects.get_or_create(name=group_name)
                if not Client.objects.filter(group=group).exists():
                    user.groups.add(group)
                else:
                    self._output(_(f'Cannot join user \'{username}\' to group \'{group_name}\': Group is referenced by a Client.'), func=self.style.WARNING)

        # Process revoking user from groups...
        groups = options.get('revoke')
        if groups:
            groups_to_revoke = [g.strip() for g in groups.split(',')]
            self._output_success(_(f'Revoking user \'{username}\' from groups: {", ".join(groups_to_revoke)}'))
            for group_name in groups_to_revoke:
                group = Group.objects.filter(name=group_name).first()
                if group:
                    if not Client.objects.filter(group=group).exists():
                        user.groups.remove(group)
                    else:
                        self._output(_(f'Cannot revoke user \'{username}\' from group \'{group_name}\': Group is referenced by a Client.'), func=self.style.WARNING)

        user.save()

        token = None
        gettoken = options.get('token')
        if gettoken is not None:
            if gettoken:
                token, created = Token.objects.get_or_create(user=user)
            else:
                try:
                    token = Token.objects.get(user=user)
                    if token is not None:
                        token.delete()
                except Token.DoesNotExist:
                    pass
        else:
            try:
                token = Token.objects.get(user=user)
            except Token.DoesNotExist:
                pass

        return user, token

    def _handle_user_create(self, options):
        username = options.get('username')
        clientname = options.get('clientname')

        try:
            with transaction.atomic():
                # Create the user with the provided username
                user = User(username=username)

                # Prompt for password and confirmation
                password = getpass.getpass(prompt=_('Enter password: '))
                password_confirm = getpass.getpass(prompt=_('Confirm password: '))

                if password != password_confirm:
                    self._output_err(_('Passwords do not match.'))
                    return

                # Set the password securely
                user.set_password(password)

                user, token = self._set_user_data(username=username, user=user, options=options)

                client = Client.objects.filter(group__name=clientname).first()
                if client:
                    user.groups.add(client.group)
                    self._output_success(_(f"User '{username}' has joined client '{clientname}'"))
                else:
                    self._output_err(_(f"Client with group name '{clientname}' does not exist."))

            self._display_user(user, token)
        except User.DoesNotExist:
            self._output_err(_(f'User \'{username}\' does not exist.'))
        except Exception as e:
            self._output_err(_(f'Failed due to previous error: {str(e).strip()}'))

    def _handle_user_read(self, options):
        username = options.get('username')
        clientname = options.get('clientname')

        client = None
        if clientname is not None:
            try:
                client = self._get_client(clientname=clientname)
            except:
                self._output_err(_(f'Client \'{clientname}\' does not exist.'))
                return

        if username is not None:
            try:
                user = self._get_user(username=username)
                if client and client.group not in user.groups.all():
                    self._output_err(_(f'User \'{username}\' for client \'{clientname}\' does not exist.'))
                    return
                try:
                    token = Token.objects.get(user=user)
                except Token.DoesNotExist:
                    token = None
                self._display_user(user, token)
            except:
                self._output_err(_(f'User \'{username}\' does not exist.'))
                return
        else:
            users = set()
            for user in User.objects.filter(is_superuser=False, is_staff=False):
                if client:
                    if client.group in user.groups.all():
                        users.add(user.username)
                else:
                    users.add(user.username)
            if client:
                self._output_success(_(f'Users for client \'{clientname}\': {", ".join(users)}'))
            else:
                self._output_success(_(f'Users: {", ".join(users)}'))

    def _handle_user_update(self, options):
        username = options.get('username')

        try:
            with transaction.atomic():
                user = self._get_user(username)

                # Check if the user is the admin for any client
                name = options.get('name')
                if name is not None:
                    client = self._get_client(clientname=username)
                    if client:
                        confirm = input(_('User is the Client admin of client \'%(clientname)s\'. Changing the name of the admin must change the name of the client. Would you like to proceed? (y/N): ') % ({'clientname': username})).lower()
                        if confirm == 'n':
                            self._output_success('Aborted.')
                            return

                        client.group.name = name
                        client.save()

                self._set_user_data(username=username, user=user, options=options)
        except User.DoesNotExist:
            self._output_err(_(f'User \'{username}\' does not exist.'))
        except Exception as e:
            self._output_err(_(f'Failed due to previous error: {str(e).strip()}'))

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

    def _output_success(self, message:str):
        self._output(message=message, pipe=self.stdout, func=self.style.SUCCESS)

    def _output_err(self, message:str):
        self._output(message=message, pipe=self.stderr, func=self.style.ERROR)

    @staticmethod
    def str_to_bool(value):
        """
        Helper conversion function to convert input parameter boolean values to a bool value (True or False).
        Returns:
            bool:   True if value (lowercase) is in ('true', 't', '1', 'yes', 'y'), False if value (lowercase) is in ('false', 'f', '0', 'no', 'n').
        Raises:
            ArgumentTypeError   If value is not in a valid format.
        """
        if value.lower() in ('true', 't', '1', 'yes', 'y'):
            return True
        elif value.lower() in ('false', 'f', '0', 'no', 'n'):
            return False
        else:
            raise ArgumentTypeError(f"Boolean value expected. Got '{value}'.")
