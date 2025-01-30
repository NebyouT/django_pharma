from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Medicine, Sale, PharmacyUser, MedicineInventory

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserRegistrationForm(UserCreationForm):
    id_number = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    id_issue_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    id_expiry_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = PharmacyUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'address', 
                 'id_number', 'date_of_birth', 'id_issue_date', 'id_expiry_date',
                 'user_type', 'password1', 'password2']
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['code', 'item_description', 'unit', 'received_from', 'quantity',
                 'batch_number', 'expiry_date', 'receiving_date', 'balance',
                 'unit_price', 'selling_price']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'item_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'received_from': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'receiving_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer_name', 'medicine', 'quantity']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'medicine': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        medicine = self.cleaned_data.get('medicine')
        
        if quantity and medicine:
            if quantity <= 0:
                raise forms.ValidationError("Quantity must be greater than zero.")
            if quantity > medicine.balance:
                raise forms.ValidationError(f"Insufficient stock. Only {medicine.balance} units available.")
        return quantity

class MedicineInventoryForm(forms.ModelForm):
    class Meta:
        model = MedicineInventory
        fields = ['code', 'item_description', 'unit', 'received_from', 'quantity', 
                 'batch_number', 'expiry_date', 'receiving_date', 'balance', 
                 'unit_price', 'selling_price']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'item_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'received_from': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'receiving_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
