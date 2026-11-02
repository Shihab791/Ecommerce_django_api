from django.contrib.auth.models import User

from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from rest_framework.permissions import (
    AllowAny,
    IsAdminUser,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer, UserProfileSerializer, CategorySerializer,ProductSerializer
from .models import UserProfile, Category, Product


# 1. Register API
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"


# 2. Login API
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


# 3. Logout API
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "logout"

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not isinstance(refresh_token, str) or not refresh_token:
            return Response(
                {"detail": "A valid refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)

            # Ensure the token belongs to the authenticated user.
            if str(token.get("user_id")) != str(request.user.pk):
                return Response(
                    {"detail": "Invalid refresh token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token.blacklist()

        except (TokenError, KeyError, TypeError, ValueError):
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Logout successful."},
            status=status.HTTP_200_OK,
        )


# 4. Refresh Token API
class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "refresh"


# 5. Protected User Profile API
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
        })


# profile view
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get_profile(self, user):
        profile, created = UserProfile.objects.get_or_create(
            user=user
        )
        return profile

    def get(self, request):
        profile = self.get_profile(request.user)

        serializer = UserProfileSerializer(
            profile,
            context={"request": request}
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        profile = self.get_profile(request.user)

        serializer = UserProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        ) 

# Catageory
class CategoryViewSet(viewsets.ModelViewSet):

    queryset = Category.objects.all().order_by("-created_at")
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

# Product
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related(
        "category"
    ).order_by("-created_at")

    serializer_class = ProductSerializer

    # Search করার জন্য
    search_fields = [
        "name",
        "description",
        "category__name",
    ]

    # Filter করার জন্য
    filterset_fields = {
        "category": ["exact"],
        "is_active": ["exact"],
        "price": ["gte", "lte"],
        "stock": ["gte", "lte"],
    }

    # কোন কোন field দিয়ে Sorting করা যাবে
    ordering_fields = [
        "name",
        "price",
        "stock",
        "created_at",
    ]

    # Default Sorting
    ordering = ["-created_at"]

    # Permission
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

    # Rate Limiting
    def get_throttles(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            self.throttle_scope = "product_write"
            return [ScopedRateThrottle()]

        return super().get_throttles()