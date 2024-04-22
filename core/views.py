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

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import JSONField
from django.shortcuts import render, redirect, get_object_or_404
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
from .serializers import *

from .utils import is_valid_email, generate_otp_code

# Security code.

# Create your views here.

@login_required
def home_view(request):
    return render(request, "core/index.html")

def auth_login_view(request):
    if request.method == 'POST':
        form = WarehauserAuthLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            if is_valid_email(username):
                user = authenticate(request, email=username, password=password)
            else:
                user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                # Redirect to a success page or any other view
                next_url = request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect('home')  # Redirect to home if 'next' is not set
            else:
                # Authentication failed
                form.add_error(None, 'Invalid username or password.')
    else:
        form = WarehauserAuthLoginForm(request)

    return render(request, 'auth/login.html', {'form': form})

def auth_logout_view(request):
    auth_logout(request=request)
    return redirect('auth_login')

@login_required
def auth_user_profile_view(request):
    return render(request=request, template_name='auth/user_profile.html')

@login_required
def auth_change_password_view(request):
    if request.method == 'POST':
        form = WarehauserAuthChangePasswordForm(data=request.POST)
        if form.is_valid():
            pass
    else:
        form = WarehauserAuthChangePasswordForm(request)

    return render(request, 'auth/reset_password.html', {'form': form})

@anonymous_required
def auth_forgot_password_view(request):
    if request.method == 'POST':
        form = WarehauserAuthForgotPasswordForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password1 = form.cleaned_data.get('password1')
            password2 = form.cleaned_data.get('password2')
            if is_valid_email(email) is False:
                form.add_error(None, 'Email is not of a valid format.')
            elif password1 != password2:
                form.add_error(None, 'Passwords do not match.')
            else:
                # Store password in session and send confirmation email...
                otp = generate_otp_code(length=6)
    # <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    # <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    # <meta name="viewport" content="width=device-width, initial-scale=1.0">

                content = f"""
<!doctype html>
<html lang="en-us">
  <head>
    <title>Forgot Password - Warehauser : Your Warehouse Done Smoothly</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <link rel="stylesheet" href="/static/core/css/warehauser.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/ionicons/2.0.1/css/ionicons.min.css">
  </head>
  <body>
    <div class="wrapper">
      <!-- <div class="background-dark"> -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
          <div class="container">
            <a class="navbar-brand" href="/">Warehauser</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
              <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarSupportedContent">
              <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                
              </ul>
              <ul class="navbar-nav">
                
                <li class="nav-item">
                  <a class="nav-link" href="/auth/login">Login</a>
                </li>
                
              </ul>
            </div>
          </div>
        </nav>
        <div id="content" class="main" name="content-box">
        <form>
            <div class="illustration"><i class="icon ion-ios-locked-outline"></i></div>
            <div class="form-row"><input class="form-control" type="text" name="username" id="username" placeholder="Username" autofocus></div>
            <div class="form-row"><input class="form-control" type="password" name="password" id="password" placeholder="Password"></div>
        </form>
        </div>
      <!-- </div> -->
    </div>
    <footer id="footer" class="bg-dark text-center">
      <div class"text-center p-3" style="background-color: rgba(0,0,0,0.2);">
        <a class="text-light" href="https://www.warehauser.org/" style="text-decoration: none;">Powered by warehauser.org</a>
      </div>
    </footer>
    
    <!-- Bootstrap 5 JS and dependencies -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
    <script src="/static/core/js/warehauser.js"></script>
    
  </body>
</html>
{otp}
"""
                send_mail(subject='Warehauser Password Reset Request',
                          message=content,
                          from_email=settings.SEND_MAIL_FROM_ADDRESS,
                          recipient_list=[email,],
                          fail_silently=False)
    else:
        form = WarehauserAuthForgotPasswordForm(request)

    return render(request, 'auth/reset_password.html', {'form': form})


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
