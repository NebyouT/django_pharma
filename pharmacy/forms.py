from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from .models import Medicine, Sale, Role, PharmacyUser

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserRegistrationForm(UserCreationForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Your password must contain at least 8 characters.'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Enter the same password as above, for verification.'
    )

    class Meta:
        model = PharmacyUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'address', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class UserUpdateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Leave empty to keep current password.'
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Enter the same password as above, for verification.'
    )

    class Meta:
        model = PharmacyUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'address']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

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
    payment_method = forms.ChoiceField(
        choices=[('cash', 'Cash'), ('bank', 'Bank Transfer')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='cash'
    )
    bank_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Name'})
    )
    sender_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sender Name'})
    )

    class Meta:
        model = Sale
        fields = ['medicine', 'quantity', 'payment_method', 'bank_name', 'sender_name']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        medicine = cleaned_data.get('medicine')
        quantity = cleaned_data.get('quantity')

        # Calculate total price if we have medicine and quantity
        if medicine and quantity:
            total_price = medicine.selling_price * quantity
            cleaned_data['total_price'] = total_price

            # For cash payments, set bank_name and sender_name
            if payment_method == 'cash':
                cleaned_data['bank_name'] = 'cash'
                cleaned_data['sender_name'] = 'none'
            elif payment_method == 'bank':
                if not cleaned_data.get('bank_name'):
                    self.add_error('bank_name', 'Bank name is required for bank transfers.')
                if not cleaned_data.get('sender_name'):
                    self.add_error('sender_name', 'Sender name is required for bank transfers.')

        return cleaned_data

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'description']
