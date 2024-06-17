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

# forms.py

from django import forms
from django.core.validators import RegexValidator
# from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm#, ReadOnlyPasswordHashField, PasswordResetForm
from django.utils.translation import gettext as _

# from django.utils.html import format_html

from core.models import CHARFIELD_MAX_LENGTH
from .renderers import WarehauserRendererMixin













# <form>
#     <div class="modal" id="modal-login" tabindex="-1" offscreen="top">
#         <div class="modal-dialog">
#             <div class="modal-content">
#                 <div class="modal-header">
#                     <div class="w-100 text-center">
#                         <ion-icon class="form-icon mt-4" name="lock-closed-outline"></ion-icon>
#                         <h2>Login</h2>
#                         <p class="modal-header-slug">Welcome to Warehauser</p>
#                     </div>
#                     <ion-icon class="modal-close-icon" name="close-circle-outline"></ion-icon>
#                 </div>
#                 <div class="modal-body">
#                     {{ form.as_modal }}
#                 </div>
#                 <div class="modal-footer">
#                     <button type="button" class="btn btn-secondary" id="closeModalButton">Close</button>
#                 </div>
#             </div>
#         </div>
#     </div>
#     {% csrf_token %}
# </form>





class WarehauserFormMixin(WarehauserRendererMixin):
    # @debug_func
    def _generate_html_input(self, name:str, field):
        attrs = {'id': name.lower(), 'name': name.lower(), 'type': field.widget.input_type,}
        attrs.update(field.widget.attrs)

        tags = {
            'tag': 'div',
            'attrs': {'class': 'row form-row mt-3',},
            'content': [{
                'tag': 'div',
                'attrs': {'class': 'input-box',},
                'content': [{
                    'tag': 'input',
                    'attrs': attrs,
                },
                {
                    'tag': 'span',
                    'attrs': {'class': 'label',},
                    'content': _(name),
                },
                *([{
                    'tag': 'div',
                    'attrs': {
                        'class': 'input-text-button',
                    },
                    'content': [{
                        'tag': 'ion-icon',
                        'attrs': {'id': f'{name}-toggle', 'name': 'eye-off-outline', 'onclick': f'passwordShowHide(this, \'{name}\', 4000);',},
                        'content': '',
                    },],
                }] if field.widget.__class__.__name__.lower() == 'passwordinput' else []),
                *([{
                    'tag': 'div',
                    'attrs': {
                        'class': 'required',
                        'data-bs-toggle': 'tooltip',
                        'data-bs-placement': 'left',
                        'data-bs-title': 'Required',
                    },
                    'content': '',
                }] if field.widget.attrs.get('required', False) else []),
                {
                    'tag': 'div',
                    'attrs': {'class': 'error error-message', 'id': f'error-{name}',},
                    'content': '',
                },
            ],},],
        }

        return tags

    # @debug_func
    def _generate_modal_header(self, data):
        content = []

        try:
            header = data['modal']['header']
        except KeyError as ke:
            pass

        if header:
            if 'icon' in header:
                value = header['icon']
                content.append(self._generate_tag(tag='ion-icon', attrs={'class': 'form-icon mt-4', 'name': value,}, content=''))

            if 'heading' in header:
                value = header['heading']
                if value:
                    content.append(self._generate_tag(tag='h2', attrs=None, content=value))

            if 'slug' in header:
                value = header['slug']
                content.append(self._generate_tag(tag='p', attrs={'class': 'modal-header-slug',}, content=value))

            if 'close' in header:
                content.append(self._generate_tag(tag='ion-icon', attrs={'class': 'modal-close-icon', 'name': 'close-circle-outline', 'role': 'img',}, content=''))

        content = self._generate_tag(tag='div', attrs={'class': 'w-100 text-center'}, content=content)
        content = self._generate_tag(tag='div', attrs={'class': 'modal-header'}, content=content)

        return content

    # @debug_func
    def _generate_button(self, button):
        attrs = button['attrs'] if button and 'attrs' in button else {}
        content = button['content'] if button and 'content' in button else ''
        content = self._generate_tag(tag='button', attrs=attrs, content=content)
        content = self._generate_tag(tag='div', attrs={'class': 'button-row'}, content=content)
        return self._generate_tag(tag='div', attrs={'class': 'row form-row mt-4'}, content=content)

    # @debug_func
    def _generate_modal_body(self, data):
        content = [self._generate_html_input(name, field) for name, field in self.fields.items()]
        content = content + [self._generate_button(button) for button in data['buttons']]
        return self._generate_tag(tag='div', attrs={'class': 'modal-body',}, content=content)

    # @debug_func
    def _generate_modal_footer(self, data):
        try:
            footer = data['modal']['footer']
        except KeyError as ke:
            footer = None
        return self._generate_tag(tag='div', attrs={'class': 'modal-footer',}, content=footer)

    def as_modal(self, data):
        content = [self._generate_modal_header(data), self._generate_modal_body(data), self._generate_modal_footer(data)]
        content = self._generate_tag(tag='div', attrs={'class': 'modal-content'}, content=content)
        content = self._generate_tag(tag='div', attrs={'class': 'modal-dialog'}, content=content)
        content = self._generate_tag(tag='div', attrs=data['modal']['attrs'], content=content)
        content = self._generate_tag(tag='form', attrs=data['attrs'], content=content)

        return self._render_bs4(self._render_tags([content]))

