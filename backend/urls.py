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

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),

    path("login/", LoginView.as_view(), name="login"),

    path("logout/", LogoutView.as_view(), name="logout"),

    path("token/refresh/", RefreshView.as_view(), name="token_refresh"),

    path("me/", CurrentUserView.as_view(), name="current_user"),

    path("profile/",UserProfileView.as_view(),name="user-profile"),
]

urlpatterns += router.urls