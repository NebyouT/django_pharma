from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='pharmacy/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('logout', RedirectView.as_view(url='/logout/', permanent=True)),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('users/<int:pk>/deactivate/', views.deactivate_user, name='deactivate_user'),
    
    # Role Management
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:pk>/update/', views.role_update, name='role_update'),
    
    # Medicine Management
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/add/', views.add_medicine, name='add_medicine'),
    path('medicines/<int:pk>/edit/', views.edit_medicine, name='edit_medicine'),
    path('medicines/<int:pk>/delete/', views.delete_medicine, name='delete_medicine'),
    
    # Sales Management
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/add/', views.add_sale, name='add_sale'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    
    # Medicine Inventory management
    path('inventory/', views.medicine_inventory_list, name='medicine_inventory_list'),
    path('inventory/add/', views.add_medicine_inventory, name='add_medicine_inventory'),
    path('inventory/<int:pk>/', views.medicine_inventory_detail, name='medicine_inventory_detail'),
    
    # Sales management
    path('sales/<int:pk>/edit/', views.edit_sale, name='edit_sale'),
    path('sales/<int:pk>/delete/', views.delete_sale, name='delete_sale'),
    path('sales/report/', views.sales_report, name='sales_report'),
    
    # Medicine management
    path('medicines/low-stock/', views.low_stock_medicines, name='low_stock_medicines'),
    path('medicines/expired/', views.expired_medicines, name='expired_medicines'),
    path('medicines/expiring-soon/', views.expiring_soon_medicines, name='expiring_soon_medicines'),
]
