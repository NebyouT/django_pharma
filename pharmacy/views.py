from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods
from .models import Medicine, Sale, MedicineInventory, Role, PharmacyUser
from .forms import (
    MedicineForm, SaleForm, UserRegistrationForm, CustomAuthenticationForm,
    MedicineInventoryForm, UserUpdateForm, RoleForm
)

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'pharmacy/login.html', {'form': form})

@require_http_methods(["GET", "POST"])
def custom_logout(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')

@login_required
def dashboard(request):
    if not request.user.role:
        messages.warning(request, "Your account does not have a role assigned. Please contact an administrator.")
        return redirect('logout')

    total_medicines = Medicine.objects.count()
    low_stock = Medicine.objects.filter(quantity__lte=F('displayed_quantity')).count()
    total_sales = Sale.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    context = {
        'total_medicines': total_medicines,
        'low_stock': low_stock,
        'total_sales': total_sales,
    }
    return render(request, 'pharmacy/dashboard.html', context)

@login_required
def user_list(request):
    if not request.user.role or request.user.role.name != 'admin':
        return HttpResponseForbidden("Access Denied")
    
    users = PharmacyUser.objects.all().order_by('username')
    return render(request, 'pharmacy/user_list.html', {
        'users': users
    })

@login_required
def user_create(request):
    if not request.user.role or request.user.role.name != 'admin':
        return HttpResponseForbidden("Access Denied")
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.role = form.cleaned_data['role']
            try:
                user.save()
                messages.success(request, 'User created successfully!')
                return redirect('user_list')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'pharmacy/user_form.html', {
        'form': form,
        'title': 'Create User'
    })

