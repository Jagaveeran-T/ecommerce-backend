from django.shortcuts import get_object_or_404
# from api.models import User
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework import generics,viewsets
from rest_framework.permissions import IsAuthenticated,IsAdminUser,AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied,ValidationError

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from django.db.models import Sum

from api.serializers import UserSerializer,UserCustomerSerializer,UserVendorSerializer,VendorCreateSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Product,Cart,CartItem,Order,OrderItems,Notifications
from .serializers import ProductSerializer,CartItemSerializer,OrderSerializer,OrderItemSerializer,NotificationSerializer,ProductDetailSerializer,ProductDetailsCustomerSerializer

from .permissions import IsVendorOrReadOnly,IsCustomer,IsVendor

# Create your views here.

User=get_user_model()

class ProductsList(generics.ListAPIView):
    queryset=Product.objects.all().order_by('-created_at')
    serializer_class=ProductSerializer
    permission_classes=[AllowAny]
    filter_backends=[DjangoFilterBackend,SearchFilter]
    # filterset_fields=['name']
    search_fields=['name']

class ProductDetailsView(generics.RetrieveAPIView):
    queryset=Product.objects.all()
    serializer_class=ProductDetailsCustomerSerializer
    permission_classes=[AllowAny]

class VendorProducts(generics.ListAPIView):
    serializer_class=ProductSerializer
    permission_classes=[IsVendor]

    def get_queryset(self):
        user=self.request.user
        return Product.objects.filter(vendor=user)

class AdminVendorProducts(generics.ListAPIView):
    serializer_class=ProductSerializer
    permission_classes=[IsAdminUser]
    def get_queryset(self):
        pk=self.kwargs['pk']
        vendor=get_object_or_404(User,pk=pk,role='vendor')
        return Product.objects.filter(vendor=vendor)

class AddVendorView(generics.CreateAPIView):
    serializer_class=VendorCreateSerializer
    permission_classes=[IsAdminUser]

class AddProducts(generics.CreateAPIView):
    queryset=Product.objects.all()
    serializer_class=ProductSerializer
    permission_classes=[IsVendorOrReadOnly]

    def perform_create(self, serializer):
        user=self.request.user
        product=serializer.save(vendor=user)

        channel_layer=get_channel_layer()
        admin_group_name="admin_notifications"
        message=f"New Product {product.name} added by {user.username}"

        async_to_sync(channel_layer.group_send(
            admin_group_name,{
                "type":"send_notification",
                "message":message
            }
        ))
        admin_user=User.objects.filter(is_staff=True).first()
        if admin_user:
            Notifications.objects.create(user=admin_user,message=message)


class ProductUpdate(generics.RetrieveUpdateDestroyAPIView):
    queryset=Product.objects.all()
    serializer_class=ProductDetailSerializer
    lookup_field='pk'
    permission_classes=[IsVendorOrReadOnly]

class CartItemView(viewsets.ModelViewSet):
    serializer_class=CartItemSerializer
    permission_classes=[IsCustomer]
    def get_queryset(self):
        cart,_=Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)
    def perform_create(self, serializer):
        cart,_=Cart.objects.get_or_create(user=self.request.user)
        product=serializer.validated_data['product']
        quantity=serializer.validated_data.get('quantity',1)
        cart_item,created=CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity':quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            pass
    def perform_destroy(self, instance):
        if instance.cart.user==self.request.user:
            instance.delete()
        else:
            raise PermissionDenied("Unauthorized")
    def list(self,request,*args,**kwargs):
        cart,_=Cart.objects.get_or_create(user=request.user)
        queryset=self.get_queryset()
        serializer=self.get_serializer(queryset,many=True)
        total=cart.get_total_cart_price()
        return Response({
            'items':serializer.data,
             'total':total
        })

        
        
