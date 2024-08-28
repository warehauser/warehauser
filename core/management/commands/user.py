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

# user.py

import json
import getpass

from datetime import datetime
from typing import Callable

from django.contrib.auth import authenticate
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import models
from django.forms.models import model_to_dict
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext as _

from ...models import Client

class WarehauserJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None:
            return 'None'
        if isinstance(obj, datetime):
            return obj.isoformat()  # Converts to ISO 8601 format string
        if isinstance(obj, User):
            return model_to_dict(obj, exclude=['password'])
        if isinstance(obj, models.Model):
            return model_to_dict(obj)
        return super().default(obj)

class Command(BaseCommand):
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

    help = _('Manage user info, create a new user, and add/remove groups from a user.')

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['create', 'c', 'read', 'r', 'update', 'u', 'delete', 'd',], help=_('Action to perform. c means create, r means read, u means update, d means delete.'))
        parser.add_argument('username', type=str, nargs='?', help=_('The username of the user to manage'))
        # parser.add_argument('-s', '--superuser', type=str, nargs='?', help=_('The username of the superuser'))
        parser.add_argument('-a', '--add', type=str, help=_('Comma-separated list of groups to join for the user'))
        parser.add_argument('-d', '--delete', action='store_true', help=_('Delete the user'))
        parser.add_argument('-e', '--email', type=str, help=_('Email address for the new user or to update an existing user'))
        parser.add_argument('-f', '--first', type=str, help=_('First name for the new user or to update an existing user'))
        parser.add_argument('-l', '--last', type=str, help=_('Last name for the new user or to update an existing user'))
        parser.add_argument('-p', '--password', type=str, help=_('Password for the new user or to update an existing user'))
        parser.add_argument('-r', '--remove', action='store_true', help=_('Comma-separated list of groups to leave for the user'))
        parser.add_argument('-A', '--active', type=str, help=_('Set user active status: "true" to activate, "false" to deactivate'))
        parser.add_argument('-t', '--token', action='store_true', help=_('Create (if it does not already exist) Auth Token for user and display Auth Token, incompatible with -R flag'))
        parser.add_argument('-R', '--revoke', action='store_true', help=_('Delete (if it exist) Auth Token for user, incompatible with -t flag'))

    def _get_user(self, username):
        user = User.objects.get(username=username, is_superuser=False, is_staff=False)
        return user

    def handle_create(self, **kwargs):
        self._output_success(_('Create User'))
        username = kwargs.get('username')
        pass

    def handle_read(self, **kwargs):
        self._output_success(_('Read User'))
        username = kwargs.get('username')

        if username is None:
            users = User.objects.filter(is_superuser=False, is_staff=False).values_list('username', flat=True)
            self._output_success(', '.join(users))
        else:
            try:
                user = self._get_user(username=username)
                token = Token.objects.get(user=user).key if Token.objects.filter(user=user).exists() else None
                # if token is None:
                #     token, created = Token.objects.get_or_create(user=user)

                # Get all groups of the user
                user_groups = user.groups.all()

                # Get all client groups
                client_groups = Client.objects.values_list('group', flat=True)

                user_info = {
                    _('id'): user.id,
                    _('username'): user.username,
                    _('email'): user.email,
                    _('first_name'): user.first_name,
                    _('last_name'): user.last_name,
                    _('is_active'): user.is_active,
                    _('is_superuser'): user.is_superuser,
                    _('is_staff'): user.is_staff,
                    _('last_login'): user.last_login.isoformat() if user.last_login else None,
                    _('date_joined'): user.date_joined.isoformat() if user.date_joined else None,
                    _('groups'): ', '.join(
                        _(f'{group.name} (client group)') if group.id in client_groups else group.name
                        for group in user_groups
                    ),
                    _('auth_token'): token,
                }

                for key, value in user_info.items():
                    prompt = key.replace('_', ' ').title()
                    prompt = self.style.SUCCESS(f'{prompt}:'.ljust(14))
                    if isinstance(value, bool) and not value:
                        value = self.style.ERROR(f'{value}')
                    elif value is None:
                        value = self.style.HTTP_INFO(f'{value}')
                    else:
                        value = self.style.SUCCESS(f'{value}')
                    self.stdout.write(f'{prompt}{value}')
            except User.DoesNotExist:
                message = _('User with username \'%(username)s\' does not exist.') % ({'username': username})
                self._output_err(message=message)
            except Token.DoesNotExist:
                message = _('Token for user \'%(username)s\' does not exist.') % ({'username': username})
                self._output_err(message=message)

    def handle_update(self, **kwargs):
        self._output_success(_('Update User'))

        username = kwargs.get('username')
        try:
            if username is None:
                raise User.DoesNotExist()
            user = self._get_user(username=username)

            flag_token = kwargs.get('token')
            flag_revoke = kwargs.get('revoke')

            if flag_token and flag_revoke:
                message = _(f'Flags -t|--token and -R|--revoke are mutually exclusive.')
                self._output_err(message=message)
                return
            elif flag_token:
                token, created = Token.objects.get_or_create(user=user)
            elif flag_revoke:
                token = Token.objects.get(user=user) if Token.objects.filter(user=user).exists() else None
                if token is not None:
                    token.delete()
                    token = None








            self._output_success(flag_token)
            self._output_success(flag_revoke)
        except User.DoesNotExist:
            message = _('User with username \'%(username)s\' does not exist.') % ({'username': username})
            self._output_err(message=message)
        pass

    def handle_delete(self, **kwargs):
        self._output_success(_('Delete User'))

        username = kwargs.get('username')
        if username is None:
            self._output_err(_('Delete action requires a username. Use -h flag for help.'))
            return

        try:
            user = self._get_user(username=username)
        except User.DoesNotExist:
            self._output_err(_(f'No client user with username \'{username}\' found.'))
            return

        confirm = input(_('Are you sure you want to delete the user \'%(username)s\'? (y/N): ') % ({'username': user.username})).lower()
        if confirm == 'y':
            token = Token.objects.get(user=user)
            token.delete()

            user.delete()
            message = _('User \'%(username)s\' deleted successfully.') % ({'username': user.username})
            self._output_success(message=message)
        else:
            self._output_success(message='Deletion cancelled.')

    def handle(self, *args, **kwargs):
        action = kwargs.pop('action')
        # superuser_username = kwargs.pop('superuser')
        # password = kwargs.get('password')
        # email = kwargs.get('email')
        # groups = kwargs.get('groups')
        # remove = kwargs.get('remove')
        # delete = kwargs.get('delete')
        # active = kwargs.get('active')
        # create_token = kwargs.get('token')

        # if not superuser_username:
        #     superuser_username = input(_('Enter superuser username: '))

        # superuser_password = getpass.getpass(_('Enter superuser password: '))

        # superuser = authenticate(username=superuser_username, password=superuser_password)

        # if superuser is None or not superuser.is_superuser:
        #     self._output_err(_('Invalid superuser credentials'))
        #     return

        if action in ['create', 'c']:
            self.handle_create(**kwargs)
        elif action in ['read', 'r']:
            self.handle_read(**kwargs)
        elif action in ['update', 'u']:
            self.handle_update(**kwargs)
        elif action in ['delete', 'd']:
            self.handle_delete(**kwargs)
        else:
            raise BaseException(_(f'Action {action} is not implemented.'))

        return
        if not username:
            self.list_users(jsn)
        else:
            user = User.objects.filter(username=username)
            if user is None:
                # attempt to create user
                self.create_user(username, email, groups, jsn)
            else:
                if delete:
                    self.confirm_and_delete_user(user, jsn)
                elif password or email or groups or active is not None:
                    self.modify_user(username, password, email, groups, remove, active, create_token, jsn)
                else:
                    self.show_user_info(username, jsn)

    def list_users(self, output_json=False):
        users = User.objects.filter(is_superuser=False, is_staff=False).values_list('username', flat=True)
        if output_json:
            users_json = {'users': list(users)}
            self.stdout.write(json.dumps(users_json, indent=4))
        else:
            self.stdout.write(self.style.SUCCESS(', '.join(users)))

    def confirm_and_delete_user(self, user, output_json=False):
        confirm = input(_('Are you sure you want to delete the user \'%(username)s\'? (y/N): ') % ({'username': user.username})).lower()
        if confirm == 'y':
            token = Token.objects.get(user=user)
            token.delete()

            user.delete()
            message = _('User \'%(username)s\' deleted successfully.') % ({'username': user.username})
            self._output(message=message, json=output_json)
        else:
            self._output(message='Deletion cancelled.', json=output_json)

    def create_user(self, username, password, email, group_names, create_token=False, output_json=False):
        if User.objects.filter(username=username).exists():
            message = _('User with username \'%(username)s\' already exists.') % ({'username': username})
            self._output(message=message, json=output_json, key='error', func=self.style.ERROR)
            return

        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()

        if create_token:
            token = Token.objects.create(user=user)
            message = _('User \'%(username)s\' created successfully. Token created successfully: %(token)s') % ({'username': username, 'token': token.key})
            self._output(message=message, json=output_json)
        else:
            message = _('User \'%(username)s\' created successfully.') % ({'username': user.username})
            self._output(message=message, json=output_json)

        if group_names:
            groups = [group.strip() for group in group_names.split(',')]
            for group_name in groups:
                group, created = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)

    def modify_user(self, username, password, email, group_names, remove, active, create_token=False, output_json=False):
        try:
            user = User.objects.get(username=username)
            if password:
                user.set_password(password)
                message = _('Password for user \'%(username)s\' updated successfully.') % ({'username': username})
                self._output(message=message, json=output_json)

            if email:
                user.email = email

                message = _('Email for user \'%(username)s\' updated successfully.') % ({'username': username})
                self._output(message=message, json=output_json)

            if active is not None:
                user.is_active = active.lower() == 'true'
                message = _('Active status for user \'%(username)s\' set to %(active)s.') % {'username': username, 'active': active}
                self._output(message=message, json=output_json)

            user.save()

            if create_token:
                token, created = Token.objects.get_or_create(user=user)
                if created:
                    message = _('Token created successfully for user \'%(username)s\': %(token)s') % ({'username': username, 'token': token.key})
                    self._output(message=message, json=output_json)
                else:
                    message = _('Token for user \'%(username)s\': %(token)s') % ({'username': username, 'token': token.key})
                    self._output(message=message, json=output_json)

            if group_names:
                groups = [group.strip() for group in group_names.split(',')]
                for group_name in groups:
                    group, created = Group.objects.get_or_create(name=group_name)
                    if remove:
                        user.groups.remove(group)
                        message = _('Removed user \'%(username)s\' from group \'%(group_name)s\'.') % ({'username': username, 'group_name': group_name})
                        self._output(message=message, json=output_json)
                    else:
                        user.groups.add(group)
                        message = _('Added user \'%(username)s\' to group \'%(group_name)s\'.') % ({'username': username, 'group_name': group_name})
                        self._output(message=message, json=output_json)

            self.show_user_info(username, output_json)

        except User.DoesNotExist:
            if output_json:
                message = _('User with username \'%(username)s\' does not exist.') % ({'username': username})
                self._output(message=message, json=output_json, key='error', func=self.style.ERROR)
        except Group.DoesNotExist:
                message = _('Group with name \'%(group_name)s\' does not exist.') % {'group_name': group_name}
                self._output(message=message, json=output_json, key='error', func=self.style.ERROR)

    def show_user_info(self, username, output_json=False):
        try:
            user = User.objects.get(username=username)
            token = Token.objects.get(user=user).key if Token.objects.filter(user=user).exists() else None
            if token is None:
                token, created = Token.objects.get_or_create(user=user)

            # Get all groups of the user
            user_groups = user.groups.all()

            # Get all client groups
            client_groups = Client.objects.values_list('group', flat=True)

            user_info = {
                _('id'): user.id,
                _('username'): user.username,
                _('email'): user.email,
                _('first_name'): user.first_name,
                _('last_name'): user.last_name,
                _('is_active'): user.is_active,
                _('is_superuser'): user.is_superuser,
                _('is_staff'): user.is_staff,
                _('last_login'): user.last_login.isoformat() if user.last_login else None,
                _('date_joined'): user.date_joined.isoformat() if user.date_joined else None,
                _('groups'): ', '.join(
                    _(f'{group.name} (client group)') if group.id in client_groups else group.name
                    for group in user_groups
                ),
                _('auth_token'): token,
            }

            if output_json:
                self.stdout.write(json.dumps(user_info, indent=4))
            else:
                for key, value in user_info.items():
                    prompt = key.replace('_', ' ').title()
                    prompt = self.style.SUCCESS(f'{prompt}:'.ljust(14))
                    if isinstance(value, bool) and not value:
                        value = self.style.ERROR(f'{value}')
                    elif value is None:
                        value = self.style.HTTP_INFO(f'{value}')
                    else:
                        value = self.style.SUCCESS(f'{value}')
                    self.stdout.write(f'{prompt}{value}')
        except User.DoesNotExist:
            message = _('User with username \'%(username)s\' does not exist.') % ({'username': username})
            self._output(message=message, json=output_json, key='error', func=self.style.ERROR)
        except Token.DoesNotExist:
            message = _('Token for user \'%(username)s\' does not exist.') % ({'username': username})
            self._output(message=message, json=output_json, key='error', func=self.style.ERROR)
