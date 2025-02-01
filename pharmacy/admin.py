from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
import csv
from django.http import HttpResponse
from datetime import datetime
from .models import Medicine, Role, PharmacyUser, Sale

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('code', 'item_description', 'quantity', 'unit_price', 'selling_price', 'expiry_date', 'is_low_stock', 'is_expired')
    list_filter = ('unit', 'expiry_date')
    search_fields = ('code', 'item_description')
    ordering = ('code',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(PharmacyUser)
class PharmacyUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'quantity', 'total_price', 'payment_method', 'created_by', 'created_at')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('medicine__code', 'medicine__item_description')
    date_hierarchy = 'created_at'
