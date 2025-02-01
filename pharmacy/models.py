from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import datetime, timedelta

class Role(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('pharmacist', 'Pharmacist'),
        ('cashier', 'Cashier'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()

class PharmacyUser(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})" if self.role else self.get_full_name()

class Medicine(models.Model):
    code = models.CharField(max_length=50, unique=True, blank=True)
    item_description = models.CharField(max_length=255, verbose_name="Item Description")
    unit = models.CharField(max_length=50, default='piece')
    received_from = models.CharField(max_length=255, null=True, blank=True, verbose_name="Received From")
    quantity = models.IntegerField(default=0)
    batch_number = models.CharField(max_length=50, null=True, blank=True, verbose_name="Batch Number")
    expiry_date = models.DateField(verbose_name="Expiry Date")
    receiving_date = models.DateField(default=timezone.now, verbose_name="Receiving Date")
    balance = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Unit Price")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Selling Price")
    displayed_quantity = models.IntegerField(default=0, help_text="Quantity to maintain on shelf")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.code:
            # Get the last medicine object
            last_medicine = Medicine.objects.order_by('-code').first()
            
            if last_medicine and last_medicine.code.startswith('MED'):
                # Extract the number and increment it
                last_number = int(last_medicine.code[3:])
                new_number = last_number + 1
            else:
                # If no existing medicine or invalid format, start with 1
                new_number = 1
            
            # Generate the new code with leading zeros (MED00001)
            self.code = f'MED{new_number:05d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.item_description}"

    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    @property
    def is_low_stock(self):
        return self.quantity <= self.displayed_quantity

    @property
    def is_complete(self):
        """Check if all important fields are filled"""
        return all([
            self.code,
            self.item_description,
            self.unit,
            self.received_from,
            self.quantity is not None,
            self.batch_number,
            self.expiry_date,
            self.balance is not None,
            self.unit_price is not None,
            self.selling_price is not None
        ])

    class Meta:
        verbose_name = 'Medicine'
        verbose_name_plural = 'Medicines'

class PaymentMethod(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
    ]
    
    name = models.CharField(max_length=10, choices=PAYMENT_CHOICES, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()

class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
    ]
    
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')
    created_by = models.ForeignKey(PharmacyUser, on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medicine.code} - {self.quantity} units - {self.get_payment_method_display()}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.medicine.selling_price * self.quantity
        
        # Update medicine balance
        self.medicine.balance -= self.quantity
        self.medicine.save()
        
        super().save(*args, **kwargs)
