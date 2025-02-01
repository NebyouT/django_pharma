from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Medicine, Sale, Role, PharmacyUser

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = PharmacyUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'address']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = PharmacyUser
        fields = ['first_name', 'last_name', 'email', 'role', 'phone_number', 'address']

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['code', 'item_description', 'unit', 'received_from', 'quantity',
                 'batch_number', 'expiry_date', 'receiving_date', 'balance',
                 'unit_price', 'selling_price']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'receiving_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['medicine', 'quantity', 'payment_method']

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'description']
