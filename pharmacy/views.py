from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Role, Medicine, Sale, PharmacyUser
from django.contrib import messages
from django.db.models import F, Sum
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from .forms import (
    MedicineForm, SaleForm, UserRegistrationForm, CustomAuthenticationForm,
    UserUpdateForm, RoleForm
)
from django.db.models.functions import TruncDay
import json

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome {user.username}!")
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

    # Get today's date for expired medicines
    today = timezone.now().date()

    # Key metrics
    total_sales = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
    total_medicines = Medicine.objects.count()
    total_users = PharmacyUser.objects.count()
    
    # Get expired medicines count
    expired_count = Medicine.objects.filter(
        expiry_date__lt=today,
        code__isnull=False,
        item_description__isnull=False,
        unit__isnull=False
    ).count()
    
    # Get low stock count
    low_stock_count = Medicine.objects.filter(
        quantity__lt=F('displayed_quantity'),
        code__isnull=False,
        item_description__isnull=False,
        unit__isnull=False
    ).count()

    context = {
        'user_role': request.user.role.name,
        'total_sales': total_sales,
        'total_medicines': total_medicines,
        'total_users': total_users,
        'expired_count': expired_count,
        'low_stock_count': low_stock_count,
    }

    # Common data for all roles
    medicines = Medicine.objects.all()
    context['total_medicines'] = medicines.count()
    
    if request.user.role.name == 'pharmacist':
        # Pharmacist specific data
        if 'search' in request.GET:
            query = request.GET.get('search')
            medicines = medicines.filter(item_description__icontains=query)
        
        # Get today's sales
        today_sales = Sale.objects.filter(
            created_at__date=today
        ).order_by('-created_at')
        
        # Calculate today's total sales amount
        today_total = today_sales.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        context.update({
            'medicines': medicines,
            'displayed_medicines': medicines.filter(quantity__gt=0).count(),
            'search_query': request.GET.get('search', ''),
            'today_sales': today_sales,
            'today_total': today_total,
            'today_sales_count': today_sales.count(),
        })
        return render(request, 'pharmacy/pharmacist_dashboard.html', context)
    
    # Admin and other roles
    # Get complete medicines (using the is_complete property)
    complete_medicines = []
    incomplete_medicines = []
    
    for medicine in medicines:
        if medicine.is_complete and medicine.quantity > 0 and not medicine.is_expired:
            complete_medicines.append(medicine)
        else:
            incomplete_medicines.append(medicine)
    
    context.update({
        'low_stock': low_stock_count,
        'total_sales': Sale.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'complete_medicines': complete_medicines,
        'incomplete_medicines': incomplete_medicines,
    })
    return render(request, 'pharmacy/dashboard.html', context)

