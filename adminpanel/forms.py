from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from .models import Usuario


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email', 
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Digite seu email'
        })
    )
    password = forms.CharField(
        label='Senha', 
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Digite sua senha'
        })
    )
    
    
class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        label='Email', 
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Digite seu email'
        })
    )
    nome = forms.CharField(
        label='Nome', 
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Digite seu nome completo'
        })
    )
    password1 = forms.CharField(
        label='Senha', 
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Digite uma senha segura'
        })
    )
    password2 = forms.CharField(
        label='Confirme a senha', 
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Confirme sua senha'
        })
    )
    
    class Meta:
        model = Usuario
        fields = ['email', 'nome', 'password1', 'password2']
        

class PerfilForm(forms.ModelForm):
    nome = forms.CharField(
        label='Nome', 
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Digite seu nome completo'
        })
    )
    email = forms.EmailField(
        label='Email', 
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Digite seu email'
        })
    )
    
    class Meta:
        model = Usuario
        fields = ['nome', 'email']


class AlterarSenhaForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Senha atual', 
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Digite sua senha atual'
        })
    )
    new_password1 = forms.CharField(
        label='Nova senha', 
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Digite uma nova senha segura'
        })
    )
    new_password2 = forms.CharField(
        label='Confirme a nova senha', 
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm placeholder-gray-400 transition-colors',
            'placeholder': 'Confirme sua nova senha'
        })
    )
