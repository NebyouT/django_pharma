from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # User management
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.register_user, name='register_user'),
    
    # Medicine management
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/add/', views.add_medicine, name='add_medicine'),
    path('medicines/low-stock/', views.low_stock_medicines, name='low_stock_medicines'),
    path('medicines/expired/', views.expired_medicines, name='expired_medicines'),
    path('medicines/expiring-soon/', views.expiring_soon_medicines, name='expiring_soon_medicines'),
    
    # Medicine Inventory management
    path('inventory/', views.medicine_inventory_list, name='medicine_inventory_list'),
    path('inventory/add/', views.add_medicine_inventory, name='add_medicine_inventory'),
    path('inventory/<int:pk>/', views.medicine_inventory_detail, name='medicine_inventory_detail'),
    
    # Sales management
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/add/', views.add_sale, name='add_sale'),
    path('sales/report/', views.sales_report, name='sales_report'),
]
