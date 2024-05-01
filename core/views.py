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
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import JSONField
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext as _

from django_filters.rest_framework import DjangoFilterBackend
from guardian.shortcuts import get_objects_for_user, assign_perm

from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from .decorators import *
from .filters import *
from .forms import *
from .models import *
from .permissions import *
from .templatetags.renderers import field_renderer_default, field_renderer_otp, render_fields
from .serializers import *

from .utils import generate_otp_code

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

@login_required
def home_view(request):
    context = {
        'title': BASE_TITLE
    }
    return render(request, "core/index.html", context=context)

# Authentication views

@anonymous_required
def auth_login_view(request):
    autofocus_field = None
    select_text = False

    if request.method.lower() == 'post':
        form = WarehauserAuthLoginForm(request, data=request.POST)

        is_valid = form.is_valid()
        if is_valid:
            login(request, form.get_user())

            # Redirect to a success page or any other view
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('home')  # Redirect to home if 'next' is not set
        else:
            messages.error(request, 'Invalid username or password.')
            first_visible_field = form.visible_fields()[0] if form.visible_fields() else None
            if first_visible_field and first_visible_field.field.widget.input_type != 'select' and first_visible_field.value():
                autofocus_field = first_visible_field.auto_id  # Autofocus the field by its auto_id
                select_text = True  # Set select_text to True to select all text in the field
    else:
        form = WarehauserAuthLoginForm(request)

    template = 'core/form.html'
    form.id = 'login-form'

    context = {
        'title': generate_page_title(_('Log In')),
        'form': form,
        'autofocus_field': autofocus_field,
        'renderers': {
            'field_renderer_default': field_renderer_default,
        },
        'select_text': select_text,
        'title': _('Login'),
        'illustration': 'icon ion-ios-locked-outline',
        'buttons': [
            {'title': _('Login'), 'attrs': generate_button_attributes({'id': 'submit', 'value': 'login', 'type': 'submit',})},
            {'title': _('Forgot Password'), 'type': 'href', 'attrs': generate_button_attributes({'id': 'forgot', 'href': 'auth_forgot_password_view', 'class': 'btn btn-secondary col-12',})},
        ],
    }

    return render(request, template, context)

