from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from locations.models import Location
from users.models import Profile



User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "password", "password2")

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        # create_user will hash the password
        user = User.objects.create_user(**validated_data, password=password)

        Profile.objects.create(user=user)
        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Customize JWT login response to include user info"""
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["latitude", "longitude", "city", "country"]

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    location = LocationSerializer()

    class Meta:
        model = Profile
        fields = ["user", "bio", "gender", "age", "avatar", "location"]