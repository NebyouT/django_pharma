from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Category, Medicine, Sale, PharmacyUser, MedicineInventory
from .forms import MedicineForm, SaleForm, UserRegistrationForm, CustomAuthenticationForm, MedicineInventoryForm
from django.db.models import F

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

@login_required
def dashboard(request):
    # Get counts and summaries
    total_medicines = Medicine.objects.count()
    low_stock_count = Medicine.objects.filter(balance__lte=10).count()  # Using balance instead of stock
    expired_count = Medicine.objects.filter(expiry_date__lte=timezone.now().date()).count()
    expiring_soon = Medicine.objects.filter(
        expiry_date__gt=timezone.now().date(),
        expiry_date__lte=timezone.now().date() + timedelta(days=30)
    ).count()

    # Get sales statistics
    today = timezone.now().date()
    daily_sales = Sale.objects.filter(sale_date__date=today).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    # Weekly sales
    week_ago = today - timedelta(days=7)
    weekly_sales = Sale.objects.filter(sale_date__date__gte=week_ago).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )

    # Monthly sales
    month_ago = today - timedelta(days=30)
    monthly_sales = Sale.objects.filter(sale_date__date__gte=month_ago).aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )

    context = {
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
        'expired_count': expired_count,
        'expiring_soon': expiring_soon,
        'daily_sales': daily_sales,
        'weekly_sales': weekly_sales,
        'monthly_sales': monthly_sales,
    }
    return render(request, 'pharmacy/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
def user_list(request):
    users = PharmacyUser.objects.all()
    return render(request, 'pharmacy/user_list.html', {'users': users})

@login_required
def add_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save(commit=False)
            if not medicine.code:
                medicine.code = generate_medicine_code()
            medicine.save()
            messages.success(request, 'Medicine added successfully!')
            return redirect('medicine_list')
    else:
        initial_code = generate_medicine_code()
        form = MedicineForm(initial={'code': initial_code})
    return render(request, 'pharmacy/medicine_form.html', {'form': form, 'title': 'Add Medicine'})

@login_required
def edit_medicine(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine updated successfully!')
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'pharmacy/medicine_form.html', {'form': form, 'title': 'Edit Medicine'})

@login_required
def medicine_list(request):
    medicines = Medicine.objects.all()
    search_query = request.GET.get('search', '')
    search_field = request.GET.get('search_field', 'code')

    if search_query:
        if search_field == 'code':
            medicines = medicines.filter(code__icontains=search_query)
        elif search_field == 'item_description':
            medicines = medicines.filter(item_description__icontains=search_query)
        elif search_field == 'batch_number':
            medicines = medicines.filter(batch_number__icontains=search_query)
        elif search_field == 'received_from':
            medicines = medicines.filter(received_from__icontains=search_query)

    medicines = medicines.order_by('-created_at')
    
    search_fields = [
        ('code', 'Code'),
        ('item_description', 'Item Description'),
        ('batch_number', 'Batch Number'),
        ('received_from', 'Received From'),
    ]

    context = {
        'medicines': medicines,
        'search_query': search_query,
        'search_field': search_field,
        'search_fields': search_fields,
    }
    return render(request, 'pharmacy/medicine_list.html', context)

def generate_medicine_code():
    prefix = "HM-"
    last_medicine = Medicine.objects.all().order_by('-code').first()
    if last_medicine and last_medicine.code.startswith(prefix):
        try:
            last_number = int(last_medicine.code[len(prefix):])
            new_number = last_number + 1
        except ValueError:
            new_number = 1
    else:
        new_number = 1
    return f"{prefix}{new_number:03d}"

@login_required
def low_stock_medicines(request):
    medicines = Medicine.objects.filter(balance__lte=10).order_by('balance')
    return render(request, 'pharmacy/medicine_list.html', {
        'medicines': medicines,
        'title': 'Low Stock Medicines'
    })

@login_required
def expired_medicines(request):
    medicines = Medicine.objects.filter(expiry_date__lte=timezone.now().date())
    return render(request, 'pharmacy/medicine_list.html', {
        'medicines': medicines,
        'title': 'Expired Medicines'
    })

@login_required
def expiring_soon_medicines(request):
    today = timezone.now().date()
    thirty_days_from_now = today + timedelta(days=30)
    medicines = Medicine.objects.filter(
        expiry_date__gt=today,
        expiry_date__lte=thirty_days_from_now
    )
    return render(request, 'pharmacy/medicine_list.html', {
        'medicines': medicines,
        'title': 'Medicines Expiring Soon'
    })

@login_required
def add_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.seller = request.user
            
            # Calculate total amount
            medicine = form.cleaned_data['medicine']
            quantity = form.cleaned_data['quantity']
            sale.total_amount = medicine.selling_price * quantity
            
            # Update medicine balance
            if medicine.balance >= quantity:
                medicine.balance -= quantity
                medicine.save()
                sale.save()
                messages.success(request, 'Sale recorded successfully!')
                return redirect('sale_list')
            else:
                messages.error(request, 'Insufficient stock!')
    else:
        form = SaleForm()
    return render(request, 'pharmacy/sale_form.html', {'form': form, 'title': 'New Sale'})

@login_required
def sale_list(request):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Get sales for different time periods
    today_sales = Sale.objects.filter(sale_date__date=today).order_by('-sale_date')
    yesterday_sales = Sale.objects.filter(sale_date__date=yesterday).order_by('-sale_date')
    weekly_sales = Sale.objects.filter(sale_date__date__gte=week_start).order_by('-sale_date')
    monthly_sales = Sale.objects.filter(sale_date__date__gte=month_start).order_by('-sale_date')

    # Calculate totals
    def calculate_total(queryset):
        return {
            'count': queryset.count(),
            'total_amount': sum(sale.total_amount for sale in queryset),
            'total_quantity': sum(sale.quantity for sale in queryset)
        }

    # Create periods list for template
    periods = [
        ('today', today_sales, calculate_total(today_sales)),
        ('yesterday', yesterday_sales, calculate_total(yesterday_sales)),
        ('weekly', weekly_sales, calculate_total(weekly_sales)),
        ('monthly', monthly_sales, calculate_total(monthly_sales))
    ]

    context = {
        'periods': periods,
        'today_total': calculate_total(today_sales),
        'yesterday_total': calculate_total(yesterday_sales),
        'weekly_total': calculate_total(weekly_sales),
        'monthly_total': calculate_total(monthly_sales)
    }
    
    return render(request, 'pharmacy/sale_list.html', context)

@login_required
@user_passes_test(is_admin)
def sales_report(request):
    # Get date range from request or default to last 30 days
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date')
    end_date_param = request.GET.get('end_date')
    
    if start_date and end_date_param:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
    else:
        start_date = end_date - timedelta(days=30)
    
    sales = Sale.objects.filter(
        sale_date__date__gte=start_date,
        sale_date__date__lte=end_date
    ).order_by('-sale_date')
    
    total_sales = sales.aggregate(
        total_amount=Sum('total_amount'),
        total_quantity=Sum('quantity')
    )
    
    context = {
        'sales': sales,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
    }
    return render(request, 'pharmacy/sales_report.html', context)

@login_required
def view_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'pharmacy/sale_detail.html', {'sale': sale})

