from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from consultation_app.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'is_blocked')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'is_blocked')