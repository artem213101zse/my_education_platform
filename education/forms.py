from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    is_teacher = forms.BooleanField(required=False, label='Являюсь учителем?')

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'is_teacher')