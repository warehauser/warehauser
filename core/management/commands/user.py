import json
from typing import Callable

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext as _

class Command(BaseCommand):
    def _output(self, message:str, json:bool = False, key:str = 'message', func:Callable[[str], str] = None):
        # Provide a default function if none is provided
        if func is None:
            func = self.style.SUCCESS

        if json:
            # Handle JSON output
            self.stdout.write(json.dumps({key:message}, indent=4))
        else:
            # Handle standard output
            self.stdout.write(func(message))

    help = _('Manage user info, create a new user, and add/remove groups from a user.')

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, nargs='?', help=_('The username of the user to manage'))
        parser.add_argument('-p', '--password', type=str, help=_('Password for the new user or to update an existing user'))
        parser.add_argument('-e', '--email', type=str, help=_('Email address for the new user or to update an existing user'))
        parser.add_argument('-g', '--groups', type=str, help=_('Comma-separated list of groups to add or remove'))
        parser.add_argument('-r', '--remove', action='store_true', help=_('Remove the specified groups from the user'))
        parser.add_argument('-d', '--delete', action='store_true', help=_('Delete the user'))
        parser.add_argument('-a', '--active', type=str, help=_('Set user active status: "true" to activate, "false" to deactivate'))
        parser.add_argument('-t', '--token', action='store_true', help=_('Create auth token if user does not exist or display existing token'))
        parser.add_argument('-j', '--json', action='store_true', help=_('Output in JSON format'))

    def handle(self, *args, **kwargs):
        username = kwargs.get('username')
        password = kwargs.get('password')
        email = kwargs.get('email')
        groups = kwargs.get('groups')
        remove = kwargs.get('remove')
        delete = kwargs.get('delete')
        active = kwargs.get('active')
        create_token = kwargs.get('token')
        output_json = kwargs.get('json')

        if not username:
            self.list_users(output_json)
        elif delete:
            self.confirm_and_delete_user(username, create_token, output_json)
        elif password and email:
            self.create_user(username, password, email, groups, create_token, output_json)
        elif password or email or groups or active is not None:
            self.modify_user(username, password, email, groups, remove, active, create_token, output_json)
        else:
            self.show_user_info(username, create_token, output_json)

    def list_users(self, output_json=False):
        users = User.objects.all().values_list('username', flat=True)
        if output_json:
            users_json = {'users': list(users)}
            self.stdout.write(json.dumps(users_json, indent=4))
        else:
            self.stdout.write(self.style.SUCCESS(', '.join(users)))

    def confirm_and_delete_user(self, username, create_token, output_json=False):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            message = _('User with username \'%(username)s\' does not exist.') % ({'username': user.username})
            self._output(message=message, json=output_json, key='error', func=self.style.ERROR)
            return

        if create_token:
            if Token.objects.filter(user=user).exists():
                token = Token.objects.get(user=user)
                token.delete()
                message = _('Token deleted successfully for user \'%(username)s\'.' % ({'username': user.username}))
                self._output(message=message, json=output_json)
            else:
                message = _('No token for user \'%(username)s\' found.' % ({'username': user.username}))
                self._output(message=message, json=output_json)
            return

        confirm = input(_('Are you sure you want to delete the user \'%(username)s\'? (y/N): ') % ({'username': user.username})).lower()
        if confirm == 'y':
            self.delete_user(user, output_json)
        else:
            self._output(message='Deletion cancelled.', json=output_json)

    def delete_user(self, user, output_json=False):
        user.delete()
        message = _('User \'%(username)s\' deleted successfully.') % ({'username': user.username})
        self._output(message=message, json=output_json)

    def create_user(self, username, password, email, group_names, create_token=False, output_json=False):
        if User.objects.filter(username=username).exists():
            message = _('User with username \'%(username)s\' already exists.') % ({'username': username})
            self._output(message=message, json=output_json, key='error', func=self.style.ERROR)
            return

        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()

        if create_token:
            token = Token.objects.create(user=user)
            message = _('Token created successfully for user \'%(username)s\': %(token)s') % ({'username': username, 'token': token.key})
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

    def show_user_info(self, username, create_token, output_json=False):
        try:
            user = User.objects.get(username=username)
            token = Token.objects.get(user=user).key if Token.objects.filter(user=user).exists() else None
            if create_token:
                if token is None:
                    token, created = Token.objects.get_or_create(user=user)
                user_info = {'username': user.username, 'auth_token': token}
            else:
                user_info = {
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active,
                    'is_superuser': user.is_superuser,
                    'is_staff': user.is_staff,
                    'last_login': user.last_login,
                    'auth_token': token,
                    'groups': ', '.join(group.name for group in user.groups.all()),
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
