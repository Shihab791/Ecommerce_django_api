from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.html import strip_tags
from rest_framework import serializers
from decimal import Decimal
from .models import UserProfile, Category, Product


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        max_length=254,
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        trim_whitespace=False,
        validators=[validate_password],
    )

    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        trim_whitespace=False,
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password",
            "confirm_password",
        ]

        extra_kwargs = {
            "username": {
                "required": True,
                "min_length": 3,
                "max_length": 150,
            },
        }

    def validate_username(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Username is required."
            )

        if not value.replace("_", "").replace("-", "").isalnum():
            raise serializers.ValidationError(
                "Use only letters, numbers, underscores or hyphens."
            )

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "This username is already taken."
            )

        return value

    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )

        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")

        email = validated_data.pop("email")

        user = User.objects.create_user(
            email=email,
            password=validated_data.pop("password"),
            **validated_data,
        )

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True
    )

    first_name = serializers.CharField(
        source="user.first_name",
        required=False,
        allow_blank=True,
        max_length=150,
    )

    last_name = serializers.CharField(
        source="user.last_name",
        required=False,
        allow_blank=True,
        max_length=150,
    )

    class Meta:
        model = UserProfile

        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "profile_picture",
        ]

        read_only_fields = [
            "username",
            "email",
        ]

    def validate_first_name(self, value):
        return value.strip()

    def validate_last_name(self, value):
        return value.strip()

    def validate_profile_picture(self, value):
        # File size limit: 5 MB
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Profile picture must be smaller than 5 MB."
            )

        # Allow only common image types
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]

        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Only JPEG, PNG, and WEBP images are allowed."
            )

        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})

        for field, value in user_data.items():
            setattr(instance.user, field, value)

        instance.user.save()

        return super().update(instance, validated_data)    


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Category name is required."
            )

        if strip_tags(value) != value:
            raise serializers.ValidationError(
                "HTML tags are not allowed."
            )

        queryset = Category.objects.filter(name__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "This category already exists."
            )

        return value

    def validate_description(self, value):
        if strip_tags(value) != value:
            raise serializers.ValidationError(
                "HTML tags are not allowed."
            )

        return value.strip()    


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    class Meta:
        model = Product

        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "price",
            "stock",
            "image",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Product name is required."
            )

        if strip_tags(value) != value:
            raise serializers.ValidationError(
                "HTML tags are not allowed."
            )

        return value

    def validate_description(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Description is required."
            )

        if strip_tags(value) != value:
            raise serializers.ValidationError(
                "HTML tags are not allowed."
            )

        return value

    def validate_price(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Price must be greater than zero."
            )

        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Stock cannot be negative."
            )

        return value

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Product image must be smaller than 5 MB."
            )

        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]

        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Only JPEG, PNG, and WEBP images are allowed."
            )

        return value    