def auth_logout_view(request):
    auth_logout(request=request)
    return redirect('auth_login_view')

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
        'renderers': {
            'field_renderer_default': field_renderer_default,
        },
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
        'renderers': {
            'field_renderer_otp': field_renderer_otp,
        },
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
    permission_classes = [IsAuthenticated, WarehauserPermission,]
    renderer_classes   = [JSONRenderer,]
    search_fields      = ['id', 'external_id', 'options__barcodes__contains', 'barcode', 'descr',]
    lookup_field       = 'id'

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]

    def create(self, request, *args, **kwargs):
        self._protect_fields(data=request.data)
        instance = super().create(request=request, *args, **kwargs)

        self._grant_all_admin_permissions(user=request.user, instance=instance)
        return instance

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data

        self._protect_fields(data=data)

        # Check for field changes
        has_changed = False
        for key, value in data.items():
            # Check if the instance's current 'key' attribute is a JSONField
            attr = getattr(instance, key, None)
            if isinstance(attr, JSONField):
                # Update the JSONField attribute
                json = getattr(instance, key, dict())
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
                {"message": f"[Update]: {instance.__class__.__name__} {instance.id} updated."},
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": f"[Update]: {instance.__class__.__name__} {instance.id} no change."},
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

    # def list(self, request):
    #     return super().list(request=request)

    # def retrieve(self, request, *args, **kwargs):
    #     pass

    def _protect_fields(self, data):
        # Prevent altering id, updated_at, or created_at fields
        disallowed_fields = ['id', 'updated_at', 'created_at']
        for field in disallowed_fields:
            if field in data:
                return Response(
                    {"error": f"Cannot change autogenerated field '{field}'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

    def _grant_all_admin_permissions(self, user, instance):
        # Give client admin users full permissions for object.
        codename = type(instance).__name__.lower()
        groups = user.groups.filter(name__startswith='warehauser_', name__endswith='_admin')
        if groups.exists():
            for group in groups:
                assign_perm(f'view_{codename}', group, instance)
                assign_perm(f'change_{codename}', group, instance)
                assign_perm(f'delete_{codename}', group, instance)

class WarehauserDefinitionViewSet(WarehauserBaseViewSet):
    def create(self, request, *args, **kwargs):
        instance = super().create(request=request, *args, **kwargs)
        codename = type(instance).__name__.lower()

        # Definition objects only allow non admin users to view.
        groups = request.user.groups.filter(name__startswith='warehauser_', name__endswith='_user')
        if groups.exists():
            for group in groups:
                assign_perm(f'view_{codename}', group, instance)

        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def do_spawn(self, request, *args, **kwargs):
        dfn = self.get_object()
        data = request.data

        instance = dfn.create_instance(data)
        instance.save()

        self._grant_all_admin_permissions(user=request.user, instance=instance)

        # Give client users full permissions for instance
        codename = type(instance).__name__.lower()
        groups = request.user.groups.filter(name__startswith='warehauser_', name__endswith='_user')
        if groups.exists():
            for group in groups:
                assign_perm(f'view_{codename}', group, instance)
                assign_perm(f'change_{codename}', group, instance)
                assign_perm(f'delete_{codename}', group, instance)

        return instance

class WarehauserInstanceViewSet(WarehauserBaseViewSet):
    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


# WAREHAUSE viewsets

class WarehauseDefViewSet(WarehauserDefinitionViewSet):
    serializer_class = WarehauseDefSerializer

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = WarehauseDefFilter

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        return get_objects_for_user(user, 'core.warehausedef', klass=queryset).order_by('created_at', 'updated_at',)

    @action(detail=True, methods=['post'])
    def do_spawn(self, request, *args, **kwargs):
        instance = super().do_spawn(request, *args, **kwargs)

        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

class WarehauseViewSet(WarehauserInstanceViewSet):
    serializer_class = WarehauseSerializer

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = WarehauseFilter

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        return get_objects_for_user(user, 'core.warehause', klass=queryset).order_by('created_at', 'updated_at',)


# PRODUCT viewsets

class ProductDefViewSet(WarehauserDefinitionViewSet):
    serializer_class = ProductDefSerializer

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = ProductDefFilter

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        return get_objects_for_user(user, 'core.productdef', klass=queryset).order_by('created_at', 'updated_at',)

    @action(detail=True, methods=['get'], url_path='warehauses')
    def get_warehauses(self, request, id=None):
        product_def = self.get_object()
        warehauses = product_def.warehauses.all()
        serializer = WarehauseSerializer(warehauses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def do_spawn(self, request, *args, **kwargs):
        instance = super().do_spawn(request, *args, **kwargs)

        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProductViewSet(WarehauserInstanceViewSet):
    serializer_class = ProductSerializer

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = ProductFilter

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        return get_objects_for_user(user, 'core.product', klass=queryset).order_by('created_at', 'updated_at',)


# EVENT viewsets

class EventDefViewSet(WarehauserDefinitionViewSet):
    serializer_class = EventDefSerializer

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = EventDefFilter

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        return get_objects_for_user(user, 'core.eventdef', klass=queryset).order_by('created_at', 'updated_at',)

    @action(detail=True, methods=['post'])
    def do_spawn(self, request, *args, **kwargs):
        instance = super().do_spawn(request, *args, **kwargs)

        if not instance.is_batched:
            # process immediately
            instance.process()
        else:
            instance.save()

        serializer = self.serializer_class(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EventViewSet(WarehauserInstanceViewSet):
    serializer_class = EventSerializer

    # API filtering
    filter_backends = [DjangoFilterBackend, SearchFilter,]
    filterset_class = EventFilter

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        return get_objects_for_user(user, 'core.event', klass=queryset).order_by('created_at', 'updated_at',)
