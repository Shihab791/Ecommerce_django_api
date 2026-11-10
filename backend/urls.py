from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    RefreshView,
    CurrentUserView,
    UserProfileView,
    CategoryViewSet,
    ProductViewSet,
    WishlistListCreateView,
    WishlistDeleteView,
    CartListCreateView,
    CartItemDetailView,
    AddressViewSet,
    OrderCreateView,
    OrderHistoryView,
    PaymentCreateView,
    PaymentStatusView,
    ReviewCreateView,
    ProductReviewListView,
    ReviewDetailView,
    AdminDashboardView,
    AdminOrderListView,
    AdminOrderStatusUpdateView,
    AdminUserListView,
    AdminUserStatusUpdateView,
)

router = DefaultRouter()

router.register(
    "categories",
    CategoryViewSet,
    basename="category"
)
router.register(
    "products",
    ProductViewSet,
    basename="product"
)

router.register(
    "addresses",
    AddressViewSet,
    basename="address"
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),

    path("login/", LoginView.as_view(), name="login"),

    path("logout/", LogoutView.as_view(), name="logout"),

    path("token/refresh/", RefreshView.as_view(), name="token_refresh"),

    path("me/", CurrentUserView.as_view(), name="current_user"),

    path("profile/",UserProfileView.as_view(),name="user-profile"),

    path("wishlist/",WishlistListCreateView.as_view(),name="wishlist"),

    path("wishlist/<int:pk>/",WishlistDeleteView.as_view(),name="wishlist-delete"),

    path("cart/",CartListCreateView.as_view(),name="cart"),

    path("cart/<int:pk>/",CartItemDetailView.as_view(),name="cart-item-detail"),

    path("orders/create/",OrderCreateView.as_view(),name="order-create"),

    path("orders/",OrderHistoryView.as_view(),name="order-history"),

    path("payments/create/",PaymentCreateView.as_view(),name="payment-create"),

    path("payments/<int:pk>/status/",PaymentStatusView.as_view(),name="payment-status"),

    path("products/<int:product_id>/reviews/",ProductReviewListView.as_view(),name="product-review-list"),

    path("products/<int:product_id>/reviews/create/",ReviewCreateView.as_view(),name="review-create"),

    path("reviews/<int:review_id>/",ReviewDetailView.as_view(),name="review-detail"),

    path("admin/dashboard/",AdminDashboardView.as_view(),name="admin-dashboard"),

    path("admin/orders/",AdminOrderListView.as_view(),name="admin-orders"),

    path("admin/orders/<int:order_id>/status/",AdminOrderStatusUpdateView.as_view(),name="admin-order-status"),

    path("admin/users/",AdminUserListView.as_view(),name="admin-users"),

    path("admin/users/<int:user_id>/status/",AdminUserStatusUpdateView.as_view(),name="admin-user-status"),
]

urlpatterns += router.urls