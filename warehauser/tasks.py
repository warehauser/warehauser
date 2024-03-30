# Copyright 2024 stingermissile @ github.com

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

from django.utils.translation import gettext as _

from abc import ABC, abstractmethod

from django.db.models import ProtectedError
from core.models import *
from core.views import *

class WarehauserThread(threading.Thread, ABC):
    def run(self):
        logging.info(f"[{self}]: {_('Started.')}")
        self.process()
        logging.info(f"[{self}]: {_('Finished.')}")

    def __str__(self):
        return f"{_('Task')} {self.__module__}.{self.__class__.__name__}(id={self.ident})"

    @abstractmethod
    def process(self):
        pass

class ArchiverThread(WarehauserThread):
    def process(self):
        pass

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
                batched_events = Event.objects.filter(is_batched=True, status=EventStatus.OPEN.value)
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
                self._collect(Event.objects.filter(is_virtual=True, status=EventStatus.DESTROY.value))
                self._collect(Warehause.objects.filter(is_virtual=True, status=WarehauseStatus.DESTROY.value))
                self._collect(Product.objects.filter(is_virtual=True, status=ProductStatus.DESTROY.value))
        except DBMutexError as e:
            raise WarehauserError(_('Unable to secure mutex for garbagecollector.'), WarehauserErrorCodes.MUTEX_ERROR, {_('error'): e})
        except DBMutexTimeoutError as e:
            raise WarehauserError(_('Unable to secure mutex for garbagecollector.'), WarehauserErrorCodes.MUTEX_TIMEOUT_ERROR, {_('error'): e})


