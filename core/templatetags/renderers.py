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

from core.utils import dict_get_or_default, dict_copy_and_update

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def render_buttons(buttons):
    return render_to_string('renderers/buttons.html', {'buttons': buttons})

@register.simple_tag
def field_renderer_default(fields:list) -> str:
    return render_to_string('renderers/forms/field_renderer_default.html', {'fields': fields})

@register.simple_tag
def field_renderer_otp(fields:list) -> str:
    return render_to_string('renderers/forms/field_renderer_otp.html', {'fields': fields})

@register.simple_tag(takes_context=True)
def render_fields(context, renderer, fields):
    # Get the method name specified in the renderer variable
    # Check if the method exists in the template context

    if renderer in register.tags:
        # Call the method with the fields argument and return the result
        return render_to_string(register.tags[renderer], {'fields': fields})

    if 'renderers' not in context:
        return f"Error: Renderer method '{renderer}' not found"

    renderers = context['renderers']
    if renderer in renderers:
        method = renderers[renderer]
        # Call the method with the fields argument and return the result
        return method(fields)
    else:
        # Handle the case where the method is not found
        return f"Error: Renderer method '{renderer}' not found"

def render_open_tag(name:str, attributes:dict, close:bool=True) -> str:
    """
    Generate a openning tag only.
    """
    result = f'<{name}'

    for key, val in attributes.items():
        result = result + ' {}="{}"'.format(key, val)

    if close:
        result = result + '/'
    result = result + '>'

    return mark_safe(result)

from lxml import html, etree

def render_layout(content:dict, dft:dict=dict(), renderers:dict=dict()) -> str:
    result = ''

    dft = dict_copy_and_update(d=dft, u=dict_get_or_default(d=content, k='default', v=dict()))

    typ = content['type'] if 'type' in content else 'tag'

    match typ:
        case 'html':
            result = result + mark_safe(content[typ])
        case 'text':
            result = result + content[typ]
        case _:
            name = content['name']
            if name in renderers:
                func = renderers[name]
            else:
                func = render_open_tag
            close = 'content' not in content
            result = result + func(name=content['name'], attributes=dict_get_or_default(d=content, k='attributes', v=dict()), close=close)

            if close is False:
                for ctnt in content['content']:
                    result = result + render_layout(content=ctnt, dft=dft, renderers=renderers)
                result = result + f'</{name}>'

    return mark_safe(result)

@register.simple_tag(takes_context=True)
def render_context(context):
    dft = context['default'] if 'default' in context else dict()
    renderers = context['renderers'] if 'renderers' in context else dict()
    content = context['content']

    result = ''

    for cnt in content:
        result = result + render_layout(content=cnt, dft=dft, renderers=renderers)

    document_root = html.fromstring(result)
    return mark_safe(dft['doctype'] + '\n' + etree.tostring(document_root, encoding='unicode', pretty_print=True))
