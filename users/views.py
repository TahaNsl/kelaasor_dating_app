import requests
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from users.models import Profile
from users.serializers import (RegisterSerializer, UserSerializer,
                               MyTokenObtainPairSerializer, ProfileSerializer)



User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()


        refresh = RefreshToken.for_user(user)
        data = {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return Response(data, status=status.HTTP_201_CREATED)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class AllUsersView(generics.ListAPIView):
    """Endpoint: GET /api/users/all/"""
    queryset = Profile.objects.select_related("user", "location").all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


class NearbyUsersView(APIView):
    """Endpoint: GET /api/users/nearby/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_profile = request.user.profile

        if not user_profile.location:
            return Response({"detail": "Your location is not set."}, status=400)

        user_lat = user_profile.location.latitude
        user_lng = user_profile.location.longitude

        nearby_profiles = []
        for profile in Profile.objects.exclude(user=request.user).select_related("location"):
            if not profile.location:
                continue

            url = "https://api.neshan.org/v1/distance-matrix"
            headers = {"Api-Key": "<YOUR_NESHAN_API_KEY>"}
            data = {
                "origins": f"{user_lat},{user_lng}",
                "destinations": f"{profile.location.latitude},{profile.location.longitude}",
            }

            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 200:
                continue

            result = response.json()
            try:
                distance = result["rows"][0]["elements"][0]["distance"]["value"]  # متر
                if distance <= 15000:
                    nearby_profiles.append(profile)
            except (KeyError, IndexError):
                continue

        serializer = ProfileSerializer(nearby_profiles, many=True)
        return Response(serializer.data)