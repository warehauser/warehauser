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

# views.py

import json

from datetime import datetime, timedelta
from typing import Any#, List

from django.shortcuts import render

from django.conf import settings
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from rest_framework.authtoken.models import Token

from core.models import *

from .decorators import *
from .forms import *
from .models import *
from core.utils import is_valid_email_address, generate_otp_code

from .renderers import _render_tags, _render_bs4, _generate_tag

BASE_TITLE = f'Warehauser - {_("Your warehouse run smoothly")}'

def generate_page_title(title:str) -> str:
    return (f'{_(title)} - {BASE_TITLE}')

def generate_button_attributes(attrs:dict) -> dict:
    dfts = {
        'type': 'submit',
        'class': 'btn btn-primary col-12',
    }

    dfts.update(attrs)

    return dfts


# Create your views here.

def home_view(request):
    context = {
        'title': generate_page_title('Welcome'),
    }

    response = render(request, "web/index.html", context=context)
    return response

class DefaultFormHandler:
    # @debug_func
    def _generate_html_input(self, name:str, field):
        attrs = {'id': name.lower(), 'name': name.lower(), 'type': field.widget.input_type,}
        attrs.update(field.widget.attrs)
        label = field.label

        tags:list = list()

        tags.append(_generate_tag(tag='input',
                            attrs=attrs,
                            content=None))

        tags.append(_generate_tag(tag='span',
                                attrs={
                                    'class': 'label',
                                },
                                content=_(label),
                                ))

        if field.widget.__class__.__name__.lower() == 'passwordinput':
            toggle_icon = _generate_tag(tag='ion-icon',
                                        attrs={
                                            'id': f'{name}-toggle',
                                            'name': 'eye-off-outline',
                                            'onclick': f'passwordShowHide(this, \'{name}\', 4000);',
                                        },
                                        content='')
            tags.append(_generate_tag(tag='div', attrs={'class': 'input-text-button',}, content=toggle_icon))

        if field.widget.attrs.get('required', False):
            tags.append(_generate_tag(tag='div',
                        attrs={
                                'class': 'required',
                                'data-bs-toggle': 'tooltip',
                                'data-bs-placement': 'left',
                                'data-bs-title': 'Required',
                        },
                        content=''))

        tags.append(_generate_tag(tag='div',
                      attrs={
                          'class': 'error error-message',
                          'id': f'error-{name}',
                          },
                       content=''))

        npt_box = _generate_tag(tag='div',
                                attrs={'class': 'input-box',},
                                content=tags)

        tags = _generate_tag(tag='div',
                           attrs={'class': 'row form-row mt-3',},
                           content=npt_box)

        return tags

    # @debug_func
    def _generate_button(self, button):
        attrs = button['attrs'] if button and 'attrs' in button else {}
        content = button['content'] if button and 'content' in button else ''
        content = _generate_tag(tag='button', attrs=attrs, content=content)
        content = _generate_tag(tag='div', attrs={'class': 'button-row'}, content=content)
        return _generate_tag(tag='div', attrs={'class': 'row form-row mt-4'}, content=content)

    # @debug_func
    def _generate_submit_button(self, id, val, content, disabled:bool=False):
        attrs = {
            'id': id,
            'type': 'submit',
            'class': 'btn btn-primary col-12',
            'value': val,
        }

        if disabled:
            attrs['disabled'] = True

        return self._generate_button({'attrs': attrs, 'content': content})

    # @debug_func
    def _generate_cancel_button(self, id, disabled:bool=False):
        attrs = {
            'id': id,
            'type': 'submit',
            'class': 'btn btn-secondary col-12',
        }

        if disabled:
            attrs['disabled'] = True

        return self._generate_button({'attrs': attrs, 'content': _('Cancel')})

    # @debug_func
    def _generate_modal_header(self, data):
        content = []

        try:
            header = data['header']
        except KeyError as ke:
            pass

        if header:
            if 'icon' in header:
                value = header['icon']
                content.append(_generate_tag(tag='ion-icon', attrs={'class': 'form-icon mt-4', 'name': value,}, content=''))

            if 'heading' in header:
                value = header['heading']
                if value:
                    content.append(_generate_tag(tag='h2', attrs=None, content=value))

            if 'slug' in header:
                value = header['slug']
                content.append(_generate_tag(tag='p', attrs={'class': 'modal-header-slug',}, content=value))

            if 'close' in header:
                id = data['attrs']['id']
                try:
                    href = header['close']['href']
                except KeyError as ke:
                    pass

                content.append(_generate_tag(tag='a', attrs={'href': href,},
                                             content=_generate_tag(tag='ion-icon', attrs={'class': 'modal-close-icon', 'name': 'close-circle-outline', 'role': 'img',}, content='')))

        content = _generate_tag(tag='div', attrs={'class': 'w-100 text-center'}, content=content)
        content = _generate_tag(tag='div', attrs={'class': 'modal-header'}, content=content)

        return content

    # @debug_func
    def _generate_modal_body(self, data):
        content = [self._generate_html_input(name, field) for name, field in self.fields.items()]
        content = content + [self._generate_button(button) for button in data['buttons']]
        return _generate_tag(tag='div', attrs={'class': 'modal-body',}, content=content)

    # @debug_func
    def _generate_modal_footer(self, data):
        try:
            footer = data['footer']
        except KeyError as ke:
            footer = None
        return _generate_tag(tag='div', attrs={'class': 'modal-footer',}, content=footer)

    # @debug_func
    def _generate_modal_element(self, data, key, content):
        try:
            attrs = data[key]['attrs']
        except KeyError as ke:
            attrs = dict()

        # Ensure the 'class' attribute exists and is a string
        class_names = attrs.get('class', '')

        # Split the class names into a list
        class_list = class_names.split()

        # Add the key if it's not already in the list
        if key not in class_list:
            class_list.append(key)

        # Remove duplicates by converting the list to a set and back to a list
        class_list = list(set(class_list))

        # Join the list back into a space-separated string
        attrs['class'] = ' '.join(class_list)

        return _generate_tag(tag='div', attrs=attrs, content=content)

    # @debug_func
    def as_modal(self, request):
        form = WarehauserAuthLoginForm(auto_id="%s")
        content = [self._generate_modal_header(form), self._generate_modal_body(form), self._generate_modal_footer(form)]
        content = self._generate_modal_element(form, 'modal-content', content)
        content = self._generate_modal_element(form, 'modal-dialog', content)
        content = _generate_tag(tag='input', attrs={'type': 'hidden', 'name': 'csrf_token', 'value': request.get_token(),}, content=content)
        content = _generate_tag(tag='form', attrs=form['attrs'], content=content)
        content = _generate_tag(tag='div', attrs=form['modal']['attrs'], content=content)

        return _render_bs4(_render_tags([content]))

    # @debug_func
    def get(self, request, *args, **kwargs) -> HttpResponse:
        return HttpResponse(status=501, reason='GET method not implemented.')

    # @debug_func
    def post(self, request, *args, **kwargs) -> JsonResponse:
        return JsonResponse(status=501, reason='POST method not implemented.')

    # @debug_func
    def patch(self, request, *args, **kwargs) -> JsonResponse:
        return JsonResponse(status=501, reason='PATCH method not implemented.')

    # @debug_func
    def delete(self, request, *args, **kwargs) -> JsonResponse:
        return JsonResponse(status=501, reason='DELETE method not implemented.')

    # @debug_func
    def head(self, request, *args, **kwargs) -> JsonResponse:
        return JsonResponse(status=501, reason='HEAD method not implemented.')

    # @debug_func
    def handle(self, request, *args, **kwargs) -> None:
        match request.method.lower():
            case 'get':
                return self.get(request, *args, **kwargs)
            case 'post':
                return self.post(request, *args, **kwargs)
            case 'patch':
                return self.patch(request, *args, **kwargs)
            case 'delete':
                return self.delete(request, *args, **kwargs)
            case 'head':
                return self.head(request, *args, **kwargs)

        return JsonResponse(status=501, reason=f'{request.method} method not implemented.')

class AuthLoginFormHandler(DefaultFormHandler):
    def get(self, request, *args, **kwargs) -> HttpResponse:
        # login_form = WarehauserAuthLoginForm(auto_id="%s")
        login_form = WarehauserAuthLoginForm()
        context = {
            'modal': {
                'attrs': {
                    "id": "modal-login",
                    "class": "modal",
                    "offscreen": "top",
                },
            },
            'header': {
                "icon": "lock-open-outline",
                "heading": _("Login"),
                "slug": _("Welcome to Warehauser"),
                # "close": True,
            },
            'content': {
                'attrs': {
                    'id': "modal-content-login",
                    'class': "modal-content",
                },
            },
            'footer': mark_safe(f'<div class="row form-row w-100 mb-5 text-center"><a id="link-forgot" href="javascript:loadForgot();">Forgot your password?</a></div>'),
            'form': {
                'obj': login_form,
                'attrs': {
                    'id': 'form-login',
                    'method': 'post',
                    'onsubmit': "submitForm(event, '#form-login', '/form/web/login/', loginSuccessHandler);",
                },
                "buttons": [
                    self._generate_submit_button('submit-login', 'login', _('Login'), True),
                ],
            },
            'scripts': [
                # { 'template': 'web/js/login.js', },
                { 'attrs': {'id': 'script-form-login', 'src': '/static/web/js/forms/login.js',}, },
                # { 'content': 'console.log("HELLO WORLD");', },
            ],
        }
        return render(request=request, template_name='web/modal.html', context=context)

    def post(self, request, *args, **kwargs) -> JsonResponse:
        if request.user.id:
            json = {
                'error': _('User already logged in'),
            }
            return JsonResponse(json, status=401) # 401 Unauthorized

        # Extract data from the POST request
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user
        if is_valid_email_address(username):
            user = authenticate(request, email=username, password=password)
        else:
            user = authenticate(request, username=username, password=password)

        if user is not None:
            # login user
            login(request, user)
            return JsonResponse({'user': user.username}, status=200) # Successful login
        else:
            # Handle invalid login credentials
            json = {
                'error': _('Invalid credentials'),
            }
            return JsonResponse(json, status=401) # 401 Unauthorized

