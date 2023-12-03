# chat/forms.py
from django import forms
from .models import Thread, Message

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

class CustomUserAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

    class Meta:
        model = get_user_model()
        fields = ('email', 'password')
        
class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['name']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']