@login_required
@user_passes_test(is_admin)
def edit_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale updated successfully!')
            return redirect('sale_list')
    else:
        form = SaleForm(instance=sale)
    return render(request, 'pharmacy/sale_form.html', {'form': form, 'title': 'Edit Sale'})

@login_required
@user_passes_test(is_admin)
def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    sale.delete()
    messages.success(request, 'Sale deleted successfully!')
    return redirect('sale_list')

@login_required
def add_medicine_inventory(request):
    if request.method == 'POST':
        form = MedicineInventoryForm(request.POST)
        if form.is_valid():
            inventory = form.save(commit=False)
            if not inventory.balance:
                inventory.balance = inventory.quantity  # Set initial balance to quantity if not provided
            inventory.save()
            messages.success(request, 'Medicine inventory added successfully!')
            return redirect('medicine_inventory_list')
    else:
        form = MedicineInventoryForm()
    return render(request, 'pharmacy/medicine_inventory_form.html', {'form': form, 'title': 'Add Medicine Inventory'})

@login_required
def medicine_inventory_list(request):
    inventories = MedicineInventory.objects.all().order_by('-receiving_date')
    return render(request, 'pharmacy/medicine_inventory_list.html', {'inventories': inventories})

@login_required
def medicine_inventory_detail(request, pk):
    inventory = get_object_or_404(MedicineInventory, pk=pk)
    return render(request, 'pharmacy/medicine_inventory_detail.html', {'inventory': inventory})

@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = PharmacyUser.objects.all().order_by('username')
    return render(request, 'pharmacy/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'User registered successfully!')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'pharmacy/user_form.html', {'form': form, 'title': 'Add New User'})

@login_required
@user_passes_test(is_admin)
def edit_user(request, pk):
    user = get_object_or_404(PharmacyUser, pk=pk)
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully!')
            return redirect('user_list')
    else:
        form = UserRegistrationForm(instance=user)
    return render(request, 'pharmacy/user_form.html', {'form': form, 'title': 'Edit User'})

@login_required
@user_passes_test(is_admin)
def deactivate_user(request, pk):
    user = get_object_or_404(PharmacyUser, pk=pk)
    if user != request.user:  # Prevent self-deactivation
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} has been deactivated.')
    else:
        messages.error(request, 'You cannot deactivate your own account.')
    return redirect('user_list')

@login_required
@user_passes_test(is_admin)
def activate_user(request, pk):
    user = get_object_or_404(PharmacyUser, pk=pk)
    user.is_active = True
    user.save()
    messages.success(request, f'User {user.username} has been activated.')
    return redirect('user_list')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')
