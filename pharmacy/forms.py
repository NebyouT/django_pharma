from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Medicine, Sale, MedicineInventory, Role, PharmacyUser

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserRegistrationForm(UserCreationForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = PharmacyUser
        fields = ('username', 'email', 'role', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and PharmacyUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'
    )

    class Meta:
        model = PharmacyUser
        fields = ('username', 'email', 'role', 'first_name', 'last_name', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and PharmacyUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['code', 'item_description', 'quantity', 'unit_price', 'selling_price', 'expiry_date', 'displayed_quantity']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'item_description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'displayed_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['medicine', 'quantity', 'total_price']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        medicine = cleaned_data.get('medicine')
        quantity = cleaned_data.get('quantity')

        if medicine and quantity:
            if quantity > medicine.quantity:
                raise forms.ValidationError('Insufficient stock available.')
            cleaned_data['total_price'] = medicine.selling_price * quantity

        return cleaned_data

class MedicineInventoryForm(forms.ModelForm):
    class Meta:
        model = MedicineInventory
        fields = ['medicine', 'quantity', 'unit_price', 'total_price']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')

        if quantity and unit_price:
            cleaned_data['total_price'] = quantity * unit_price

        return cleaned_data

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'description']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-control'}, choices=Role.ROLE_CHOICES),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
