from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter
from sales.views import SalesStats

router=DefaultRouter()
router.register("add-to-cart",views.CartItemView,basename='add-cart')
router.register("buy-now",views.OrderView,basename='buy-now')
router.register("vendor-orders",views.VendorOrderItems,basename='vendor-orders')

urlpatterns = [
    # products
    path("product/",views.ProductsList.as_view(),name='product-list'),
    path("product/details/<int:pk>/",views.ProductDetailsView.as_view()),
    path("vendor/dashboard/",views.VendorDashboard.as_view()),
    path("vendor/product/add/",views.AddProducts.as_view(),name='product-add'),
    path('vendor/products/<int:pk>/',views.ProductUpdate.as_view(),name='product-update'),
    path("vendor/products/",views.VendorProducts.as_view()),
    
   
    #Admin access
    path('admin/',views.AdminDashboard.as_view()),
    path('admin/orders/',views.OrderListView.as_view()),
    path('admin/customers/',views.CustomerListView.as_view()),
    path('admin/vendors/',views.VendorListView.as_view()),
    path("admin/vendors/<int:pk>/",views.AdminVendorProducts.as_view(),name='vendor-products'),

    path("admin/sales-stats/",SalesStats.as_view(),name='sales-stats'),
    path("admin/add/vendor/",views.AddVendorView.as_view()),
    
    path("notifications/",views.NotificationListView.as_view()),
    
    path("",include(router.urls))
    
]
