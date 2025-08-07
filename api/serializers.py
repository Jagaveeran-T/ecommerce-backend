from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model


User=get_user_model()
class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)
    password2=serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields=['username','email','password','password2']
    def validate_username(self,value):
        if User.objects.filter(username__iexact=value).exists():
            raise ValidationError("Username Already Exists")
        return value
    def validate_email(self,value):
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError("Email Already Exists")
        return value
    def validate(self,data):
        if data['password'] != data['password2']:
            raise ValidationError("Password does not match")
        return data
    def create(self,validated_data):
        validated_data.pop("password2")
        validated_data['role']='customer'
        user = User.objects.create_user(**validated_data)
        return user


class VendorCreateSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)
    class Meta:
        model=User
        fields=['username','email','password','phone','company_name']
    def create(self, validated_data):
        validated_data['role']='vendor'
        return User.objects.create_user(**validated_data)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields='__all__'
    
class UserCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['id','username','email']
    
class UserVendorSerializer(serializers.ModelSerializer):
    products_count=serializers.SerializerMethodField()
    class Meta:
        model=User
        fields = ['id','username','email','products_count']
    
    def get_products_count(self,obj):
        return obj.products.count()