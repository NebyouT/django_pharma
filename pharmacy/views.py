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
    low_stock_count = Medicine.objects.filter(stock__lte=F('minimum_stock')).count()
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

@user_passes_test(is_admin)
def user_list(request):
    users = PharmacyUser.objects.all()
    return render(request, 'pharmacy/user_list.html', {'users': users})

@login_required
def add_medicine(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine added successfully!')
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'pharmacy/medicine_form.html', {'form': form})

@login_required
def medicine_list(request):
    medicines = Medicine.objects.all()
    return render(request, 'pharmacy/medicine_list.html', {'medicines': medicines})

@login_required
def low_stock_medicines(request):
    medicines = Medicine.objects.filter(stock__lte=F('minimum_stock'))
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
            medicine = form.cleaned_data['medicine']
            quantity = form.cleaned_data['quantity']
            
            if medicine.stock >= quantity:
                medicine.stock -= quantity
                medicine.save()
                sale.total_amount = medicine.price * quantity
                sale.save()
                messages.success(request, 'Sale recorded successfully!')
                return redirect('sale_list')
            else:
                messages.error(request, 'Insufficient stock!')
    else:
        form = SaleForm()
    return render(request, 'pharmacy/sale_form.html', {'form': form})

@login_required
def sale_list(request):
    sales = Sale.objects.all().order_by('-sale_date')
    return render(request, 'pharmacy/sale_list.html', {'sales': sales})

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
