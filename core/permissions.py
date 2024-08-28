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

from .models import Client

# Permission classes here.

class WarehauserPermission(BasePermission):
    def has_permission(self, request, view):
        user: User = request.user
        return user and user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Check if the user is staff or superuser
        if user.is_staff or user.is_superuser:
            return True

        # Check if the user is a member of the group associated with the client's owner
        client = Client.objects.filter(group__in=user.groups.all()).first()
        return client and obj.owner == client

class IsSuperuser(IsAuthenticated):
    """
    Allows access only to superusers.
    """
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and user.is_superuser