class AuthForgotFormHandler(DefaultFormHandler):
    def get(self, request, *args, **kwargs) -> HttpResponse:
        forgot_form = WarehauserAuthForgotPasswordForm(auto_id="%s")
        context = {
            'modal': {
                'attrs': {
                    "id": "modal-forgot",
                    "class": "modal",
                    "offscreen": "top",
                },
            },
            'header': {
                "icon": "lock-open-outline",
                "heading": _("Forgot Password"),
                "slug": _("Let's Reset Your Password"),
                # "close": True,
            },
            'content': {
                'attrs': {
                    'id': "modal-content-forgot",
                    'class': "modal-content",
                },
            },
            # 'footer': mark_safe(f'<div class="row form-row w-100 mb-5 text-center"><a id="link-forgot" href="javascript:loadForgot();">Forgot your password?</a></div>'),
            'form': {
                'obj': forgot_form,
                'attrs': {
                    'id': 'form-forgot',
                    'method': 'post',
                    'onsubmit': "submitForm(event, '#form-forgot', '/form/web/forgot/', forgotSuccessHandler);",
                },
                "buttons": [
                    self._generate_submit_button('submit-forgot', 'reset', _('Reset'), True),
                    self._generate_cancel_button('cancel-forgot', True),
                ],
            },
        }
        return render(request=request, template_name='web/modal.html', context=context)

    def post(self, request, *args, **kwargs) -> JsonResponse:
        print(f'AuthForgotFormHandler.post() called')
        form = WarehauserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            data = {
                'otp': {
                    'codes': {
                        generate_otp_code(): {
                            'status': 0,
                            'type': 'passwd',
                            'dt': f'{timezone.localtime(timezone.now())}',
                            'data': {
                                'old_password': make_password(form.cleaned_data.get('old_password')),
                            },
                        },
                    },
                },
            }

            try:
                with db_mutex(f'core_useraux'):
                    try:
                        aux = UserAux.objects.get(user=user)
                        aux.options.update(data)
                    except Exception as e:
                        aux = UserAux.objects.create(user=user, options=data)

                    if 'attempts' not in aux.options['otp']:
                        aux.options['otp']['attempts'] = list()
                    aux.save()
            except Exception as e:
                raise e

            user = form.save()
            update_session_auth_hash(request, user)

        return JsonResponse({}, status=200) # Successful request