class OrderView(viewsets.ModelViewSet):
    serializer_class=OrderSerializer
    permission_classes=[IsCustomer]
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        user=self.request.user
        cart=Cart.objects.get(user=user)
        cart_items=cart.items.all()

        if not cart_items.exists():
            raise ValidationError("Cart is Empty")
        total=sum([item.total for item in cart_items])
        order=serializer.save(user=user,total=total)
        

        for item in cart_items:
            OrderItems.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                total=item.total )
            
            vendor=item.product.vendor
            
            group_name = f"vendor_{vendor.id}"
            channel_layer=get_channel_layer()
            vendor_message=f"New Order for your product{item.product.name}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type":"send_notification",
                    "message":vendor_message
                }
                )
            Notifications.objects.create(user=vendor,message=vendor_message)
    

        admin_group_name="admin_notifications"
        admin_message=f"New order placed by {user.username} Total:{total}"
        async_to_sync(channel_layer.group_send)(
            admin_group_name,
                {
                    "type":"send_notification",
                    "message":admin_message
                }
            )
        admin_user=User.objects.filter(is_staff=True).first()
        if admin_user:
            Notifications.objects.create(user=admin_user,message=admin_message)
            

        cart_items.delete()

class VendorDashboard(APIView):
    permission_classes=[IsAuthenticated,IsVendor]

    def get(self,request):
       vendor=request.user
       total_product=Product.objects.filter(vendor=vendor).count()

       vendor_items=OrderItems.objects.filter(product__vendor=vendor)

       total_orders=vendor_items.values('order').distinct().count()

       total_items_sold=vendor_items.aggregate(total_qty=Sum('quantity')).get('total_qty',0) or 0

       total_amount=vendor_items.aggregate(Total=Sum('total')).get('Total',0) or 0

       return Response({
           "Summary":{
               "Total Product":total_product,
               "Total Orders" : total_orders,
               "Total Ordered Items" : total_items_sold,
               "Total Revenue" : total_amount
           }
       })
    

class VendorOrderItems(viewsets.ReadOnlyModelViewSet):
    serializer_class=OrderItemSerializer
    permission_classes=[IsAuthenticated,IsVendor]
    def get_queryset(self):
        return OrderItems.objects.filter(product__vendor=self.request.user)

class AdminDashboard(APIView):
    permission_classes=[IsAdminUser]

    def get(self,request):
        total_customers=User.objects.filter(role='customer').count()
        total_vendors=User.objects.filter(role='vendor').count()
        total_orders=Order.objects.count()
        total_amount=Order.objects.aggregate(total=Sum('total')).get('total',0) or 0

        return Response({
            "summary":{
                "Total_Customers":total_customers,
                "Total_Vendors":total_vendors,
                "Total_Orders":total_orders,
                "Total_Amount":total_amount
            }
        })

        

class CustomerListView(generics.ListAPIView):
    queryset=User.objects.filter(role='customer')
    serializer_class=UserCustomerSerializer
    permission_classes=[IsAdminUser]

class VendorListView(generics.ListAPIView):
    queryset=User.objects.filter(role='vendor')
    serializer_class=UserVendorSerializer
    permission_classes=[IsAdminUser]

class OrderListView(generics.ListAPIView):
    
    serializer_class=OrderSerializer
    permission_classes=[IsAdminUser]

    def get_queryset(self):
        queryset=Order.objects.all()
        from_date=self.request.query_params.get('from_date')
        to_date=self.request.query_params.get('to_date')
        if from_date and to_date:
            queryset=queryset.filter(created_at__date__gte=from_date,created_at__date__lte=to_date)
        return queryset
    def list(self, request, *args, **kwargs):
        queryset=self.get_queryset()
        serializer=self.get_serializer(queryset,many=True)
        total=Order.objects.aggregate(total=Sum('total')).get('total',0) or 0
        return Response({"orders":serializer.data,"Total":total})


class NotificationListView(generics.ListAPIView):
    serializer_class=NotificationSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        return Notifications.objects.filter(user=self.request.user).order_by('-timestamp')
    
