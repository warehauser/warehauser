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
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils.translation import gettext as _

from core.models import CHARFIELD_MAX_LENGTH

class WarehauserAuthLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        kwargs['auto_id'] = False
        super().__init__(*args, **kwargs)

    username = forms.CharField(
        label=_('Username'),
        max_length=CHARFIELD_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'id': 'username',
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
            'autofocus': 'true',
        }),
    )

    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'id': 'password',
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
        }),
    )

class WarehauserAuthForgotPasswordForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs['auto_id'] = False
        super().__init__(*args, **kwargs)

    email = forms.EmailField(
        label=_("Email"),
        max_length=CHARFIELD_MAX_LENGTH,
        widget=forms.EmailInput(attrs={
            'id': 'email',
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
            'autofocus': 'true',
        }),
    )

    password = forms.CharField(
        label=_("New Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'id': 'password',
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
        }),
    )

    confirm = forms.CharField(
        label=_("Confirm Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'id': 'confirm',
            'placeholder': '',
            'required': 'true',
            'autocomplete': 'off',
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




# class ExampleForm(forms.Form):
#     # Basic Input Types
#     char_field = forms.CharField(widget=forms.TextInput(attrs={}))
#     password_field = forms.CharField(widget=forms.PasswordInput(attrs={}))
#     email_field = forms.EmailField(widget=forms.EmailInput(attrs={}))
#     url_field = forms.URLField(widget=forms.URLInput(attrs={}))
#     number_field = forms.IntegerField(widget=forms.NumberInput(attrs={}))
#     date_field = forms.DateField(widget=forms.DateInput(attrs={}))
#     time_field = forms.TimeField(widget=forms.TimeInput(attrs={}))
#     datetime_field = forms.DateTimeField(widget=forms.DateTimeInput(attrs={}))

#     # File Input
#     file_field = forms.FileField(widget=forms.ClearableFileInput)

#     # Select and Choice Fields
#     choice_field = forms.ChoiceField(choices=[('1', 'First'), ('2', 'Second'), ('3', 'Third')], widget=forms.Select)
#     multiple_choice_field = forms.MultipleChoiceField(choices=[('1', 'First'), ('2', 'Second'), ('3', 'Third')], widget=forms.CheckboxSelectMultiple)

#     # Boolean and Checkbox
#     boolean_field = forms.BooleanField(widget=forms.CheckboxInput)
#     favourite_color = forms.ChoiceField(choices=[('red', _('Red')), ('green', _('Green')), ('blue', _('Blue'))], widget=forms.RadioSelect)

#     # TextArea
#     textarea_field = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 20}))

#     # SlugField
#     slug_field = forms.SlugField(widget=forms.TextInput(attrs={}))
    
#     # Color Input
#     color_field = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}))
    
#     # Hidden Input
#     hidden_field = forms.CharField(widget=forms.HiddenInput, initial="hidden_value")

#     # Custom Widget
#     custom_widget_field = forms.CharField(widget=forms.TextInput(attrs={}))
