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
def get_value_by_key(d: dict, key: str):
    return d.get(key, None)

@register.simple_tag
def setvar(val=None):
    return val

@register.simple_tag
def render_form_as_modal(context):
    # print(context.keys())
    # return ''

    form = context.get('form')
    data = context.get('data', {})  # Provide default empty dictionary if 'data' is missing

    if form:
        return form.as_modal(data=data)
    return ''