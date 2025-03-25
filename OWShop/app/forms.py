"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))


class PoolForm(forms.Form):
    rating_overall = forms.IntegerField(label='Общая оценка сайта (1-5)', min_value=1, max_value=5)
    rating_design = forms.IntegerField(label='Оценка оказанных услуг (1-5)', min_value=1, max_value=5)
    rating_content = forms.IntegerField(label='Оценка техподдержки (1-5)', min_value=1, max_value=5)
    features_liked = forms.CharField(label='Какой товар был приобретен?', widget=forms.Textarea)
    features_improve = forms.CharField(label='Что можно улучшить?', widget=forms.Textarea)
    newsletter = forms.BooleanField(label='Подписаться на рассылку новостей?', required=False)
    contact_method = forms.ChoiceField(label='Как с вами связаться?', choices=[('email', 'Email'), ('phone', 'Телефон')])
