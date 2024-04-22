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

# decorators.py

from django.shortcuts import redirect
from django.urls import reverse

def anonymous_required(view_func, redirect_url=None):
    """
    Decorator for views that checks that the user is not authenticated,
    redirecting to the specified URL if necessary.
    """
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            # User is authenticated, redirect to the specified URL
            if redirect_url:
                return redirect(redirect_url)
            else:
                return redirect(reverse('home'))  # Redirect to home or any other URL
        else:
            # User is not authenticated, execute the view function
            return view_func(request, *args, **kwargs)

    return _wrapped_view
