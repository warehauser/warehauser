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

from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('web.urls')),
]


urlpatterns += i18n_patterns(
    path('', include('web.urls'))
)

admin.site.site_header = "Warehauser Admin"
admin.site.site_title = "Warehauser Admin Portal"
admin.site.index_title = "Welcome to Warehauser Portal"
