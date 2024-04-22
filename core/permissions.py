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

# permissions.py

from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission, IsAuthenticated

# Permission classes here.

class WarehauserPermission(BasePermission):
    def has_permission(self, request, view):
        method:str = request.method
        user:User  = request.user

        model_name = view.queryset.model.__name__.lower()

        if method in ['GET']:
            return True
        if method in ['POST']:
            return user.has_perm(f'core.add_{model_name}')
        if method in ['PUT', 'PATCH']:
            return user.has_perm(f'core.change_{model_name}')
        if method in ['DELETE']:
            return user.has_perm(f'core.delete_{model_name}')
        return False

    def has_object_permission(self, request, view, obj):         
        method:str = request.method
        user:User  = request.user

        codename = type(obj).__name__.lower()

        if method in ['GET']:
            return user.is_staff or user.has_perm(f'view_{codename}', obj)
        if method in ['PUT', 'PATCH']:
            return user.has_perm(f'change_{codename}', obj)
        if method in ['DELETE']:
            return user.has_perm(f'delete_{codename}', obj)
        return False

class IsSuperuser(IsAuthenticated):
    """
    Allows access only to superusers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser
