from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User management
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.register_user, name='register_user'),
    path('users/edit/<int:pk>/', views.edit_user, name='edit_user'),
    path('users/deactivate/<int:pk>/', views.deactivate_user, name='deactivate_user'),
    path('users/activate/<int:pk>/', views.activate_user, name='activate_user'),
    
    # Medicine management
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/add/', views.add_medicine, name='add_medicine'),
    path('medicines/edit/<int:pk>/', views.edit_medicine, name='edit_medicine'),
    path('medicines/low-stock/', views.low_stock_medicines, name='low_stock_medicines'),
    path('medicines/expired/', views.expired_medicines, name='expired_medicines'),
    path('medicines/expiring-soon/', views.expiring_soon_medicines, name='expiring_soon_medicines'),
    
    # Sales management
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/add/', views.add_sale, name='add_sale'),
    path('sales/<int:pk>/', views.view_sale, name='view_sale'),
    path('sales/<int:pk>/edit/', views.edit_sale, name='edit_sale'),
    path('sales/<int:pk>/delete/', views.delete_sale, name='delete_sale'),
    path('sales/report/', views.sales_report, name='sales_report'),
    
    # Medicine Inventory management
    path('inventory/', views.medicine_inventory_list, name='medicine_inventory_list'),
    path('inventory/add/', views.add_medicine_inventory, name='add_medicine_inventory'),
    path('inventory/<int:pk>/', views.medicine_inventory_detail, name='medicine_inventory_detail'),
]