class WarehauserAuthLoginForm(AuthenticationForm, WarehauserFormMixin):
    # id:str = 'form-login'

    def __init__(self, *args, **kwargs):
        self.csrf_token = kwargs.pop('csrf_token', None)
        super().__init__(*args, **kwargs)

        # Customize form fields here if needed
        self.fields['username'].widget.attrs.update({
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
        })

        self.fields['password'].widget.attrs.update({
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
        })

class WarehauserAuthForgotPasswordForm(forms.Form, WarehauserFormMixin):
    # id:str = 'form-password-reset'

    def __init__(self, *args, **kwargs):
        self.csrf_token = kwargs.pop('csrf_token', None)
        super().__init__(*args, **kwargs)

    email = forms.EmailField(
        label=_("Email"),
        max_length=CHARFIELD_MAX_LENGTH,
        widget=forms.EmailInput(attrs={
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
            'css_classes': 'row form-row mb-4',
        }),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'id': 'new-password',
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
            'css_classes': 'row form-row mb-4',
        }),
    )
    confirm = forms.CharField(
        label=_("Confirm"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'id': 'confirm',
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
            'css_classes': 'row form-row mb-4',
        }),
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

class WarehauserPasswordChangeForm(PasswordChangeForm):
    error_messages = {
        'password_incorrect': _("Incorrect current password."),
        'password_mismatch': _("The password and confirm password fields did not match."),
    }

    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'old_password', 'placeholder': _('Current Password'), 'autofocus': True, 'autocomplete': 'off'}),
    )
    new_password1 = forms.CharField(
        label=_("New password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'new_password1', 'placeholder': _('Password'), 'autocomplete': 'off'}),
    )
    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'new_password2', 'placeholder': _('Confirm Password'), 'autocomplete': 'off'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return new_password2

otp_validator = RegexValidator(r'^[A-Za-z0-9]$', 'OTP must be a single alphanumeric character.')

class WarehauserOTPChallengeForm(forms.Form):
    otp1 = forms.CharField(max_length=1, validators=[otp_validator], widget=forms.TextInput(attrs={'class': 'form-control otp', 'id': 'otp1', 'autocomplete': 'off', 'autofocus': True,}))
    otp2 = forms.CharField(max_length=1, validators=[otp_validator], widget=forms.TextInput(attrs={'class': 'form-control otp', 'id': 'otp2', 'autocomplete': 'off'}))
    otp3 = forms.CharField(max_length=1, validators=[otp_validator], widget=forms.TextInput(attrs={'class': 'form-control otp', 'id': 'otp3', 'autocomplete': 'off'}))
    otp4 = forms.CharField(max_length=1, validators=[otp_validator], widget=forms.TextInput(attrs={'class': 'form-control otp', 'id': 'otp4', 'autocomplete': 'off'}))
    otp5 = forms.CharField(max_length=1, validators=[otp_validator], widget=forms.TextInput(attrs={'class': 'form-control otp', 'id': 'otp5', 'autocomplete': 'off'}))
    otp6 = forms.CharField(max_length=1, validators=[otp_validator], widget=forms.TextInput(attrs={'class': 'form-control otp', 'id': 'otp6', 'autocomplete': 'off'}))

    def clean(self):
        cleaned_data = super().clean()
        otp_combined = self.get_otp_combined()
        if len(otp_combined) != 6:
            raise forms.ValidationError('Invalid attempt.')
        return cleaned_data

    def get_otp_combined(self):
        otp_combined = ''.join(self.cleaned_data.get(f'otp{i}', '') for i in range(1, 7))
        return otp_combined

    def layout(self, *args, **kwargs):
        """
        Define the layout of form fields for WarehauserOTPChallengeForm.
        Overrides the layout method from the base class.
        Returns a list of dicts each with a renderer class and a list of fields.
        """
        return [{'renderer': 'field_renderer_otp', 'fields': self.visible_fields()}]