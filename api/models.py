from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class User(AbstractUser):
    ROLES = (('customer','Customer'),('vendor','Vendor'),('admin','Admin'))
    role = models.CharField(max_length=10,choices=ROLES,default=ROLES[0][0])
    phone=models.CharField(max_length=10,blank=True,null=True)
    company_name=models.CharField(max_length=100,blank=True,null=True)

    def save(self, *args, **kwargs):
        # If user is a superuser, automatically set role to 'admin'
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)

