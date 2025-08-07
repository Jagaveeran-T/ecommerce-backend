from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework.exceptions import ValidationError

from django.utils import timezone
from datetime import timedelta
from calendar import monthrange

from django.db.models import Sum
from django.db.models.functions import TruncDay

from myapp.models import OrderItems,Product

class SalesStats(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        user=request.user
        today=timezone.now().date()
        type=request.query_params.get('type','week')
        product_id=request.query_params.get('product_id')
        if type == 'month':
            start_date=today.replace(day=1)
            end_date=today.replace(day=monthrange(today.year,today.month)[1])
            label_format="%d-%b"
            total_days=(end_date-start_date).days + 1
        else:
            start_date=today - timedelta(days=today.weekday())
            end_date=start_date + timedelta(days=6)
            label_format="%a"
            total_days=7
        
        if user.is_staff:
            order_items= OrderItems.objects.filter(order__created_at__date__range=(start_date,end_date))
        elif user.role == 'vendor':
            order_items = OrderItems.objects.filter(product__vendor=user,order__created_at__date__range=(start_date,end_date))
        else:
            return Response({"details":"Unauthorized Access"},status=403)
        
        if product_id:
            try:
                product=Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                raise ValidationError("Product Not Found")
            if user.role== 'vendor' and product.vendor != user:
                raise ValidationError("You cannot acess this product")
            order_items=order_items.filter(product=product)
        
        grouped_data = (
            order_items.annotate(day=TruncDay('order__created_at')).values('day').annotate(quantity=Sum('quantity'),total=Sum('total'))
        )
        result=[]
        for i in range(total_days):
            current_day=start_date + timedelta(days=i)
            stat=next((x for x in grouped_data if x['day'].date() == current_day),None)
            result.append({
                "date":current_day.strftime(label_format),
                "quantity":stat['quantity'] if stat else 0,
                "Earnings":float(stat['total']) if stat else 0.0

            })
        return Response(result)
