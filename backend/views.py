from django.contrib.auth.models import User
from django.db import transaction

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

from rest_framework.generics import (
    ListCreateAPIView,
    DestroyAPIView,
)

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import ValidationError

from .serializers import RegisterSerializer, UserProfileSerializer, CategorySerializer,ProductSerializer, WishlistAddSerializer, WishlistItemSerializer, CartAddSerializer, CartItemSerializer, CartUpdateSerializer, AddressSerializer
from .models import UserProfile, Category, Product, WishlistItem, CartItem, Address


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

class WishlistListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "wishlist_write"

    def get_queryset(self):
        return (
            WishlistItem.objects
            .filter(user=self.request.user)
            .select_related("product")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WishlistAddSerializer
        return WishlistItemSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class WishlistDeleteView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "wishlist_write"

    def get_queryset(self):
        return WishlistItem.objects.filter(
            user=self.request.user
        )

    def delete(self, request, *args, **kwargs):
        try:
            item = self.get_queryset().get(pk=kwargs["pk"])
        except WishlistItem.DoesNotExist:
            return Response(
                {"detail": "Wishlist item not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()

        return Response(
            {"detail": "Product removed from wishlist."},
            status=status.HTTP_200_OK
        )   

class CartListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cart_write"

    def get(self, request):
        cart_items = (
            CartItem.objects
            .filter(user=request.user)
            .select_related("product")
            .order_by("-created_at")
        )

        serializer = CartItemSerializer(cart_items, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]

        try:
            product = Product.objects.get(
                id=product_id,
                is_active=True
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found or unavailable."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Stock check
        if quantity > product.stock:
            return Response(
                {"detail": "Requested quantity is not available in stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={"quantity": quantity}
        )

        # যদি আগে থেকেই Cart-এ থাকে
        if not created:
            new_quantity = cart_item.quantity + quantity

            if new_quantity > product.stock:
                return Response(
                    {"detail": "Requested quantity exceeds available stock."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity = new_quantity
            cart_item.save()

        return Response(
            CartItemSerializer(cart_item).data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            )
        )     

class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cart_write"

    def get_object(self, request, pk):
        try:
            return CartItem.objects.select_related(
                "product"
            ).get(
                pk=pk,
                user=request.user
            )
        except CartItem.DoesNotExist:
            return None

    def patch(self, request, pk):
        cart_item = self.get_object(request, pk)

        if not cart_item:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CartUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data["quantity"]

        # Stock check
        if quantity > cart_item.product.stock:
            return Response(
                {"detail": "Requested quantity exceeds available stock."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        return Response(
            CartItemSerializer(cart_item).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):
        cart_item = self.get_object(request, pk)

        if not cart_item:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_item.delete()

        return Response(
            {"detail": "Product removed from cart."},
            status=status.HTTP_200_OK
        )    

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "address_write"

    def get_queryset(self):
        return (
            Address.objects
            .filter(user=self.request.user)
            .order_by("-is_default", "-created_at")
        )

    def perform_create(self, serializer):
        with transaction.atomic():

            is_default = serializer.validated_data.get(
                "is_default",
                False
            )

            # যদি এটি User-এর প্রথম Address হয়,
            # তাহলে Automatically Default হবে
            if not Address.objects.filter(
                user=self.request.user
            ).exists():
                is_default = True

            # নতুন Default Address দিলে
            # আগের Default Address বন্ধ হবে
            if is_default:
                Address.objects.filter(
                    user=self.request.user,
                    is_default=True
                ).update(is_default=False)

            serializer.save(
                user=self.request.user,
                is_default=is_default
            )

    def perform_update(self, serializer):
        with transaction.atomic():

            is_default = serializer.validated_data.get(
                "is_default",
                serializer.instance.is_default
            )

            # নতুন Default Address হলে
            # অন্যগুলো Default থাকবে না
            if is_default:
                Address.objects.filter(
                    user=self.request.user,
                    is_default=True
                ).exclude(
                    pk=serializer.instance.pk
                ).update(is_default=False)

            serializer.save(is_default=is_default)    