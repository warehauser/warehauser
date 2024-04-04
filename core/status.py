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

# status.py

STATUS_DESTROY    = -1
STATUS_CLOSED     = 0
STATUS_PROCESSING = 1
STATUS_ON_HOLD    = 2
STATUS_OPEN       = 3

# WAREHAUSE STATUS CODES
WAREHAUSEDEF_STATUS_CODES = (
    (STATUS_DESTROY,    'Destroy'),
    (STATUS_CLOSED,     'Closed'),
    (STATUS_OPEN,       'Open'),
)

WAREHAUSE_STATUS_CODES = (
    (STATUS_DESTROY,    'Destroy'),
    (STATUS_CLOSED,     'Closed'),
    (STATUS_OPEN,       'Open'),
)

# PRODUCT STATUS CODES
PRODUCTDEF_STATUS_CODES = (
    (STATUS_DESTROY,    'Destroy'),
    (STATUS_CLOSED,     'Closed'),
    (STATUS_OPEN,       'Open'),
)

PRODUCT_STATUS_CODES = (
    (STATUS_DESTROY,    'Destroy'),
    (STATUS_CLOSED,     'Closed'),
    (STATUS_OPEN,       'Open'),
)

# EVENT STATUS CODES
EVENTDEF_STATUS_CODES = (
    (STATUS_DESTROY,    'Destroy'),
    (STATUS_CLOSED,     'Closed'),
    (STATUS_OPEN,       'Open'),
)

EVENT_STATUS_CODES = (
    (STATUS_DESTROY,    'Destroy'),
    (STATUS_CLOSED,     'Closed'),
    (STATUS_PROCESSING, 'Processing'),
    (STATUS_ON_HOLD,    'On Hold'),
    (STATUS_OPEN,       'Open'),
)
