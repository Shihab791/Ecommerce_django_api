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
]

urlpatterns += router.urls