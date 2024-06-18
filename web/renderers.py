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

from bs4 import BeautifulSoup

from django.utils.safestring import mark_safe

from .utils import debug_func

def _render_tags(tags:list):
    """
    Renders HTML tags from a list of tag dictionaries.

    The `tags` parameter is a list of dictionaries where each dictionary
    defines an HTML tag and its attributes, content, and optional callable
    functions to dynamically generate attribute values or content.

    Each dictionary in the `tags` list should have the following structure:
    {
        'tag': str,  # The name of the HTML tag (e.g., 'div', 'span').
        'attrs': dict (optional),
            # Dictionary of attribute key-value pairs.
                # Attribute values can be a:
                # - str: A string value for the attribute.
                # - bool: A boolean value; True converts to 'true', False is omitted.
                # - dict: A dictionary with a 'callable' key and optional 'args' or 'kwargs'.
                #         Example: {'callable': function_pointer, 'args': [], 'kwargs': {}}
        'content': str or dict or list (optional),
            # The content inside the tag.
            # Content can be a:
                # - str: A string value for the tag content.
                # - dict: A dictionary with a 'callable' key and optional 'args' or 'kwargs'.
                #         Example: {'callable': function_pointer, 'args': [], 'kwargs': {}}
                # - list: A list of dictionaries to nest tags inside the current tag each of which take the form of the tags dictionary.
    }

    Examples:
    tags = [
        {
            'tag': 'div',
            'attrs': {
                'class': 'row form-row mb-4',
                'style': {
                    'callable': self._dothat, # assuming self._dothat is a function defined as def _dothat(self, *args, **kwargs)
                    'kwargs': {'foo': 'bar'}
                }
            },
            'content': [
                {
                    'tag': 'div',
                    'attrs': {'class': 'input-box'},
                    'content': {
                        'callable': self._dothis, # assuming self._dothis is a function defined as def _dothis(self, *args, **kwargs)
                        'args': [],
                        'kwargs': {}
                    }
                }
            ]
        }
    ]
    return self._append_tags(tags)

    Parameters:
    tags (list): A list of dictionaries defining the HTML tags and their attributes and content.

    Returns:
    str: A safe HTML string constructed from the provided tags.
    """
    def _render_tag(tag_dict):
        tag = tag_dict['tag']
        attrs = tag_dict.get('attrs', {})
        content = tag_dict.get('content', None)

        def evaluate_value(value):
            if isinstance(value, dict):
                if 'callable' in value and callable(value['callable']):
                    callable_func = value['callable']
                    args = value.get('args', [])
                    kwargs = value.get('kwargs', {})
                    return callable_func(*args, **kwargs)
            elif isinstance(value, bool):
                return str(value).lower()
            return value

        # Create the attribute string
        attr_str = (' ' + ' '.join(f'{key}="{evaluate_value(value)}"' for key, value in attrs.items())) if attrs else ''

        # Handle the content
        if isinstance(content, dict):
            if 'callable' in content and callable(content['callable']):
                callable_func = content['callable']
                args = content.get('args', [])
                kwargs = content.get('kwargs', {})
                content = callable_func(*args, **kwargs)
            else:
                content = ''.join(_render_tag(content))
        elif isinstance(content, list):
            content = ''.join(_render_tag(sub_tag) for sub_tag in content)

        # Construct the tag
        if content is None:
            return f'<{tag}{attr_str} />'
        elif content == '':
            return f'<{tag}{attr_str}></{tag}>'
        else:
            return f'<{tag}{attr_str}>{content}</{tag}>'

    html = ''.join(_render_tag(tag_dict) for tag_dict in tags)
    return mark_safe(html)

def _generate_tag(tag, attrs, content):
    return {'tag': tag, 'attrs': attrs, 'content': content}

def _render_bs4(content):
    soup = BeautifulSoup(content, 'html.parser')
    return mark_safe(soup.prettify())
