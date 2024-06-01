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

# client.py

import json

from django.core.management.base import BaseCommand#, CommandError
from django.contrib.auth.models import Group, User
from django.utils.translation import gettext as _
# from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = _('Manage clients (groups starting with "client_*")')

    def add_arguments(self, parser):
        parser.add_argument('client', type=str, nargs='?', help=_('The name of the client to manage (without the "client_" prefix)'))
        parser.add_argument('-u', '--users', type=str, help=_('Comma-separated list of existing usernames to add or remove'))
        parser.add_argument('-r', '--remove', action='store_true', help=_('Remove the specified users from the client'))
        parser.add_argument('-d', '--delete', action='store_true', help=_('Delete the client'))
        parser.add_argument('-j', '--json', action='store_true', help=_('Output in JSON format'))

    def handle(self, *args, **kwargs):
        client_name = kwargs.get('client')
        users = kwargs.get('users')
        remove = kwargs.get('remove')
        delete = kwargs.get('delete')
        output_json = kwargs.get('json')

        if not client_name:
            self.list_clients(output_json)
        elif delete:
            self.confirm_and_delete_client(client_name, output_json)
        elif users:
            self.modify_client_users(client_name, users, remove, output_json)
        else:
            self.create_or_show_client_info(client_name, output_json)

    def list_clients(self, output_json=False):
        clients = Group.objects.filter(name__startswith='client_').values_list('name', flat=True)
        client_names = [client_name.split('client_')[1] for client_name in clients]
        if output_json:
            response = {'clients': client_names}
            self.stdout.write(json.dumps(response, indent=4))
        else:
            self.stdout.write(self.style.SUCCESS(', '.join(client_names)))

    def confirm_and_delete_client(self, client_name, output_json=False):
        try:
            group = Group.objects.get(name=f'client_{client_name}')
            if group.user_set.exists():
                if output_json:
                    response = {'error': _('Client has members and cannot be deleted.')}
                    self.stdout.write(json.dumps(response, indent=4))
                else:
                    self.stdout.write(self.style.ERROR(_('Client has members and cannot be deleted.')))
            else:
                group.delete()
                if output_json:
                    response = {'message': _('Client \'%s\' deleted successfully.') % client_name}
                    self.stdout.write(json.dumps(response, indent=4))
                else:
                    self.stdout.write(self.style.SUCCESS(_('Client \'%s\' deleted successfully.') % client_name))
        except Group.DoesNotExist:
            if output_json:
                response = {'error': _('Client \'%s\' does not exist.') % client_name}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.ERROR(_('Client \'%s\' does not exist.') % client_name))

    def delete_client(self, client_name, output_json=False):
        try:
            group = Group.objects.get(name=f'client_{client_name}')
            group.delete()
            if output_json:
                response = {'message': _('Client \'%s\' deleted successfully.') % client_name}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.SUCCESS(_('Client \'%s\' deleted successfully.') % client_name))
        except Group.DoesNotExist:
            if output_json:
                response = {'error': _('Client \'%s\' does not exist.') % client_name}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.ERROR(_('Client \'%s\' does not exist.') % client_name))

    def create_or_show_client_info(self, client_name, output_json=False):
        try:
            group = Group.objects.get(name=f'client_{client_name}')
            users = group.user_set.all().values_list('username', flat=True)
            if output_json:
                response = {'client': client_name, 'members': list(users)}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.SUCCESS(_('Client \'%s\' members: %s') % (client_name, ', '.join(users))))
        except Group.DoesNotExist:
            self.create_client(client_name, output_json)

    def create_client(self, client_name, output_json=False):
        group = Group.objects.create(name=f'client_{client_name}')
        if output_json:
            response = {'message': _('Client \'%s\' created successfully.') % client_name}
            self.stdout.write(json.dumps(response, indent=4))
        else:
            self.stdout.write(self.style.SUCCESS(_('Client \'%s\' created successfully.') % client_name))

    def modify_client_users(self, client_name, usernames, remove, output_json=False):
        try:
            group = Group.objects.get(name=f'client_{client_name}')
            usernames_list = [username.strip() for username in usernames.split(',')]
            for username in usernames_list:
                try:
                    user = User.objects.get(username=username)
                    if remove:
                        user.groups.remove(group)
                        if output_json:
                            response = {'message': _('Removed user \'%s\' from client \'%s\'.') % (username, client_name)}
                            self.stdout.write(json.dumps(response, indent=4))
                        else:
                            self.stdout.write(self.style.SUCCESS(_('Removed user \'%s\' from client \'%s\'.') % (username, client_name)))
                    else:
                        if not user.groups.exists():
                            user.groups.add(group)
                            if output_json:
                                response = {'message': _('Added user \'%s\' to client \'%s\'.') % (username, client_name)}
                                self.stdout.write(json.dumps(response, indent=4))
                            else:
                                self.stdout.write(self.style.SUCCESS(_('Added user \'%s\' to client \'%s\'.') % (username, client_name)))
                        else:
                            if output_json:
                                response = {'error': _('User \'%s\' is already a member of another client.') % username}
                                self.stdout.write(json.dumps(response, indent=4))
                            else:
                                self.stdout.write(self.style.ERROR(_('User \'%s\' is already a member of another client.') % username))
                except User.DoesNotExist:
                    if output_json:
                        response = {'error': _('User with username \'%s\' does not exist.') % username}
                        self.stdout.write(json.dumps(response, indent=4))
                    else:
                        self.stdout.write(self.style.ERROR(_('User with username \'%s\' does not exist.') % username))
        except Group.DoesNotExist:
            if output_json:
                response = {'error': _('Client \'%s\' does not exist.') % client_name}
                self.stdout.write(json.dumps(response, indent=4))
            else:
                self.stdout.write(self.style.ERROR(_('Client \'%s\' does not exist.') % client_name))
