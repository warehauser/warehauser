import json

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext as _
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
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
            if output_json:
                response = {'error': _('User with username \'%s\' does not exist.') % user.username}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.ERROR(_('User with username \'%s\' does not exist.') % user.username))

        if create_token:
            if Token.objects.filter(user=user).exists():
                token = Token.objects.get(user=user)
                token.delete()
                if output_json:
                    response = {'message': _(f'Token deleted successfully for user {user.username}.')}
                    self.stdout.write(json.dumps(response, indent=4))
                else:
                    self.stdout.write(self.style.SUCCESS(_(f'Token deleted successfully for user {user.username}.')))
            else:
                if output_json:
                    response = {'message': _(f'No token user {user.username} found.')}
                    self.stdout.write(json.dumps(response, indent=4))
                else:
                    self.stdout.write(self.style.SUCCESS(_(f'No token user {user.username} found.')))
            return

        confirm = input(_('Are you sure you want to delete the user \'%s\'? (y/N): ') % username).lower()
        if confirm == 'y':
            self.delete_user(user, output_json)
        else:
            if output_json:
                response = {'message': 'Deletion cancelled.'}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.SUCCESS(_('Deletion cancelled.')))

    def delete_user(self, user, output_json=False):
        user.delete()
        if output_json:
            response = {'message': _('User \'%s\' deleted successfully.') % user.username}
            self.stdout.write(json.dumps(response, indent=4))
        else:
            self.stdout.write(self.style.SUCCESS(_('User \'%s\' deleted successfully.') % user.username))

    def create_user(self, username, password, email, group_names, create_token=False, output_json=False):
        if User.objects.filter(username=username).exists():
            if output_json:
                response = {'error': _('User with username \'%s\' already exists.') % username}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.ERROR(_('User with username \'%s\' already exists.') % username))
            return

        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()

        if create_token:
            token = Token.objects.create(user=user)
            if output_json:
                response = {'message': _('Token created successfully for user \'%s\': %s') % (username, token.key)}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.SUCCESS(_('Token created successfully for user \'%s\': %s') % (username, token.key)))
        else:
            if output_json:
                response = {'message': _('User \'%s\' created successfully.') % username}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.SUCCESS(_('User \'%s\' created successfully.') % username))

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
                if output_json:
                    response = {'message': _('Password for user \'%s\' updated successfully.') % username}
                    self.stdout.write(json.dumps(response, indent=4))
                else:
                    self.stdout.write(self.style.SUCCESS(_('Password for user \'%s\' updated successfully.') % username))

            if email:
                user.email = email

                if output_json:
                    response = {'message': _('Email for user \'%s\' updated successfully.') % username}
                    self.stdout.write(json.dumps(response, indent=4))
                else:
                    self.stdout.write(self.style.SUCCESS(_('Email for user \'%s\' updated successfully.') % username))

            if active is not None:
                user.is_active = active.lower() == 'true'
                if output_json:
                    response = {'message': _('Active status for user \'%s\' set to %s.') % (username, active)}
                    self.stdout.write(json.dumps(response, indent=4))
                else:
                    self.stdout.write(self.style.SUCCESS(_('Active status for user \'%s\' set to %s.') % (username, active)))

            user.save()

            if create_token:
                token, created = Token.objects.get_or_create(user=user)
                if created:
                    if output_json:
                        response = {'message': _('Token created successfully for user \'%s\': %s') % (username, token.key)}
                        self.stdout.write(json.dumps(response, indent=4))
                    else:
                        self.stdout.write(self.style.SUCCESS(_('Token created successfully for user \'%s\': %s') % (username, token.key)))
                else:
                    if output_json:
                        response = {'message': _('Token already exists for user \'%s\': %s') % (username, token.key)}
                        self.stdout.write(json.dumps(response, indent=4))
                    else:
                        self.stdout.write(self.style.SUCCESS(_('Token already exists for user \'%s\': %s') % (username, token.key)))

            if group_names:
                groups = [group.strip() for group in group_names.split(',')]
                for group_name in groups:
                    group, created = Group.objects.get_or_create(name=group_name)
                    if remove:
                        user.groups.remove(group)
                        if output_json:
                            response = {'message': _('Removed user \'%s\' from group \'%s\'.') % (username, group_name)}
                            self.stdout.write(json.dumps(response, indent=4))
                        else:
                            self.stdout.write(self.style.SUCCESS(_('Removed user \'%s\' from group \'%s\'.') % (username, group_name)))
                    else:
                        user.groups.add(group)
                        if output_json:
                            response = {'message': _('Added user \'%s\' to group \'%s\'.') % (username, group_name)}
                            self.stdout.write(json.dumps(response, indent=4))
                        else:
                            self.stdout.write(self.style.SUCCESS(_('Added user \'%s\' to group \'%s\'.') % (username, group_name)))

            self.show_user_info(username, output_json)

        except User.DoesNotExist:
            if output_json:
                response = {'error': _('User with username \'%s\' does not exist.') % username}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.ERROR(_('User with username \'%s\' does not exist.') % username))
        except Group.DoesNotExist:
            if output_json:
                response = {'error': _('Group with name \'%s\' does not exist.') % group_name}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.ERROR(_('Group with name \'%s\' does not exist.') % group_name))

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
            if output_json:
                response = {'error': _('User with username \'%s\' does not exist.') % username}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.ERROR(_('User with username \'%s\' does not exist.') % username))
        except Token.DoesNotExist:
            if output_json:
                response = {'error': _('Token for user \'%s\' does not exist.') % username}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.ERROR(_('Token for user \'%s\' does not exist.') % username))