def app_form_router(request, app, name):
    router = (app + '.' + name).replace(' ', '')
    match router:
        case 'web.login':
            return AuthLoginFormHandler().handle(request)
        case 'web.logout':
            auth_logout(request=request)
            return redirect('home_view')
        case 'web.forgot':
            return AuthForgotFormHandler().handle(request)
        # case '???':... etc

    return HttpResponse(status=404, reason=f'Form {name} for app {app} not found.')

# @user_passes_test(lambda u: u.is_superuser)
# def client_groups_view(request):
#     # Filter groups with names starting with 'client_'
#     client_groups = Group.objects.filter(name__startswith='client_')
    
#     # Extract the display name (the part after 'client_') and create a list of tuples
#     group_links = [(group.name, group.name.replace('client_', '')) for group in client_groups]
    
#     context = {
#         'group_links': group_links,
#     }
    
#     return render(request, 'client_list.html', context)

# def group_detail_view(request, group_name):
#     group = get_object_or_404(Group, name=group_name)
#     return render(request, 'client_detail.html', {'client': group})






@login_required
def client_detail_view(request, client):
    print(Group.objects.filter(name=f'client_{client}'))
    context = {
        'modal': {
            'attrs': {
                'id': f'modal-clients',
                'class': 'modal',
                'offscreen': 'right',
            },
        },
        'header': {
            'icon': 'cube-outline',
            'heading': _(f'Client {client}'),
            'slug': _('Choose the Warehause'),
            # "close": True,
        },
        'content': {
            'attrs': {
                'id': 'modal-content-forgot',
                'class': 'modal-content',
            },
            'template': 'web/client_detail.html',
            'data': {'client': Group.objects.filter(name=f'client_{client}').first(),
                     'user_token': Token.objects.get(user=request.user).key,},
        },
    }

    return render(request=request, template_name='web/modal.html', context=context)

@login_required
def client_list_view(request):
    if not request.user.is_superuser:
        client_group = request.user.groups.filter(name__startswith='client_').first()

        if client_group:
            # If a group is found, redirect to the client detail view
            group_name = client_group.name.replace('client_', '')
            return client_detail_view(request, group_name)
        else:
            # Handle case where no group is found
            return HttpResponse(status=401, reason=f'No client group found.')



        # find the Group the user belongs to that has the name in the form of 'client_' and return client_detail_view(request, groupname)
        pass

    # Filter groups with names starting with 'client_'
    client_groups = Group.objects.filter(name__startswith='client_')
    
    # Extract the display name (the part after 'client_') and create a list of tuples
    group_links = [(group.name, group.name.replace('client_', '')) for group in client_groups]

    context = {
        'modal': {
            'attrs': {
                'id': f'modal-clients',
                'class': 'modal',
                'offscreen': 'right',
            },
        },
        'header': {
            'icon': 'cube-outline',
            'heading': _('Client'),
            'slug': _('Choose the client'),
            # "close": True,
        },
        'content': {
            'attrs': {
                'id': 'modal-content-forgot',
                'class': 'modal-content',
            },
            'template': 'web/client_list.html',
            'data': {'links': group_links,},
        },
    }

    return render(request=request, template_name='web/modal.html', context=context)






    data = '''
        <div class="container-fluid">
'''
    if(request.user.is_superuser):
        data = data + '''
            <div class="row">
                <a class="nav-link" href="#">
                    <ion-icon name="people-outline" class="icon"></ion-icon>
                    <span class="link-text">Clients</span>
                </a>
            </div>
'''



                        # <div id="sidebar-toggler" class="text-end">
                        #     <ion-icon name="ellipsis-horizontal-outline" size="large"></ion-icon>
                        # </div>

                            # <li class="nav-item">
                            #     <a class="nav-link" href="#">
                            #         <ion-icon name="bar-chart-outline" class="icon"></ion-icon>
                            #         <span class="link-text">Reports</span>
                            #     </a>
                            # </li>
                            # <li class="nav-item">
                            #     <a class="nav-link" href="#">
                            #         <ion-icon name="layers-outline" class="icon"></ion-icon>
                            #         <span class="link-text">Integrations</span>
                            #     </a>
                            # </li>

    data = data + '''
            <div class="row">
                <nav id="sidebar" class="col-md-3 col-lg-2 d-md-block bg-light sidebar">
                    <div class="position-sticky">
                        <ul class="nav flex-column">
                            <li class="nav-item">
                                <a class="nav-link" href="#">
                                    <ion-icon name="location-outline" class="icon"></ion-icon>
                                    <span class="link-text">Warehauses</span>
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="#">
                                    <ion-icon name="cube-outline" class="icon"></ion-icon>
                                    <span class="link-text">Products</span>
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="#">
                                    <ion-icon name="notifications-outline" class="icon"></ion-icon>
                                    <span class="link-text">Events</span>
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="#">
                                    <ion-icon name="settings-outline" class="icon"></ion-icon>
                                    <span class="link-text">Settings</span>
                                </a>
                            </li>
                        </ul>
                    </div>
                </nav>

                <!-- Main content area -->
                <div class="col-md-9 col-lg-10 ms-sm-auto px-md-4">
                    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                        <h1 class="h2">Dashboard</h1>
                    </div>
                    <p>Hello world</p>
                </div>
            </div>'''

    data = data + '''
        </div>
'''

    return HttpResponse(mark_safe(data))
    if request.user:
        print('user is ', request.user)

    tags = [
        _generate_tag('div', {}, [_generate_tag('a', {'href': '#'}, 'Hello World')]),
    ]
    return HttpResponse(_render_tags(tags))












