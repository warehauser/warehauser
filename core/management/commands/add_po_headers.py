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

# add_po_headers.py

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
