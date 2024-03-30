# Copyright 2024 stingermissile @ github.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
URL configuration for warehauser project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin

from django.urls import path, re_path, include
from django.utils import timezone
from rest_framework import routers, serializers, viewsets

# class AbstractSerializer(serializers.ModelSerializer):
#     def update(self, instance, validated_data):
#         for key in validated_data:
#             if key == 'updated_at':
#                 continue
#             instance.__dict__[key] = validated_data.get(key, instance.__dict__[key])
#         instance.updated_at = timezone.now()
#         instance.save()
#         return instance

# # Serializers define the API representation.
# class UserSerializer(AbstractSerializer):
#     # class Meta:
#     #     model = User
#     #     exclude = ['password',]

#     class Meta:
#         model = User
#         fields = ['url', 'username', 'first_name', 'last_name', 'email', 'is_staff']

# # ViewSets define the view behavior.
# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

# Routers provide an easy way of automatically determining the URL conf.
# router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include('core.urls')),
    # path('auth/', include('django.contrib.auth.urls')),
    # path('admin/login/', login_view),
    # path('admin/logout/', logout_view),
    # path('auth/', include('secure.urls')),
    path('admin/', admin.site.urls),
    # path('api/', include(router.urls)),

    # path('api/', include('rest_framework.urls', namespace='rest_framework')),
    # path('admin/', include(router.urls)),
]

admin.site.site_header = "Warehauser Admin"
admin.site.site_title = "Warehauser Admin Portal"
admin.site.index_title = "Welcome to Warehauser Portal"

# print(include('rest_framework.urls', namespace='rest_framework'))
# print(admin.site.urls)
