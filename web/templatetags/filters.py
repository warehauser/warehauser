# Copyright 2024 warehauser @ github.com

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
