from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.utils import timezone
from datetime import datetime, timedelta

class PharmacyUser(AbstractUser):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('pharmacist', 'Pharmacist'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='pharmacist')
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def is_admin(self):
        return self.user_type == 'admin'

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'

class Medicine(models.Model):
    code = models.CharField(max_length=50, unique=True)
    item_description = models.TextField()
    unit = models.CharField(max_length=50)
    received_from = models.CharField(max_length=200)
    quantity = models.IntegerField()
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    receiving_date = models.DateField()
    balance = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.item_description}"

    @property
    def is_expired(self):
        return self.expiry_date <= timezone.now().date()

    @property
    def total_value(self):
        return self.balance * self.unit_price

class MedicineInventory(models.Model):
    code = models.CharField(max_length=50, unique=True)
    item_description = models.TextField()
    unit = models.CharField(max_length=50)
    received_from = models.CharField(max_length=200)
    quantity = models.IntegerField()
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    receiving_date = models.DateField()
    balance = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.item_description}"

    class Meta:
        verbose_name_plural = 'Medicine Inventory'
        ordering = ['code']

    @property
    def is_expired(self):
        return self.expiry_date <= timezone.now().date()

    @property
    def total_value(self):
        return self.balance * self.unit_price

class Sale(models.Model):
    customer_name = models.CharField(max_length=200)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)
    seller = models.ForeignKey(PharmacyUser, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.customer_name} - {self.medicine.code} - {self.medicine.item_description}"

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.medicine.selling_price * self.quantity
        super().save(*args, **kwargs)
