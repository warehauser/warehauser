
from django.core.management.base import BaseCommand, CommandParser
from django.utils.translation import gettext as _

# I want to customise the -h help printout functionality.
# If the user says manage.py cmd -h then I want to print the Command's help. But if the user says manage.py cmd create -h I want to print the CreateCommand help. How do I do this?
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('action', choices=['create', 'c', 'read', 'r', 'update', 'u', 'delete', 'd'], help=_('Action to perform. c means create, r means read, u means update, d means delete.'))
        parser.add_argument('args', type=str, nargs='+', help='One or more arguments to process')

    def handle(self, *args, **options):
        action = options['action']

        if action == 'c' or action == 'create':
            subcommand = self.CreateCommand()
        elif action == 'r' or action == 'read':
            subcommand = self.ReadCommand()
        elif action == 'u' or action == 'update':
            subcommand = self.UpdateCommand()
        elif action == 'd' or action == 'delete':
            subcommand = self.DeleteCommand()

        subcommand.style  = self.style
        subcommand.stdout = self.stdout
        subcommand.stderr = self.stderr

        subcommand.handle(*args, **options)
        subcommand.execute(*args, **options)

    class CreateCommand(BaseCommand):
        def add_arguments(self, parser):
            parser.add_argument('action', choices=['create', 'c'], help=_('Action to perform. Create a new user.'))
            parser.add_argument('username', type=str, nargs='?', help=_('The username of the user to manage.'))

        def handle(self, *args, **options):
            pass

    class ReadCommand(BaseCommand):
        def add_arguments(self, parser):
            parser.add_argument('action', choices=['read', 'r'], help=_('Action to perform. Display information about an existing user.'))
            parser.add_argument('username', type=str, nargs='?', help=_('The username of the user to manage.'))

        def handle(self, *args, **options):
            print(options['args'])
            # self.print_help('manage.py', self.__module__.split('.')[-1])

    class UpdateCommand(BaseCommand):
        def add_arguments(self, parser):
            parser.add_argument('action', choices=['update', 'u'], help=_('Action to perform. Update an existing user.'))
            parser.add_argument('username', type=str, nargs='?', help=_('The username of the user to manage.'))

        def handle(self, *args, **options):
            pass

    class DeleteCommand(BaseCommand):
        def add_arguments(self, parser):
            parser.add_argument('action', choices=['delete', 'd'], help=_('Action to perform. Delete an existing user.'))
            parser.add_argument('username', type=str, nargs='?', help=_('The username of the user to manage.'))

        def handle(self, *args, **options):
            pass