from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from .forms import WarehauserAuthLoginForm

@anonymous_required
def auth_login_view_old(request):
    if request.method.lower() == 'post':
        form = WarehauserAuthLoginForm(auto_id="%s", data=request.POST)
        if form.is_valid():
            user = form.get_user()
        else:
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if is_valid_email_address(username):
                user = authenticate(request, email=username, password=password)
            else:
                user = authenticate(request, username=username, password=password)

        if user:
            # login user
            login(request, user)
            return JsonResponse({'user': user.username}, status=200)
        else:
            # Handle invalid login credentials
            return JsonResponse({'error': 'Invalid credentials',}, status=401)
    else:
        form = WarehauserAuthLoginForm(request)

    data = {
        'attrs': {'id': 'form-login', 'action': 'javascript:submitLogin();', 'method': 'post',},
        'buttons': [{'attrs': {'type': 'submit', 'value': 'login', 'class': 'btn btn-primary col-12', 'disabled': True,}, 'content': _('Login')}],
        'modal': {
            'attrs': {'class': 'modal', 'id': 'modal-login', 'tabindex': -1,},
        },
        'modal-dialog': {},
        'modal-content': {
            'attrs': {
                'id': 'modal-login-content',
                'stage-parent': 'modal-login',
                'offscreen': 'top',
            },
        },
        'header': {
            'icon': 'lock-closed-outline',
            'heading': _('Login'),
            'slug': _('Welcome to Warehauser'),
            # 'close': True, # use the close key to add a close icon to the modal. Not advised for form-login
        },
        'body': {},
        'footer': [{
            'tag': 'div',
            'attrs': {'class': 'row form-row w-100 mb-4 text-center'},
            'content': [{'tag': 'a', 'attrs': {'id': 'link-forgot', 'href': 'javascript:getForgotPassword();',}, 'content': _('Forgot your password?'),}]}],
        'csrf': get_token(request=request),
    }

    return HttpResponse(form.as_modal(data=data))

def auth_logout_view(request):
    auth_logout(request=request)
    return redirect('home_view')

@login_required
def auth_user_profile_view(request):
    return render(request=request, template_name='auth/user_profile.html')

