from django.db import models
from django.contrib.auth import get_user_model

User=get_user_model()
# Create your models here.
class Product(models.Model):
    name=models.CharField(max_length=50)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    description=models.TextField()
    image=models.ImageField(upload_to='products/',blank=True,null=True)
    vendor=models.ForeignKey(User,on_delete=models.CASCADE,related_name='products')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user =models.ForeignKey(User,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} - Cart"
    def get_total_cart_price(self):
        return sum(item.get_total_price()  for item in self.items.all() )
    
class CartItem(models.Model):
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField()
    total=models.DecimalField(max_digits=10,decimal_places=2)
    def __str__(self):
        return f"{self.quantity} - {self.product.name}"
    def get_total_price(self):
        return self.quantity * self.product.price
    def save(self,*args,**kwargs):
        self.total=self.get_total_price()
        super().save(*args,**kwargs)


class Order(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    total=models.DecimalField(max_digits=10,decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Order {self.id} - {self.user.username}"
class OrderItems(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField()
    total=models.DecimalField(max_digits=10,decimal_places=2)
    def __str__(self):
        return f"{self.quantity} - {self.product.name}"
    def get_total_price(self):
        return self.total * self.quantity
    
class Notifications(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name="notifications")
    message=models.TextField()
    is_read=models.BooleanField(default=True)
    timestamp=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} : {self.message}"

 