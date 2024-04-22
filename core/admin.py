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

# admin.py

from django.conf import settings
from django.utils.translation import gettext as _

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group

from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import get_objects_for_user

from .models import WarehauseDef, Warehause, ProductDef, Product, EventDef, Event

class CustomUserAdmin(UserAdmin):
    readonly_fields = ('user_permissions', 'date_joined', 'last_login',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'groups')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name',),
        }),
    )

    list_display = ('email', 'first_name', 'last_name',)
    search_fields = ('email', 'first_name', 'last_name',)
    ordering = ('email', 'first_name', 'last_name',)

    def get_fieldsets(self, request, obj=None):
        if obj:
            if isinstance(obj, User):
                return self.fieldsets
        else:
            return self.add_fieldsets

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class CustomGroupAdmin(GroupAdmin):
    pass

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)

def is_staff(user):
    return user.groups.filter(name=settings.WAREHAUSER_USER_GROUP).exists()

def is_superuser(user):
    return user.groups.filter(name=settings.WAREHAUSER_ADMIN_GROUP).exists()

# Convenience mixin for read only permission override for admin site for all but superusers...
class WarehauserReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return is_superuser(request.user)

    def has_change_permission(self, request, obj=None):
        return is_superuser(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_superuser(request.user)

    def has_view_permission(self, request, obj=None):
        return is_superuser(request.user)

class WarehauserAdmin(GuardedModelAdmin):
    list_display = ('descr', 'barcode',)
    readonly_fields = ('created_at', 'updated_at',)
    ordering = ('id',)

    # def has_add_permission(self, request, obj=None):
    #     return self.has_permission(request=request, obj=obj, action='add')

    # def has_change_permission(self, request, obj=None):
    #     return self.has_permission(request=request, obj=obj, action='change')

    # def has_delete_permission(self, request, obj=None):
    #     return self.has_permission(request=request, obj=obj, action='delete')

    # def has_view_permission(self, request, obj=None):
    #     return self.has_permission(request=request, obj=obj, action='view')

    # def has_module_permission(self, request):
    #     if is_superuser(request.user):
    #         return True
    #     return self.get_model_objects(request=request).exists()

    # def has_permission(self, request, obj, action):
    #     user = request.user

    #     if is_superuser(user):
    #         return True

    #     opts = self.opts
    #     perm = f'{opts.app_label}.{action}_{opts.model_name}'

    #     if obj:
    #         print('In WarehauserAdmin.has_permission!')
    #         return user.has_perm(perm, obj)
    #     else:
    #         print(f'In WarehauserAdmin.has_permission WITH NO OBJ! perm is {perm}')
    #         return True

    def get_model_objects(self, request, action=None, klass=None):
        opts = self.opts
        actions = [action] if action else ['change', 'delete', 'view']
        klass = klass if klass else opts.model
        perms = [f'{perm}_{klass._meta.model_name}' for perm in actions]
        res = get_objects_for_user(user=request.user, klass=klass, perms=perms, any_perm=True, with_superuser=False)
        return res

    def get_queryset(self, request):
        if is_superuser(request.user):
            return super().get_queryset(request=request)

        res = self.get_model_objects(request=request)
        return res

@admin.register(WarehauseDef)
class WarehauseDefAdmin(WarehauserAdmin):
    pass

@admin.register(Warehause)
class WarehauseAdmin(WarehauserAdmin):
    pass

@admin.register(ProductDef)
class ProductDefAdmin(WarehauserAdmin):
    pass

@admin.register(Product)
class ProductAdmin(WarehauserAdmin):
    pass

@admin.register(EventDef)
class EventDefAdmin(WarehauserAdmin):
    pass

@admin.register(Event)
class EventAdmin(WarehauserAdmin):
    readonly_fields = ('created_at', 'updated_at', 'proc_start', 'proc_end',)
