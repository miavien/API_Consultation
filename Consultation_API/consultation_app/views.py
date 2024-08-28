from django.shortcuts import render
from rest_framework import generics
from .models import *
from .serializers import *
# Create your views here.
class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'