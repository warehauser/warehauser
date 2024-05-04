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
# from django.forms.widgets import TextInput, PasswordInput, CheckboxInput, RadioSelect, Select, Textarea, DateInput, DateTimeInput
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def render_buttons(buttons):
    html = '<div class="row form-row mb-5">'
    for button in buttons:
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

    return render_to_string('core/forms/buttons.html', {'buttons': mark_safe(html)})

@register.simple_tag(takes_context=True)
def render_fields(context, form) -> str:
    html = ''
    for field in form.visible_fields():
        html = html + render_to_string(f'core/forms/fields/{field.field.widget.__class__.__name__.lower()}.html', {'context': context, 'field': field})
    for field in form.hidden_fields():
        html += field

    return mark_safe(html)

@register.simple_tag(takes_context=True)
def render_form(context, form) -> str:
    id = form['id']
    onsubmit = context['onsubmit'] if 'onsubmit' in context else 'submit_form'
    onsubmit = f'javascript:{onsubmit}(this);return false;'

    html = f'''<form id="{id}" method="post" onsubmit="{onsubmit}">
        <div id="form-header-{id}" class="text-center">
            <ion-icon id="form-header-icon-{id}" name="{form['header']['icon']}" class="form-icon mt-5"></ion-icon>
            <h2 id="form-title-{id}">{form['header']['title']}</h2>
        </div>
        <div class="text-center">
            <p class="mt-5">{form['header']['slug']}</p>
        </div>

        <div class="row justify-content-center my-5">'''

    html = html + f'''<input type="hidden" name="csrfmiddlewaretoken" value="{context['csrf_token']}">'''
    html = html + render_fields(context=context, form=form['form'])

    if 'buttons' in form:
        html = html + render_buttons(buttons=form['buttons'])

    if 'postmark' in form:
        postmark = form['postmark']
        html = html + f'<div class="row form-row center">{postmark}</div>'

    html = html + '</div></form>'
    return mark_safe(html)
