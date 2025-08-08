from rest_framework import serializers
from .models import Product,Cart,CartItem,Order,OrderItems,Notifications
from django.db.models import Sum

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields=['id','name','image','price']
        read_only_fields=['vendor']

class ProductDetailsCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields=['name','description','image','price','vendor']
        read_only_fields=['vendor']

class ProductDetailSerializer(serializers.ModelSerializer):
    total_quantity_sold=serializers.SerializerMethodField()
    total_revenue=serializers.SerializerMethodField()
    class Meta:
        model=Product
        fields=['id','name','image','description','price','vendor','total_quantity_sold','total_revenue']
        read_only_fields=['vendor','total_quantity_sold','total_revenue']
    def get_total_quantity_sold(self,obj):
        request=self.context.get('request')
        if request and (request.user == obj.vendor or request.user.is_staff):
            return OrderItems.objects.filter(product=obj).aggregate(qty=Sum('quantity')).get('qty') or 0
        return None
    def get_total_revenue(self,obj):
        request=self.context.get('request')
        if request and (request.user == obj.vendor or request.user.is_staff):
            return OrderItems.objects.filter(product=obj).aggregate(total=Sum('total')).get('total') or 0
        return None

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields='__all__'
        
class CartItemSerializer(serializers.ModelSerializer):
    product=serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True
    )
    product_name=serializers.CharField(source='product.name',read_only=True)
    class Meta:
        model=CartItem
        fields=['id','product_name','product','quantity','total']
        read_only_fields=['total','quantity']
    
class OrderItemSerializer(serializers.ModelSerializer):
    product_name=serializers.CharField(source='product.name',read_only=True)
    price=serializers.CharField(source='product.price',read_only=True)
    class Meta:
        model=OrderItems
        fields=['id','product_name','price','quantity','total']

class OrderSerializer(serializers.ModelSerializer):
    username=serializers.CharField(source='user.username',read_only=True)
    items=OrderItemSerializer(many=True,read_only=True)
    class Meta:
        model =Order
        fields=['id','username','created_at','total','items']
        read_only_fields=['username','total']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Notifications
        fields='__all__'