from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import logout, login
from django.views.decorators.http import require_http_methods
from .models import Medicine, Sale, Role, PharmacyUser
from .forms import (
    MedicineForm, SaleForm, UserRegistrationForm, CustomAuthenticationForm,
    UserUpdateForm, RoleForm
)

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

    context = {
        'user_role': request.user.role.name
    }

    # Common data for all roles
    medicines = Medicine.objects.all()
    context['total_medicines'] = medicines.count()
    
    if request.user.role.name == 'pharmacist':
        # Get today's date
        today = timezone.now().date()
        
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
        'low_stock': Medicine.objects.filter(quantity__lte=F('displayed_quantity')).count(),
        'total_sales': Sale.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'complete_medicines': complete_medicines,
        'incomplete_medicines': incomplete_medicines,
    })
    return render(request, 'pharmacy/dashboard.html', context)

@login_required
def pharmacist_dashboard(request):
    if request.user.role.name != 'pharmacist':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')

    # Get medicines with low stock (less than 10)
    low_stock = Medicine.objects.filter(quantity__lt=10).count()
    
    # Get expired medicines
    today = timezone.now().date()
    expired = Medicine.objects.filter(expiry_date__lt=today).count()
    
    # Get total medicines
    total_medicines = Medicine.objects.count()
    
    # Get recent sales
    recent_sales = Sale.objects.order_by('-date')[:5]
    
    context = {
        'user_role': 'pharmacist',
        'low_stock_count': low_stock,
        'expired_count': expired,
        'total_medicines': total_medicines,
        'recent_sales': recent_sales,
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
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")

    if request.method == 'POST':
        try:
            medicine = Medicine.objects.create(
                code=request.POST.get('code'),
                item_description=request.POST.get('item_description'),
                unit=request.POST.get('unit'),
                received_from=request.POST.get('received_from'),
                quantity=request.POST.get('quantity'),
                batch_number=request.POST.get('batch_number'),
                expiry_date=request.POST.get('expiry_date'),
                receiving_date=request.POST.get('receiving_date'),
                balance=request.POST.get('balance'),
                unit_price=request.POST.get('unit_price'),
                selling_price=request.POST.get('selling_price')
            )
            messages.success(request, 'Medicine added successfully!')
            return redirect('medicine_list')
        except Exception as e:
            messages.error(request, f'Error adding medicine: {str(e)}')
    
    return render(request, 'pharmacy/add_medicine.html')

@login_required
def edit_medicine(request, pk):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
    
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if request.method == 'POST':
        try:
            medicine.code = request.POST.get('code')
            medicine.item_description = request.POST.get('item_description')
            medicine.unit = request.POST.get('unit')
            medicine.received_from = request.POST.get('received_from')
            medicine.quantity = request.POST.get('quantity')
            medicine.batch_number = request.POST.get('batch_number')
            medicine.expiry_date = request.POST.get('expiry_date')
            medicine.receiving_date = request.POST.get('receiving_date')
            medicine.balance = request.POST.get('balance')
            medicine.unit_price = request.POST.get('unit_price')
            medicine.selling_price = request.POST.get('selling_price')
            medicine.save()
            
            messages.success(request, 'Medicine updated successfully!')
            return redirect('medicine_list')
        except Exception as e:
            messages.error(request, f'Error updating medicine: {str(e)}')
    
    return render(request, 'pharmacy/edit_medicine.html', {'medicine': medicine})

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
    if not request.user.role or request.user.role.name not in ['admin', 'cashier', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
        
    sales = Sale.objects.all().order_by('-created_at')
    return render(request, 'pharmacy/sale_list.html', {
        'sales': sales
    })

@login_required
def add_sale(request):
    if not request.user.role or request.user.role.name not in ['admin', 'cashier', 'pharmacist']:
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
    if not request.user.role or request.user.role.name not in ['admin', 'cashier', 'pharmacist']:
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
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
    
    # Consider medicines with quantity less than 10 as low stock
    low_stock = Medicine.objects.filter(quantity__lt=10).order_by('item_description')
    
    return render(request, 'pharmacy/medicine_list.html', {
        'complete_medicines': low_stock,
        'incomplete_medicines': [],
        'total_medicines': low_stock.count(),
        'empty_descriptions': 0,
        'show_only_low_stock': True
    })

@login_required
def expired_medicines(request):
    if not request.user.role or request.user.role.name not in ['admin', 'pharmacist']:
        return HttpResponseForbidden("Access Denied")
    
    today = timezone.now().date()
    expired = Medicine.objects.filter(expiry_date__lt=today).order_by('expiry_date')
    
    return render(request, 'pharmacy/medicine_list.html', {
        'complete_medicines': expired,
        'incomplete_medicines': [],
        'total_medicines': expired.count(),
        'empty_descriptions': 0,
        'show_only_expired': True
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