@login_required
def auth_change_password_view(request):
    user = request.user

    if request.method.lower() == 'post':
        form = WarehauserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            data = {
                'otp': {
                    'codes': {
                        generate_otp_code(): {
                            'status': 0,
                            'type': 'passwd',
                            'dt': f'{timezone.localtime(timezone.now())}',
                            'data': {
                                'old_password': make_password(form.cleaned_data.get('old_password')),
                            },
                        },
                    },
                },
            }

            try:
                with db_mutex(f'core_useraux'):
                    try:
                        aux = UserAux.objects.get(user=user)
                        aux.options.update(data)
                    except Exception as e:
                        aux = UserAux.objects.create(user=user, options=data)

                    if 'attempts' not in aux.options['otp']:
                        aux.options['otp']['attempts'] = list()
                    aux.save()
            except Exception as e:
                raise e

            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('auth_user_profile_view')
    else:
        form = WarehauserPasswordChangeForm(request.user)

    template = 'core/form.html'
    form.id = 'login-form'

    context = {
        'form': form,
        # 'renderers': {
        #     'field_renderer_default': field_renderer_default,
        # },
        'title': _('Change Password'),
        'illustration': 'icon ion-ios-locked-outline',
        'buttons': [
            {'title': _('Change Password'), 'attrs': generate_button_attributes({'id': 'submit', 'value': 'login', 'type': 'submit',})},
        ],
    }

    return render(request, template, context)

















@anonymous_required
def auth_forgot_password_view(request):
    if request.method.lower() == 'post':
        form = WarehauserAuthForgotPasswordForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            confirm = form.cleaned_data.get('confirm')

            if is_valid_email_address(email) is False:
                form.add_error(None, 'Email is not of a valid format.')
            elif password != confirm:
                form.add_error(None, 'Passwords do not match.')
            else:
                user = User.objects.filter(email=email).first()
                if not user:
                    # If the user with the email address supplied does not exist, return success (but do nothing! HEHEHE!)
                    return JsonResponse({}, status=200)

                otp = generate_otp_code(length=6)

                data = {
                    'otp': {
                        'codes': {
                            otp: {
                                'status': 0,
                                'type': 'forgotpwd',
                                'dt': f'{timezone.localtime(timezone.now())}',
                                'data': {
                                    'password': make_password(password),
                                },
                            },
                        },
                    },
                }

                try:
                    with db_mutex(f'core_useraux'):
                        try:
                            aux = UserAux.objects.get(user=user)
                            aux.options.update(data)
                        except Exception as e:
                            aux = UserAux.objects.create(user=user, options=data)

                        if 'attempts' not in aux.options['otp']:
                            aux.options['otp']['attempts'] = list()
                        aux.save()
                except Exception as e:
                    raise e

                # Store password in session and send confirmation email...
                content = f"""
Hi,

Here is your one time code to change your password:

{otp}

"""

                send_mail(subject='Warehauser Password Reset Request',
                          message=content,
                          from_email=settings.SEND_MAIL_FROM_ADDRESS,
                          recipient_list=[email,],
                          fail_silently=False)

            return JsonResponse({}, status=200)
        else:
            return JsonResponse({}, status=200)

    data = {
        'attrs': {'id': 'form-forgot', 'action': 'javascript:submitForgotPassword();', 'method': 'post',},
        'buttons': [{'attrs': {'type': 'submit', 'value': 'sendcode', 'class': 'btn btn-primary col-12', 'disabled': True,}, 'content': _('Send Code')}],
        'modal': {
            'attrs': {'class': 'modal', 'id': 'modal-forgot', 'tabindex': -1, 'offscreen': 'top',},
            'header': {
                'icon': 'lock-closed-outline',
                'heading': _('Forgot Password'),
                'slug': _('Request change of password'),
                'close': {'href': 'javascript:cancelForm(loadLogin);',}, # use the close key to add a close icon to the modal. Not advised for form-login
            },
            'body': {
            },
        },
        'csrf': get_token(request=request),
    }

    form = WarehauserAuthForgotPasswordForm(request)
    return HttpResponse(form.as_modal(data=data))
















