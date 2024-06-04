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
from django.shortcuts import render, redirect, get_object_or_404
from django.templatetags.static import static
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils import translation

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .decorators import *
from .filters import *
from .forms import *
from .models import *
from .permissions import *
from .serializers import *
from .utils import *

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

# from django.forms.boundfield import BoundField

# def apply_patches():
#     print('Applying patches')
#     if not getattr(BoundField.css_classes, 'patched', False):
#         unpatched = BoundField.css_classes

#         def css_classes(self, extra_classes=None):
#             return unpatched(self, ['form-field'] + (extra_classes or []))

#         BoundField.css_classes = css_classes
#         BoundField.css_classes.patched = True




def home_view(request):

    login_form = AuthenticationForm(auto_id="%s")
    login_form.fields['username'].widget.attrs.update({'autocomplete': 'off', 'css_classes': 'row form-row mb-4'})
    login_form.fields['password'].widget.attrs.update({'autocomplete': 'off', 'css_classes': 'row form-row mb-4'})

    login_form.id = 'form-login'
    login_form.onsubmit = f'submit_login_form(\'{login_form.id}\')'
    login_form.header = {
        'icon': 'lock-closed-outline',
        'heading': _('Login'),
        'slug': _('Welcome to Warehauser'),
    }
    login_form.footer = [{'classlist': 'row form-row center mb-5', 'content': mark_safe('<a id="link-forgot" href="#">Forgot your password?</a>'),},]

    password_reset_form = WarehauserAuthForgotPasswordForm(auto_id="%s")
    password_reset_form.id = 'form-password-reset'
    password_reset_form.card = {
        'classList': 'invisible',
        'onload': mark_safe('animate_move_element_dismiss_right("card-form-password-reset",0,"linear")'),
    }
    password_reset_form.onsubmit = f'submit_password_reset_form(\'{password_reset_form.id}\')'
    password_reset_form.header = {
        'icon': 'lock-closed-outline',
        'heading': _('Forgot Password'),
        'slug': _('Let\'s fix that'),
    }

    context = {
        'title': generate_page_title('Welcome'),
        'forms': [password_reset_form, login_form,],
    }

    response = render(request, "core/dashboard.html", context=context)
    return response

@login_required
def home_view2(request):
    context = {
        'title': BASE_TITLE
    }
    return render(request, "core/index.html", context=context)

# Authentication views







from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from .forms import WarehauserAuthLoginForm

@anonymous_required
def auth_login_view(request):
    if request.method.lower() == 'post':
        form = WarehauserAuthLoginForm(None, data=request.POST)
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

    return render(request, 'core/forms/login.html', {'form': form})

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
        return _auth_otp_form(request=request, title=_(f'{action.title()} Action'), err=f'Too many attempts. Wait {minutes} minutes before retrying.')

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


# Model view sets

class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = get_user_model()
    permission_classes = [AllowAny]

class WarehauserBaseViewSet(viewsets.ModelViewSet):
    lookup_field = 'id'
    permission_classes = [WarehauserPermission,]
    renderer_classes = [JSONRenderer,]
    search_fields = ['id', 'external_id', 'options__values__contains', 'value', 'descr', 'owner']

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]

    def _protect_fields(self, data):
        # Prevent altering id, updated_at, or created_at fields
        for field in ['id', 'owner', 'updated_at', 'created_at']:
            if field in data:
                raise ValidationError(
                    {'error': _(f'Cannot set autogenerated field \'{field}\'.')}
                )

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user

        # If the user is staff or superuser, they can see all objects
        if user.is_staff or user.is_superuser:
            return self.serializer_class.Meta.model.objects.all().order_by('created_at', 'updated_at')

        # Otherwise, only show objects the user has access to
        return self.serializer_class.Meta.model.objects.filter(owner__in=user.groups.all()).order_by('created_at', 'updated_at')

    def create(self, request, *args, **kwargs):
        data = request.data
        self._protect_fields(data)

        # Retrieve the user's group that starts with 'client_'
        group = filter_owner_groups(request.user.groups).first()
        if not group:
            raise ValidationError({'error': _('User is not a member of any client group.')})

        # Set the owner field to the retrieved group
        data['owner'] = group.id

        # return super().create(request, *args, **kwargs)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data

        self._protect_fields(data=data)

        # Check for field changes
        has_changed = False
        for key, value in data.items():
            attr = getattr(instance, key, None)
            if isinstance(attr, dict) and isinstance(value, dict):
                # Update the JSONField attribute
                json = getattr(instance, key, {})
                json.update(value)
                setattr(instance, key, json)
                has_changed = True
            elif attr != value:
                # Update regular field
                setattr(instance, key, value)
                has_changed = True

        if has_changed:
            instance.updated_at = timezone.now()
            instance.save()

            return Response(
                {'message': _(f'[Update]: {instance.__class__.__name__} {instance.id} updated.')},
                status=status.HTTP_200_OK
            )

        return Response(
            {'message': _(f'[Update]: {instance.__class__.__name__} {instance.id} no change.')},
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
        except ObjectDoesNotExist as e:
            return Response(data={'message': e.detail}, status=e.code)
        return Response(status=status.HTTP_204_NO_CONTENT)

class WarehauserDefinitionViewSet(WarehauserBaseViewSet):
    def _do_spawn(self, request, *args, **kwargs):
        dfn = self.get_object()
        data = request.data

        instance = dfn.create_instance(data)
        instance.save()

        return instance

    @action(detail=True, methods=['post'])
    def do_spawn(self, request, *args, **kwargs):
        instance = self._do_spawn(request=request)

        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

class WarehauserInstanceViewSet(WarehauserBaseViewSet):
    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


# WAREHAUSE viewsets

class WarehauseDefViewSet(WarehauserDefinitionViewSet):
    serializer_class = WarehauseDefSerializer
    filterset_class = WarehauseDefFilter

class WarehauseViewSet(WarehauserInstanceViewSet):
    serializer_class = WarehauseSerializer
    filterset_class = WarehauseFilter


# PRODUCT viewsets

class ProductDefViewSet(WarehauserDefinitionViewSet):
    serializer_class = ProductDefSerializer
    filterset_class = ProductDefFilter

    @action(detail=True, methods=['get'], url_path='warehauses')
    def get_warehauses(self, request, id=None):
        product_def = self.get_object()
        warehauses = product_def.warehauses.all()
        serializer = WarehauseSerializer(warehauses, many=True)
        return Response(serializer.data)

class ProductViewSet(WarehauserInstanceViewSet):
    serializer_class = ProductSerializer
    filterset_class = ProductFilter


# EVENT viewsets

class EventDefViewSet(WarehauserDefinitionViewSet):
    serializer_class = EventDefSerializer
    filterset_class = EventDefFilter

    @action(detail=True, methods=['post'])
    def do_spawn(self, request, *args, **kwargs):
        instance = super()._do_spawn(request=request)

        if not instance.is_batched:
            # process immediately
            instance.process()
        else:
            instance.save()

        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EventViewSet(WarehauserInstanceViewSet):
    serializer_class = EventSerializer
    filterset_class = EventFilter
