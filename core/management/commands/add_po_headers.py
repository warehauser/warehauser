import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Add headers to .po files in the locale directory'

    def handle(self, *args, **options):
        locale_dir = getattr(settings, 'LOCALE_PATHS', [])[0]
        if not locale_dir:
            self.stdout.write(self.style.ERROR('LOCALE_PATHS setting is not configured properly.'))
            return

        header = '''msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: {lang}\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"
'''

        for root, dirs, files in os.walk(locale_dir):
            for file in files:
                if file.endswith('.po'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r+', encoding='utf-8') as f:
                        content = f.read()
                        if not content.startswith('msgid ""\nmsgstr ""'):
                            lang = os.path.basename(root)
                            f.seek(0)
                            f.write(header.format(lang=lang) + content)
                            self.stdout.write(self.style.SUCCESS(f'Added header to {file_path}'))
                        else:
                            self.stdout.write(self.style.NOTICE(f'Header already present in {file_path}'))

        self.stdout.write(self.style.SUCCESS('Finished processing .po files.'))