def _auth_otp_form(request:Any, title:str, err:str = None) -> HttpResponse:
    form = WarehauserOTPChallengeForm()
    form.id = 'otp-form'

    template = 'core/form.html'
    context = {
        'form': form,
        # 'renderers': {
        #     'field_renderer_otp': field_renderer_otp,
        # },
        'title': title,
        'title_class': 'form-title',
        'preamble': 'Enter code:',
        'illustration': 'icon ion-ios-locked-outline',
        'buttons': [
            {'title': _('Verify'), 'attrs': generate_button_attributes({'id': 'submit', 'value': 'submit', 'type': 'submit', 'disabled': 'true',})},
        ],
    }

    if err:
        context['messages'] = [err]

    return render(request, template, context)

def _auth_opt_register_attempt(useraux:UserAux, action:str) -> None:
    now = timezone.localtime(timezone.now())
    attempt = {'dt': str(now), 'action': action}

    if 'otp' not in useraux.options:
        useraux.options['otp'] = dict()
    if 'attempts' not in useraux.options['otp']:
        useraux.options['otp']['attempts'] = list()

    useraux.options['otp']['attempts'].append(attempt)
    useraux.save()

def _auth_otp_attempt(request:Any, action:str, type:str, useraux:UserAux, otp:str) -> HttpResponse:
    options = useraux.options

    # Check the attempts have not locked the otp...
    minutes = 1
    now = timezone.localtime(timezone.now())
    time_limit = now - timedelta(minutes=minutes)

    attempts = options['otp']['attempts']
    count = 0

    for att in attempts.copy():
        # Convert att['dt'] string to datetime object
        dt = datetime.strptime(att['dt'], '%Y-%m-%d %H:%M:%S.%f%z')

        if dt < time_limit:
            attempts.remove(att) # Remove expired attempt
            continue

        if att['action'] == action:
            count = count + 1

    if count > 2:
        _auth_opt_register_attempt(useraux=useraux, action=action)
        return _auth_otp_form(request=request, title=_(f'{action.title()} Action'), err=_(f'Too many attempts. Wait {minutes} minutes before retrying.'))

    time_limit = now - timedelta(days=1)

    if otp in options['otp']['codes']:
        otp_info = options['otp']['codes'][otp]

        # If the otp request is stale, delete it and resend the form without errors...
        dt = datetime.strptime(otp_info['dt'], '%Y-%m-%d %H:%M:%S.%f%z')
        if dt < time_limit:
            del options['otp']['codes'][otp]
            useraux.save()
            return _auth_otp_form(request=request, title=_(f'{action.title()} Action'))

        match f'{type}':
            case 'passwd':
                if action == 'revoke':
                    useraux.user.password = otp_info['data']['old_password']
                    useraux.user.save()

        del options['otp']['codes'][otp]
        useraux.save()

        return redirect(reverse('home'))

    attempts.append({'dt': str(now), 'action': action})
    useraux.save()

    return _auth_otp_form(request=request, title=_(f'{action.title()} Action'))

def _auth_otp_view(request:Any, action:str, user:int, otp:str=None) -> HttpResponse:
    title = _(f'{action.title()} Action')
    try:
        user_obj = get_user_model().objects.get(id=user)
    except Exception as e:
        return _auth_otp_form(request=request, title=title)

    try:
        useraux = UserAux.objects.get(user=user_obj)
    except Exception as e:
        _auth_opt_register_attempt(useraux=UserAux.objects.create(user=user_obj, options=dict({'otp': {'codes': {}, 'attempts': []}})), action=action)
        return _auth_otp_form(request=request, title=title)

    if otp is None:
        if request.method.lower() == 'post':
            form = WarehauserOTPChallengeForm(request.POST)
            if form.is_valid():
                return _auth_otp_attempt(request=request, action=action, type='passwd', useraux=useraux, otp=form.get_otp_combined())
        return _auth_otp_form(request=request, title=title)
    else:
        return _auth_otp_attempt(request=request, action=action, type='passwd', useraux=useraux, otp=otp)

def auth_otp_revoke_view(request:Any, user:int, otp:str=None) -> HttpResponse:
    return _auth_otp_view(request=request, action='revoke', user=user, otp=otp)

def auth_otp_accept_view(request:Any, user:int, otp:str=None) -> HttpResponse:
    return _auth_otp_view(request=request, action='accept', user=user, otp=otp)