@login_required
def pharmacist_dashboard(request):
    if not request.user.role or request.user.role.name != 'pharmacist':
        return HttpResponseForbidden("Access Denied")

    # Functions available to pharmacists
    can_sell = True
    can_view_medicines = True
    can_request_drugs = True

    context = {
        'can_sell': can_sell,
        'can_view_medicines': can_view_medicines,
        'can_request_drugs': can_request_drugs,
    }
    return render(request, 'pharmacy/pharmacist_dashboard.html', context)

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
            try:
                user = form.save()
                messages.success(request, 'User created successfully!')
                return redirect('user_list')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'pharmacy/user_form.html', {
        'form': form,
        'title': 'Create New User'
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
                user = form.save()
                messages.success(request, 'User updated successfully!')
                return redirect('user_list')
            except Exception as e:
                messages.error(request, f'Error updating user: {str(e)}')
    else:
        form = UserUpdateForm(instance=user)
    
    return render(request, 'pharmacy/user_form.html', {
        'form': form,
        'title': f'Update User: {user.username}'
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
    medicines = Medicine.objects.all().order_by('item_description')
    
    # Get counts for the labels
    total_medicines = medicines.count()
    empty_descriptions = medicines.filter(Q(item_description__isnull=True) | Q(item_description='')).count()
    
    # Separate complete and incomplete medicines
    complete_medicines = []
    incomplete_medicines = []
    
    for medicine in medicines:
        if medicine.is_complete and medicine.quantity > 0 and not medicine.is_expired:
            complete_medicines.append(medicine)
        else:
            incomplete_medicines.append(medicine)
    
    context = {
        'complete_medicines': complete_medicines,
        'incomplete_medicines': incomplete_medicines,
        'total_medicines': total_medicines,
        'empty_descriptions': empty_descriptions,
    }
    
    return render(request, 'pharmacy/medicine_list.html', context)

@login_required
def add_medicine(request):
    if not request.user.role or request.user.role.name != 'admin':
        return HttpResponseForbidden("Access Denied")

    if request.method == 'POST':
        try:
            form = MedicineForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Medicine added successfully!')
                return redirect('medicine_list')
            else:
                messages.error(request, 'Please correct the errors below.')
        except Exception as e:
            messages.error(request, f'Error adding medicine: {str(e)}')
    else:
        form = MedicineForm()
    
    return render(request, 'pharmacy/medicine_form.html', {'form': form})

@login_required
def edit_medicine(request, pk):
    if not request.user.role or request.user.role.name != 'admin':
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

    return render(request, 'pharmacy/medicine_form.html', {'form': form})

@login_required
def delete_medicine(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
    
    medicine = get_object_or_404(Medicine, pk=pk)
    
    try:
        medicine.delete()
        messages.success(request, f'Medicine "{medicine.item_description}" has been deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting medicine: {str(e)}')
    
    return redirect('medicine_list')

@login_required
def delete_empty_medicines(request):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
    
    try:
        empty_medicines = Medicine.objects.filter(Q(item_description__isnull=True) | Q(item_description=''))
        count = empty_medicines.count()
        empty_medicines.delete()
        messages.success(request, f'Successfully deleted {count} medicines without descriptions.')
    except Exception as e:
        messages.error(request, f'Error deleting medicines: {str(e)}')
    
    return redirect('medicine_list')

@login_required
def sale_list(request):
    # Categorize sales
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    today_sales = Sale.objects.filter(created_at__date=today)
    yesterday_sales = Sale.objects.filter(created_at__date=yesterday)
    weekly_sales = Sale.objects.filter(created_at__date__gte=start_of_week)
    monthly_sales = Sale.objects.filter(created_at__date__gte=start_of_month)

    context = {
        'today_sales': today_sales,
        'yesterday_sales': yesterday_sales,
        'weekly_sales': weekly_sales,
        'monthly_sales': monthly_sales,
    }
    return render(request, 'pharmacy/sale_list.html', context)

@login_required
def add_sale(request):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
        
    # Get all medicines and prepare data for template
    medicines_data = []
    for medicine in Medicine.objects.all():
        medicines_data.append({
            'id': medicine.id,
            'code': medicine.code,
            'item_description': medicine.item_description,
            'unit': medicine.unit,
            'quantity': medicine.quantity,
            'selling_price': medicine.selling_price,
            'expiry_date': medicine.expiry_date,
            'is_low_stock': medicine.quantity < 10,
            'is_expired': medicine.expiry_date and medicine.expiry_date <= timezone.now().date()
        })
        
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            try:
                sale = form.save(commit=False)
                sale.created_by = request.user
                
                # Get the medicine and check stock
                medicine = sale.medicine
                if medicine.quantity >= sale.quantity:
                    # Calculate total price
                    sale.total_price = medicine.selling_price * sale.quantity
                    
                    # Set payment details
                    if sale.payment_method == 'cash':
                        sale.bank_name = 'cash'
                        sale.sender_name = 'none'
                    
                    # Update medicine quantity
                    medicine.quantity -= sale.quantity
                    medicine.save()
                    
                    # Save the sale
                    sale.save()
                    
                    messages.success(request, f'Sale recorded successfully! Total amount: {sale.total_price} ETB')
                    return redirect('sale_list')
                else:
                    messages.error(request, f'Insufficient stock! Only {medicine.quantity} units available.')
            except Exception as e:
                messages.error(request, f'Error recording sale: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SaleForm()
    
    return render(request, 'pharmacy/sale_form.html', {
        'form': form,
        'title': 'New Sale',
        'medicines': medicines_data
    })

@login_required
def sale_detail(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
    
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'pharmacy/sale_detail.html', {
        'sale': sale
    })

@login_required
def edit_sale(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier', 'pharmacist']:
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
    if not request.user.role or request.user.role.name not in ['admin', 'cashier', 'pharmacist']:
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
    # Group sales by day and payment method
    sales_by_day = Sale.objects.all().order_by('-created_at')
    
    # Prepare data for display
    sales_data = {}
    for sale in sales_by_day:
        day = sale.created_at.date()
        if day not in sales_data:
            sales_data[day] = {'cash': [], 'transfer': []}
        
        if sale.payment_method == 'cash':
            sales_data[day]['cash'].append(sale)
        else:
            sales_data[day]['transfer'].append(sale)
    
    print('Sales Data:', sales_data)  # Debug statement
    return render(request, 'pharmacy/sales_report.html', {
        'sales_data': sales_data
    })

@login_required
def low_stock_medicines(request):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")

    # Get medicines with low stock (less than 10) and complete data
    low_stock_medicines = Medicine.objects.filter(
        quantity__lt=10,
        # Ensure all required fields are present and not null
        code__isnull=False,
        item_description__isnull=False,
        category__isnull=False,
        unit__isnull=False,
        quantity__isnull=False,
        expiry_date__isnull=False,
        batch_number__isnull=False,
        displayed_quantity__isnull=False,
        unit_price__isnull=False,
        selling_price__isnull=False
    ).exclude(  # Exclude empty strings and zero values
        code='',
        item_description='',
        category='',
        unit='',
        batch_number='',
        unit_price=0,
        selling_price=0
    ).order_by('quantity')

    return render(request, 'pharmacy/low_stock_medicines.html', {
        'medicines': low_stock_medicines,
        'title': 'Low Stock Medicines'
    })

@login_required
def expired_medicines(request):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")

    # Get expired medicines with complete data
    today = timezone.now().date()
    expired_medicines = Medicine.objects.filter(
        expiry_date__lte=today,
        # Ensure all required fields are present
        code__isnull=False,
        item_description__isnull=False,
        category__isnull=False,
        unit__isnull=False,
        quantity__isnull=False,
        expiry_date__isnull=False,
        batch_number__isnull=False
    ).exclude(  # Exclude empty strings
        code='',
        item_description='',
        category='',
        unit='',
        batch_number=''
    ).order_by('expiry_date')

    return render(request, 'pharmacy/expired_medicines.html', {
        'medicines': expired_medicines,
        'title': 'Expired Medicines'
    })

@login_required
def search_medicine(request):
    query = request.GET.get('q', '')
    medicines = []
    
    if query:
        medicines = Medicine.objects.filter(
            Q(code__icontains=query) |
            Q(item_description__icontains=query)
        ).order_by('item_description')
    
    return JsonResponse({
        'medicines': [{
            'id': m.id,
            'code': m.code,
            'item_description': m.item_description,
            'quantity': m.quantity,
            'unit_price': float(m.unit_price),
            'selling_price': float(m.selling_price)
        } for m in medicines]
    })

@login_required
def search_medicines(request):
    query = request.GET.get('q', '').strip()
    
    try:
        medicines = Medicine.objects.filter(
            Q(code__icontains=query) | 
            Q(item_description__icontains=query)
        ).values(
            'id', 'code', 'item_description', 'quantity',
            'unit_price', 'selling_price', 'expiry_date',
            'balance', 'unit', 'displayed_quantity'
        ).order_by('code')[:10]  # Limit to 10 rows
        
        # Format dates and add computed fields
        medicine_list = list(medicines)
        current_date = timezone.now().date()
        
        for med in medicine_list:
            med['expiry_date'] = med['expiry_date'].strftime('%Y-%m-%d')
            # Add is_low_stock flag
            med['is_low_stock'] = med['quantity'] <= med['displayed_quantity']
            # Add is_expired flag
            med['is_expired'] = datetime.strptime(med['expiry_date'], '%Y-%m-%d').date() <= current_date
            
        return JsonResponse(medicine_list, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def record_sale(request):
    try:
        medicine_id = request.POST.get('medicine_id')
        quantity = int(request.POST.get('quantity', 0))
        payment_method = request.POST.get('payment_method', 'cash')
        
        medicine = Medicine.objects.get(id=medicine_id)
        
        if medicine.balance < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Insufficient stock. Available: {medicine.balance}'
            }, status=400)
        
        sale = Sale.objects.create(
            medicine=medicine,
            quantity=quantity,
            payment_method=payment_method,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Sale recorded successfully',
            'sale_id': sale.id,
            'total_price': float(sale.total_price)
        })
        
    except Medicine.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Medicine not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

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

@login_required
def search_and_sell_medicine(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            medicine = form.cleaned_data['medicine']
            quantity = form.cleaned_data['quantity']
            payment_method = form.cleaned_data['payment_method']
            cash_amount = form.cleaned_data['cash_amount']
            bank_name = form.cleaned_data['bank_name']
            sender_name = form.cleaned_data['sender_name']

            # Reduce the medicine quantity
            medicine.quantity = F('quantity') - quantity
            medicine.save()

            # Create a new sale record
            sale = Sale(
                medicine=medicine,
                quantity=quantity,
                payment_method=payment_method,
                cash_amount=cash_amount if payment_method == 'cash' else None,
                bank_name=bank_name if payment_method == 'bank' else None,
                sender_name=sender_name if payment_method == 'bank' else None,
            )
            sale.save()

            messages.success(request, "Sale recorded successfully.")
            return redirect('sale_list')
    else:
        form = SaleForm()

    return render(request, 'pharmacy/search_and_sell.html', {'form': form})

@login_required
def expired_medicines(request):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")

    # Get expired medicines
    today = timezone.now().date()
    expired_medicines = Medicine.objects.filter(expiry_date__lte=today).order_by('expiry_date')

    return render(request, 'pharmacy/expired_medicines.html', {
        'medicines': expired_medicines,
        'title': 'Expired Medicines'
    })

@login_required
def low_stock_medicines(request):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")

    # Get medicines with low stock (less than 10 units)
    low_stock_medicines = Medicine.objects.filter(quantity__lt=10).order_by('quantity')

    return render(request, 'pharmacy/low_stock_medicines.html', {
        'medicines': low_stock_medicines,
        'title': 'Low Stock Medicines'
    })
