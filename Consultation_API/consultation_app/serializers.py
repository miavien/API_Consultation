from rest_framework import serializers
from .models import *

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class BlockUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()