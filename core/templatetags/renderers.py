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

# renderers.py

import logging

from django import template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def render_buttons(buttons):
    html = ''
    for button in buttons:
        html = html + '<div class="form-row">'
        if button['type'] == 'href' if 'type' in button else False:
            html = html + '<a'
            if 'attrs' in button:
                for k, v in button['attrs'].items():
                    if k == 'href':
                        html = html + f' href="{ reverse(v) }"'
                    else:
                        html = html + f' {k}="{v}"'
            title = button['title']
            html = html + f'>{title}</a>'
        else:
            html = html + '<button'
            if 'attrs' in button:
                for k, v in button['attrs'].items():
                    html = html + f' {k}="{v}"'
            title = button['title']
            html = html + f'>{title}</button>'
        html = html + '</div>'

    return render_to_string('renderers/buttons.html', {'buttons': mark_safe(html)})

@register.simple_tag
def field_renderer_default(fields:list) -> str:
    print('core.renderers.field_renderer_default(fields:list)')
    return render_to_string('renderers/forms/field_renderer_default.html', {'fields': fields})

@register.simple_tag
def field_renderer_otp(fields:list) -> str:
    return render_to_string('renderers/forms/field_renderer_otp.html', {'fields': fields})

@register.simple_tag(takes_context=True)
def render_fields(context, renderer, fields):
    if 'renderers' not in context:
        return f"Error: Renderer method '{renderer}' not found"

    renderers = context['renderers']
    if renderer in renderers:
        func = renderers[renderer]
        return func(fields)
    else:
        # Handle the case where the method is not found
        return f"Error: Renderer method '{renderer}' not found"
