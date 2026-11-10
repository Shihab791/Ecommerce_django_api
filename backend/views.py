from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db import transaction
from decimal import Decimal

from rest_framework import generics, status, viewsets, serializers
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

from .serializers import RegisterSerializer, UserProfileSerializer, CategorySerializer,ProductSerializer, WishlistAddSerializer, WishlistItemSerializer, CartAddSerializer, CartItemSerializer, CartUpdateSerializer, AddressSerializer, OrderSerializer, OrderCreateSerializer, PaymentCreateSerializer, PaymentSerializer, ReviewSerializer
from .models import UserProfile, Category, Product, WishlistItem, CartItem, Address, Order, OrderItem, Payment, Review

User = get_user_model()

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

class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "order_create"

    @transaction.atomic
    def post(self, request):

        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        address_id = serializer.validated_data["address_id"]

        # শুধু নিজের Address ব্যবহার করতে পারবে
        try:
            address = Address.objects.get(
                id=address_id,
                user=request.user
            )
        except Address.DoesNotExist:
            return Response(
                {"detail": "Delivery address not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cart Items নেওয়া
        cart_items = (
            CartItem.objects
            .select_related("product")
            .filter(user=request.user)
        )

        if not cart_items.exists():
            return Response(
                {"detail": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_amount = Decimal("0.00")

        # Order তৈরি
        order = Order.objects.create(
            user=request.user,
            address=address,
            total_amount=Decimal("0.00")
        )

        for cart_item in cart_items:

            product = cart_item.product

            # Product active কিনা
            if not product.is_active:
                return Response(
                    {
                        "detail": (
                            f"{product.name} is currently unavailable."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Stock check
            if cart_item.quantity > product.stock:
                return Response(
                    {
                        "detail": (
                            f"Insufficient stock for {product.name}."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            subtotal = product.price * cart_item.quantity

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_price=product.price,
                quantity=cart_item.quantity,
                subtotal=subtotal
            )

            total_amount += subtotal

            # Stock কমানো
            product.stock -= cart_item.quantity
            product.save()

        # Final Total
        order.total_amount = total_amount
        order.save()

        # Order হওয়ার পরে Cart Empty
        cart_items.delete()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )             

class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        orders = (
            Order.objects
            .filter(user=request.user)
            .prefetch_related("items")
            .order_by("-created_at")
        )

        serializer = OrderSerializer(
            orders,
            many=True
        )

        return Response(serializer.data)

class PaymentCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment_create"

    @transaction.atomic
    def post(self, request):

        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        payment_method = serializer.validated_data[
            "payment_method"
        ]

        # শুধু নিজের Order-এর Payment করতে পারবে
        try:
            order = Order.objects.get(
                id=order_id,
                user=request.user
            )

        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Order Cancelled হলে Payment করা যাবে না
        if order.status == "cancelled":
            return Response(
                {
                    "detail": (
                        "Payment cannot be made for "
                        "a cancelled order."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # আগের Payment আছে কিনা
        payment = Payment.objects.filter(
            order=order
        ).first()

        # Payment সফল হয়ে থাকলে আবার করা যাবে না
        if payment and payment.status == "success":
            return Response(
                {"detail": "This order is already paid."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # নতুন Payment Record
        if not payment:

            payment = Payment.objects.create(
                order=order,
                payment_method=payment_method,
                amount=order.total_amount,
                status="pending"
            )

        else:
            # পুরোনো Failed/Pending Payment থাকলে update
            payment.payment_method = payment_method
            payment.amount = order.total_amount
            payment.status = "pending"
            payment.save()

        return Response(
            {
                "detail": "Payment request created successfully.",
                "payment": PaymentSerializer(payment).data,

                # পরে এখানে provider payment URL আসবে
                "next_step": (
                    "Redirect to the selected payment gateway."
                ),
            },
            status=status.HTTP_201_CREATED
        ) 

class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        try:
            payment = Payment.objects.select_related(
                "order"
            ).get(
                pk=pk,
                order__user=request.user
            )

        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK
        )  

class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "review_write"

    def post(self, request, product_id):

        # Product আছে কিনা check
        try:
            product = Product.objects.get(
                id=product_id,
                is_active=True
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # একই User আগে Review দিয়েছে কিনা
        if Review.objects.filter(
            user=request.user,
            product=product
        ).exists():
            return Response(
                {
                    "detail": (
                        "You have already reviewed "
                        "this product."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = serializer.save(
            user=request.user,
            product=product
        )

        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )             

class ProductReviewListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):

        reviews = (
            Review.objects
            .filter(
                product_id=product_id,
                product__is_active=True
            )
            .select_related("user")
            .order_by("-created_at")
        )

        serializer = ReviewSerializer(
            reviews,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )  

class ReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "review_write"

    def get_object(self, request, review_id):
        try:
            return Review.objects.select_related(
                "product"
            ).get(
                id=review_id,
                user=request.user
            )

        except Review.DoesNotExist:
            return None

    def patch(self, request, review_id):
        review = self.get_object(
            request,
            review_id
        )

        if not review:
            return Response(
                {"detail": "Review not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReviewSerializer(
            review,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, review_id):
        review = self.get_object(
            request,
            review_id
        )

        if not review:
            return Response(
                {"detail": "Review not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        review.delete()

        return Response(
            {"detail": "Review deleted successfully."},
            status=status.HTTP_200_OK
        )      

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "admin_dashboard"

    def get(self, request):

        total_users = User.objects.count()

        total_products = Product.objects.count()

        total_orders = Order.objects.count()

        pending_orders = Order.objects.filter(
            status="pending"
        ).count()

        processing_orders = Order.objects.filter(
            status="processing"
        ).count()

        delivered_orders = Order.objects.filter(
            status="delivered"
        ).count()

        # শুধু Delivered Order-এর Sales হিসাব করছি
        total_sales = (
            Order.objects
            .filter(status="delivered")
            .aggregate(
                total=Sum("total_amount")
            )["total"]
            or 0
        )

        recent_orders = (
            Order.objects
            .select_related("user", "address")
            .order_by("-created_at")[:10]
        )

        recent_orders_data = []

        for order in recent_orders:
            recent_orders_data.append({
                "id": order.id,
                "username": order.user.username,
                "total_amount": order.total_amount,
                "status": order.status,
                "created_at": order.created_at,
            })

        return Response(
            {
                "statistics": {
                    "total_users": total_users,
                    "total_products": total_products,
                    "total_orders": total_orders,
                    "pending_orders": pending_orders,
                    "processing_orders": processing_orders,
                    "delivered_orders": delivered_orders,
                    "total_sales": total_sales,
                },

                "recent_orders": recent_orders_data,
            },
            status=status.HTTP_200_OK
        )  

class AdminOrderListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):

        orders = (
            Order.objects
            .select_related("user", "address")
            .prefetch_related("items")
            .order_by("-created_at")
        )

        serializer = OrderSerializer(
            orders,
            many=True
        )

        return Response(serializer.data)

class AdminOrderStatusUpdateView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "admin_write"

    def patch(self, request, order_id):

        try:
            order = Order.objects.get(id=order_id)

        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminOrderStatusSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        order.status = serializer.validated_data["status"]
        order.save()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_200_OK
        )          

class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):

        users = (
            User.objects
            .all()
            .order_by("-date_joined")
        )

        users_data = []

        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_active": user.is_active,
                "date_joined": user.date_joined,
            })

        return Response(
            users_data,
            status=status.HTTP_200_OK
        )  

class AdminUserStatusSerializer(serializers.Serializer):

    is_active = serializers.BooleanField()

class AdminUserStatusUpdateView(APIView):
    permission_classes = [IsAdminUser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "admin_write"

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Jehetu admin nijei nijer status change korte parbe na, tai ekhane check kora hocche
        if user == request.user:
            return Response(
                {
                    "detail": "You cannot change your own account status."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AdminUserStatusSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        user.is_active = serializer.validated_data["is_active"]
        user.save()

        return Response(
            {
                "detail": "User status updated successfully.",
                "user_id": user.id,
                "is_active": user.is_active,
            },
            status=status.HTTP_200_OK
        )          