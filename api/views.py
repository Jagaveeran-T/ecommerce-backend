
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token


from .serializers import RegisterSerializer
from django.contrib.auth import authenticate,get_user_model




User=get_user_model()
# Create your views here.

class RegisterView(APIView):
    def post(self,request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user=serializer.save()
            token,_=Token.objects.get_or_create(user=user)
            return Response({'Token':token.key},status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self,request):
        username=request.data.get('username')
        password=request.data.get('password')
        user=authenticate(request,username=username,password=password)
        if user:
             token,_=Token.objects.get_or_create(user=user)
             if user.is_staff:
                 role='admin'
             else:
                 role=user.role
             return Response({
                 "Token":token.key,
                 "username":user.username,
                 "role":role
                 },status=status.HTTP_200_OK)
        return Response({'Errors':'Invalid credentials'},status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        request.user.auth_token.delete()
        return Response({'message':'Logout Successfully'})
    
