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

# urls.py

from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

router.register(prefix=r'warehausedefs', viewset=views.WarehauseDefViewSet, basename='warehausedef')
router.register(prefix=r'warehauses',    viewset=views.WarehauseViewSet,    basename='warehause')
router.register(prefix=r'productdefs',   viewset=views.ProductDefViewSet,   basename='productdef')
router.register(prefix=r'products',      viewset=views.ProductViewSet,      basename='product')
router.register(prefix=r'eventdefs',     viewset=views.EventDefViewSet,     basename='eventdef')
router.register(prefix=r'events',        viewset=views.EventViewSet,        basename='event')

urlpatterns = [
    path('auth/login/', views.auth_login_view, name='auth_login'),
    path('auth/logout/', views.auth_logout_view, name='auth_logout'),
    path('auth/forgot_password/', views.auth_forgot_password_view, name='auth_forgot_password'),
    path('auth/change_password/', views.auth_change_password_view, name='auth_change_password'),
    path('auth/profile/', views.auth_user_profile_view, name='auth_user_profile'),
    path('api/', include(router.urls)),
    path('', views.home_view, name='home'),
]
