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
from typing import Any, List

from django.shortcuts import render

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
# from django.core.mail import send_mail
# from django.db.models import JSONField
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
# from django.templatetags.static import static
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils import translation

from core.models import *

from .decorators import *
from .forms import *
from .models import *
from core.utils import *
from .renderers import _render_tags, _generate_tag

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

    login_form = WarehauserAuthLoginForm(auto_id="%s")
    # login_form.fields['username'].widget.attrs.update({'autocomplete': 'off', 'css_classes': 'row form-row mb-4'})
    # login_form.fields['password'].widget.attrs.update({'autocomplete': 'off', 'css_classes': 'row form-row mb-4'})

    # login_form.modalid = 'modal-login'
    # login_form.offscreen = 'top'
    # login_form.header = {
    #     'icon': 'lock-closed-outline',
    #     'heading': _('Login'),
    #     'slug': _('Welcome to Warehauser'),
    #     'close': True,
    # }
    # login_form.footer = [{'tag': 'div', 'attrs': {'class': 'row form-row w-100 mb-5 text-center'}, 'content': mark_safe('<a id="link-forgot" href="#">Forgot your password?</a>'),},]

    password_reset_form = WarehauserAuthForgotPasswordForm(auto_id="%s")
    # password_reset_form.modalid = 'modal-password-reset'
    # password_reset_form.offscreen = 'right'
    # password_reset_form.card = {
    #     'classList': 'invisible',
    #     'onload': mark_safe('animate_move_element_dismiss_right("card-form-password-reset",0,"linear")'),
    # }
    # password_reset_form.onsubmit = f'submit_password_reset_form(\'{password_reset_form.id}\')'
    # password_reset_form.header = {
    #     'icon': 'lock-closed-outline',
    #     'heading': _('Forgot Password'),
    #     'slug': _('Let\'s fix that'),
    # }

    context = {
        'title': generate_page_title('Welcome'),
    }

    response = render(request, "web/index.html", context=context)
    return response

def dashboard_view(request):
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
def auth_login_view(request):
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
        'attrs': {'id': 'form-login', 'action': 'javascript:submitLogin(\'form-login\');', 'method': 'post',},
        'buttons': [{'attrs': {'type': 'submit', 'value': 'login', 'class': 'btn btn-primary col-12', 'disabled': True,}, 'content': _('Login')}],
        'modal': {
            'attrs': {'class': 'modal', 'id': 'modal-login', 'tabindex': -1, 'offscreen': 'top',},
            'header': {
                'icon': 'lock-closed-outline',
                'heading': _('Login'),
                'slug': _('Welcome to Warehauser'),
                # 'close': True, # use the close key to add a close icon to the modal. Not advised for form-login
            },
            'body': {
            },
            'footer': [{
                'tag': 'div',
                'attrs': {'class': 'row form-row w-100 mb-4 text-center'},
                'content': [{'tag': 'a', 'attrs': {'id': 'link-forgot', 'href': '#',}, 'content': _('Forgot your password?'),}]}],
        },
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
        pass

    form = WarehauserAuthForgotPasswordForm(request)
    return render(request, 'auth/reset_password.html', {'form': form})

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

