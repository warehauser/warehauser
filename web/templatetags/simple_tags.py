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
from django.template.loader import render_to_string
from django.forms import CheckboxInput, CheckboxSelectMultiple, ClearableFileInput, TextInput, EmailInput, URLInput, NumberInput, PasswordInput, RadioSelect, Textarea, Select, HiddenInput, DateInput, TimeInput, DateTimeInput
from django.utils.translation import gettext as _

from web.renderers import _render_tags, _render_attrs

register = template.Library()

@register.simple_tag
def setvar(val=None):
    return val

@register.simple_tag
def render_field(form, field):
    context = {
        'form': form,
        'field': field,
    }
    widget = field.field.widget
    if isinstance(widget, DateTimeInput):
        return render_to_string(f'web/forms/fields/datetime.html', context)
    elif isinstance(widget, DateInput):
        return render_to_string(f'web/forms/fields/date.html', context)
    elif isinstance(widget, TimeInput):
        return render_to_string(f'web/forms/fields/time.html', context)
    elif isinstance(widget, CheckboxSelectMultiple):
        return render_to_string(f'web/forms/fields/checkboxmultiple.html', context)
    elif isinstance(widget, CheckboxInput):
        return render_to_string(f'web/forms/fields/checkbox.html', context)
    elif isinstance(widget, RadioSelect):
        return render_to_string(f'web/forms/fields/radio.html', context)
    elif isinstance(widget, TextInput):
        return render_to_string(f'web/forms/fields/text.html', context)
    elif isinstance(widget, EmailInput):
        return render_to_string(f'web/forms/fields/email.html', context)
    elif isinstance(widget, URLInput):
        return render_to_string(f'web/forms/fields/url.html', context)
    elif isinstance(widget, NumberInput):
        return render_to_string(f'web/forms/fields/number.html', context)
    elif isinstance(widget, PasswordInput):
        return render_to_string(f'web/forms/fields/password.html', context)
    elif isinstance(widget, Textarea):
        return render_to_string(f'web/forms/fields/textarea.html', context)
    elif isinstance(widget, Select):
        return render_to_string(f'web/forms/fields/select.html', context)
    elif isinstance(widget, ClearableFileInput):
        return render_to_string(f'web/forms/fields/file.html', context)
    elif isinstance(widget, HiddenInput):
        return render_to_string(f'web/forms/fields/hidden.html', context)
    else:
        return render_to_string(f'web/forms/fields/default.html', context)

@register.simple_tag
def render_tags(tag):
    return _render_tags(tag)

@register.simple_tag
def render_attrs(data: dict):
    return _render_attrs(data)
