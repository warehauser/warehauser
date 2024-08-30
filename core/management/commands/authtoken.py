# myapp/management/commands/authtoken.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _

class Command(BaseCommand):
    help = _('Get, create, or delete an auth token for a user.')

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help=_('Username of the user to get the token for.'))
        parser.add_argument('-d', '--delete', action='store_true', help=_('Delete the auth token if it exists.'))
        parser.add_argument('-c', '--create', action='store_true', help=_('Create the auth token if it does not already exist.'))

    def handle(self, *args, **options):
        username = options.get('username')
        delete = options.get('delete')
        create = options.get('create')

        try:
            user = User.objects.get(username=username)
            if delete:
                token = Token.objects.filter(user=user).first()
                if token:
                    token.delete()
                    self.stdout.write(self.style.SUCCESS(_('Token deleted successfully.')))
                else:
                    self.stdout.write(self.style.ERROR(_('No token exists for this user.')))
            else:
                if create:
                    token, created = Token.objects.get_or_create(user=user)
                else:
                    try:
                        token = Token.objects.get(user=user)
                    except Token.DoesNotExist:
                        self.stderr.write(self.style.ERROR(_(f'Token for user \'{username}\' not found.')))
                        return
                self.stdout.write(self.style.SUCCESS(f'Authorization: Token {token.key}'))
        except ObjectDoesNotExist:
            self.stdout.write(self.style.ERROR(_('User does not exist.')))
