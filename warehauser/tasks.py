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

# tasks.py

import logging
import threading

from db_mutex import DBMutexError, DBMutexTimeoutError
from db_mutex.db_mutex import db_mutex
from urllib.parse import urljoin

from django.db.models import ProtectedError, Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.urls import reverse

from datetime import timedelta

from core.models import *
from core.views  import *

class WarehauserThread(threading.Thread):
    def run(self):
        logging.info(f"[{self}]: {_('Started.')}")
        self.process()
        logging.info(f"[{self}]: {_('Finished.')}")

    def __str__(self):
        return f"{_('Task')} {self.__module__}.{self.__class__.__name__}(id={self.ident})"

    def process(self):
        pass

class ArchiverThread(WarehauserThread):
    def _archive_useraux(self):
        key = 'send_mail'
        delta = timezone.now() - timedelta(hours=24)

        objects = UserAux.objects.filter(
            Q(options__has_key='send_mail') &
            Q(options__send_mail__has_key='dt') &
            Q(options__send_mail__dt__lt=f'{delta}') &
            Q(options__send_mail__has_key='emailthread')
        )

        for useraux in objects:
            del useraux.options[key]
            useraux.save()

    def process(self):
        try:
            with db_mutex(f'archiver'):
                self._archive_useraux()
        except DBMutexError as e:
            raise WarehauserError(_('Unable to secure mutex for eventqueue.'), WarehauserErrorCodes.MUTEX_ERROR, {_('error'): e})
        except DBMutexTimeoutError as e:
            raise WarehauserError(_('Unable to secure mutex for eventqueue.'), WarehauserErrorCodes.MUTEX_TIMEOUT_ERROR, {_('error'): e})

class GenerateReportsThread(WarehauserThread):
    def process(self):
        pass

class EventProcessThread(threading.Thread):
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}(id={self.ident})"

    def run(self):
        logging.info(f"[{self}]: {_('Started.')}")
        try:
            with db_mutex(f'event:{self.event.id}'):
                logging.info(_(f'[{self}]: Processing {self.event}.'))
                self.event.process()
        except DBMutexError as e:
            raise WarehauserError(_('Unable to secure mutex for eventqueue.'), WarehauserErrorCodes.MUTEX_ERROR, {_('error'): e})
        except DBMutexTimeoutError as e:
            raise WarehauserError(_('Unable to secure mutex for eventqueue.'), WarehauserErrorCodes.MUTEX_TIMEOUT_ERROR, {_('error'): e})

class EventQueueThread(WarehauserThread):
    def process(self):
        try:
            with db_mutex(f'eventqueue'):
                batched_events = Event.objects.filter(is_batched=True, status=STATUS_OPEN)
                for event in batched_events:
                    EventProcessThread(event).start()
        except DBMutexError as e:
            raise WarehauserError(_('Unable to secure mutex for eventqueue.'), WarehauserErrorCodes.MUTEX_ERROR, {_('error'): e})
        except DBMutexTimeoutError as e:
            raise WarehauserError(_('Unable to secure mutex for eventqueue.'), WarehauserErrorCodes.MUTEX_TIMEOUT_ERROR, {_('error'): e})

class GarbageCollectorThread(WarehauserThread):
    def _collect(self, models):
        for model in models:
            try:
                model.log(level=logging.INFO, msg=_(f'Garbage collecting {model.__class__.__name__}({model.id})'))
                model.delete()
            except ProtectedError as e:
                model.log(level=logging.ERROR, msg=f'Unable to delete {model} as it is referenced by other object(s).\n{e}')

    def process(self):
        try:
            with db_mutex(f'garbagecollector'):
                self._collect(Event.objects.filter(is_virtual=True, status=STATUS_DESTROY))
                self._collect(Warehause.objects.filter(is_virtual=True, status=STATUS_DESTROY))
                self._collect(Product.objects.filter(is_virtual=True, status=STATUS_DESTROY))
        except DBMutexError as e:
            raise WarehauserError(_('Unable to secure mutex for garbagecollector.'), WarehauserErrorCodes.MUTEX_ERROR, {_('error'): e})
        except DBMutexTimeoutError as e:
            raise WarehauserError(_('Unable to secure mutex for garbagecollector.'), WarehauserErrorCodes.MUTEX_TIMEOUT_ERROR, {_('error'): e})

import json
class EmailThread(WarehauserThread):
    def _send_password_change_emails(self):
        auxs = UserAux.objects.filter(
            Q(options__contains={'otp': {'codes': {}}}) &  # Check for existence of 'otp' and 'codes' keys
            ~Q(options__otp__codes={})  # Exclude empty 'codes' dictionary
        )

        for aux in auxs:
            # print(json.dumps(aux.options['otp']['codes'], indent=3))
            for otp, data in aux.options['otp']['codes'].items():
                if int(data['status']) > 0:
                    continue

                logging.info(msg=f'Processing {aux.user.username} email sending.')

                data['status'] = 1
                aux.save()

                to_address = aux.user.email
                server_address = settings.EMAIL_WAREHAUSER_HOST
                revoke_url = reverse('auth_otp_revoke_view', kwargs={'user': aux.user.id, 'otp': otp,})
                complete_url = urljoin(server_address, revoke_url)

                message = f"""
Hi {aux.user.get_username()},

Your Warehauser account password has been successfully changed. If this was done in error then click on this link:

    {complete_url}

Otherwise, happy warehausing!

Regards,
The Warehause Admin Team
"""

                send_mail(subject='Warehauser password change successful',
                        message=message,
                        from_email='noreply@warehauser.org',
                        recipient_list=[to_address],
                        fail_silently=False)

    def process(self):
        try:
            with db_mutex(f'emailthread'):
                self._send_password_change_emails()
        except DBMutexError as e:
            return
        except Exception as e:
            raise e
