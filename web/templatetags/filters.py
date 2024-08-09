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

# filters.py

from django import template

register = template.Library()

@register.filter
def pop_key(d: dict, key: str):
    return d.pop(key, None)

@register.filter
def pop_key_from_attrs(field, key):
    return pop_key(field.field.widget.attrs, key)

@register.filter
def get_value_by_key(d: dict, key: str, default: str = None):
    if default is not None:
        if default.lower() == 'true':
            default = True
        elif default.lower() == 'false':
            default = False
    return d.get(key, default)

@register.filter(name='has_key')
def has_key(d: dict, key: str):
    if d is None:
        return False
    return key in d
