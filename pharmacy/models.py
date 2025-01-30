from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import datetime, timedelta

class Role(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('pharmacist', 'Pharmacist'),
        ('cashier', 'Cashier'),
        ('inventory', 'Inventory Manager'),
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
    code = models.CharField(max_length=10, unique=True)
    item_description = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)
    displayed_quantity = models.IntegerField(default=0, help_text="Quantity to maintain on shelf")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.item_description}"

    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    @property
    def is_low_stock(self):
        return self.quantity <= self.displayed_quantity

class Sale(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(PharmacyUser, on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medicine.code} - {self.quantity} units"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.medicine.selling_price * self.quantity
        super().save(*args, **kwargs)

class MedicineInventory(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(PharmacyUser, on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medicine.code} - {self.quantity} units"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
        
        # Update medicine quantity
        self.medicine.quantity += self.quantity
        self.medicine.save()
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Medicine Inventory'
