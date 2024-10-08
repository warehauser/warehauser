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

from . import views

urlpatterns = [
    # path('auth/login/', views.auth_login_view, name='auth_login_view'),
    # path('auth/logout/', views.auth_logout_view, name='auth_logout_view'),
    path('auth/forgot/', views.auth_forgot_password_view, name='auth_forgot_password_view'),
    path('auth/change_password/', views.auth_change_password_view, name='auth_change_password_view'),
    path('auth/profile/', views.auth_user_profile_view, name='auth_user_profile_view'),
    path('auth/revoke/<int:user>/<str:otp>/', views.auth_otp_revoke_view, name='auth_otp_revoke_view'),
    path('auth/revoke/<int:user>/', views.auth_otp_revoke_view, name='auth_otp_revoke_manual_view'),
    path('auth/accept/<int:user>/<str:otp>/', views.auth_otp_accept_view, name='auth_otp_accept_view'),
    path('auth/accept/<int:user>/', views.auth_otp_accept_view, name='auth_otp_accept_manual_view'),
    path('', views.home_view, name='home_view'),
    path('c/', views.client_list_view, name='client_list_view'),
    path('c/<str:client>/warehauses/', views.client_detail_view, name='client_detail_view'),
    path('form/web/logout/', views.app_form_router, {'app': 'web', 'name': 'logout',}, name='auth_logout_view'),
    path('form/<str:app>/<str:name>/', views.app_form_router, name='form_router'),

    # path('client-groups/', views.client_groups_view, name='client_groups'),
    # path('groups/<str:group_name>/', views.group_detail_view, name='group_detail'),
    # path('auth/modal/<str:name>/', views.app_form_router, {'app': 'auth'}, name='auth_app_form_router_view'),
    # path('modal/<str:name>/', views.form_router, name='form_router_view'),

    # path('testform/', views.testform, name='testform'),
]