@login_required
def user_update(request, pk):
    if not request.user.role or request.user.role.name != 'admin':
        return HttpResponseForbidden("Access Denied")
    
    user = get_object_or_404(PharmacyUser, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.role = form.cleaned_data['role']
                user.save()
                messages.success(request, 'User updated successfully!')
                return redirect('user_list')
            except Exception as e:
                messages.error(request, f'Error updating user: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserUpdateForm(instance=user)
    
    return render(request, 'pharmacy/user_form.html', {
        'form': form,
        'title': 'Update User'
    })

@login_required
def deactivate_user(request, pk):
    if not request.user.role or request.user.role.name != 'admin':
        return HttpResponseForbidden("Access Denied")
    
    user = get_object_or_404(PharmacyUser, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account!')
    else:
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} has been deactivated.')
    return redirect('user_list')

@login_required
def role_list(request):
    if not request.user.role or request.user.role.name != 'admin':
        return HttpResponseForbidden("Access Denied")
    
    roles = Role.objects.all().order_by('name')
    return render(request, 'pharmacy/role_list.html', {
        'roles': roles
    })

@login_required
def role_create(request):
    if not request.user.role or request.user.role.name != 'admin':
        return HttpResponseForbidden("Access Denied")
    
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role created successfully!')
            return redirect('role_list')
    else:
        form = RoleForm()
    
    return render(request, 'pharmacy/role_form.html', {
        'form': form,
        'title': 'Create Role'
    })

@login_required
def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User registered successfully!')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'pharmacy/user_form.html', {'form': form})

@login_required
def medicine_list(request):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist', 'inventory']:
        return HttpResponseForbidden("Access Denied")
        
    medicines = Medicine.objects.all().order_by('code')
    return render(request, 'pharmacy/medicine_list.html', {
        'medicines': medicines,
        'title': 'All Medicines'
    })

@login_required
def add_medicine(request):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
        
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save(commit=False)
            
            # Generate the next code
            last_medicine = Medicine.objects.order_by('-code').first()
            if last_medicine:
                last_num = int(last_medicine.code.split('-')[1])
                medicine.code = f'HM-{str(last_num + 1).zfill(3)}'
            else:
                medicine.code = 'HM-001'
                
            medicine.save()
            messages.success(request, 'Medicine added successfully!')
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    
    return render(request, 'pharmacy/medicine_form.html', {
        'form': form,
        'title': 'Add Medicine'
    })

@login_required
def edit_medicine(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
        
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine updated successfully!')
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    
    return render(request, 'pharmacy/medicine_form.html', {
        'form': form,
        'medicine': medicine,
        'title': 'Edit Medicine'
    })

@login_required
def delete_medicine(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
    
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        medicine.delete()
        messages.success(request, 'Medicine deleted successfully!')
        return redirect('medicine_list')
    
    return render(request, 'pharmacy/medicine_confirm_delete.html', {
        'medicine': medicine
    })

@login_required
def sale_list(request):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier']:
        return HttpResponseForbidden("Access Denied")
        
    sales = Sale.objects.all().order_by('-created_at')
    return render(request, 'pharmacy/sale_list.html', {
        'sales': sales
    })

@login_required
def add_sale(request):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier']:
        return HttpResponseForbidden("Access Denied")
        
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.created_by = request.user
            
            # Update medicine quantity
            medicine = sale.medicine
            if medicine.quantity >= sale.quantity:
                medicine.quantity -= sale.quantity
                medicine.save()
                sale.save()
                messages.success(request, 'Sale recorded successfully!')
                return redirect('sale_list')
            else:
                messages.error(request, 'Insufficient stock!')
    else:
        form = SaleForm()
    
    return render(request, 'pharmacy/sale_form.html', {
        'form': form,
        'title': 'New Sale'
    })

@login_required
def sale_detail(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier']:
        return HttpResponseForbidden("Access Denied")
    
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'pharmacy/sale_detail.html', {
        'sale': sale
    })

@login_required
def edit_sale(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier']:
        return HttpResponseForbidden("Access Denied")
    
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale updated successfully!')
            return redirect('sale_list')
    else:
        form = SaleForm(instance=sale)
    
    return render(request, 'pharmacy/sale_form.html', {
        'form': form,
        'title': 'Edit Sale'
    })

@login_required
def delete_sale(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier']:
        return HttpResponseForbidden("Access Denied")
    
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        # Restore medicine quantity
        medicine = sale.medicine
        medicine.quantity += sale.quantity
        medicine.save()
        
        sale.delete()
        messages.success(request, 'Sale deleted successfully!')
        return redirect('sale_list')
    
    return render(request, 'pharmacy/sale_confirm_delete.html', {
        'sale': sale
    })

@login_required
def sales_report(request):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier']:
        return HttpResponseForbidden("Access Denied")
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = timezone.now().replace(day=1).date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if not end_date:
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get sales for date range
    sales = Sale.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).order_by('-created_at')
    
    # Calculate totals
    total_sales = sales.aggregate(
        total_quantity=Sum('quantity'),
        total_amount=Sum('total_price')
    )
    
    context = {
        'sales': sales,
        'start_date': start_date,
        'end_date': end_date,
        'total_quantity': total_sales['total_quantity'] or 0,
        'total_amount': total_sales['total_amount'] or 0,
    }
    return render(request, 'pharmacy/sales_report.html', context)

@login_required
def low_stock_medicines(request):
    if not request.user.role or request.user.role.name not in ['admin', 'inventory']:
        return HttpResponseForbidden("Access Denied")
    
    medicines = Medicine.objects.filter(quantity__lte=F('displayed_quantity'))
    context = {'medicines': medicines, 'title': 'Low Stock Medicines'}
    return render(request, 'pharmacy/medicine_list.html', context)

@login_required
def expired_medicines(request):
    if not request.user.role or request.user.role.name not in ['admin', 'inventory']:
        return HttpResponseForbidden("Access Denied")
    
    medicines = Medicine.objects.filter(expiry_date__lt=timezone.now().date())
    context = {'medicines': medicines, 'title': 'Expired Medicines'}
    return render(request, 'pharmacy/medicine_list.html', context)

@login_required
def expiring_soon_medicines(request):
    if not request.user.role or request.user.role.name not in ['admin', 'inventory']:
        return HttpResponseForbidden("Access Denied")
    
    expiry_threshold = timezone.now().date() + timedelta(days=30)
    medicines = Medicine.objects.filter(
        expiry_date__gt=timezone.now().date(),
        expiry_date__lte=expiry_threshold
    )
    context = {'medicines': medicines, 'title': 'Medicines Expiring Soon'}
    return render(request, 'pharmacy/medicine_list.html', context)

@login_required
def medicine_inventory_list(request):
    if not request.user.role or request.user.role.name not in ['admin', 'inventory']:
        return HttpResponseForbidden("Access Denied")
    
    inventories = MedicineInventory.objects.all().order_by('-created_at')
    return render(request, 'pharmacy/medicine_inventory_list.html', {
        'inventories': inventories
    })

@login_required
def add_medicine_inventory(request):
    if not request.user.role or request.user.role.name not in ['admin', 'inventory']:
        return HttpResponseForbidden("Access Denied")
    
    if request.method == 'POST':
        form = MedicineInventoryForm(request.POST)
        if form.is_valid():
            inventory = form.save(commit=False)
            inventory.created_by = request.user
            inventory.save()
            messages.success(request, 'Inventory record added successfully!')
            return redirect('medicine_inventory_list')
    else:
        form = MedicineInventoryForm()
    
    return render(request, 'pharmacy/medicine_inventory_form.html', {
        'form': form,
        'title': 'Add Inventory Record'
    })

@login_required
def medicine_inventory_detail(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'inventory']:
        return HttpResponseForbidden("Access Denied")
    
    inventory = get_object_or_404(MedicineInventory, pk=pk)
    return render(request, 'pharmacy/medicine_inventory_detail.html', {
        'inventory': inventory
    })

@login_required
def role_update(request, pk):
    if not request.user.role or request.user.role.name != 'admin':
        return HttpResponseForbidden("Access Denied")
    
    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role updated successfully!')
            return redirect('role_list')
    else:
        form = RoleForm(instance=role)
    
    return render(request, 'pharmacy/role_form.html', {
        'form': form,
        'title': 'Update Role'
    })
