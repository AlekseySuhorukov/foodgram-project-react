from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from api.models import (Favorite, Follow, Ingredient, IngredientRecipe, Recipe,
                        ShoppingList, Tag)

User = get_user_model()

MIN_AMOUNT = 1
MAX_AMOUNT = 32000


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class GETUserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous or (user == obj):
            return False
        return Follow.objects.filter(user=user, following=obj).exists()


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = "id", "name", "image", "cooking_time"
        read_only_fields = ("__all__",)


class FollowSerializer(serializers.ModelSerializer):

    email = serializers.ReadOnlyField(source="following.email")
    id = serializers.ReadOnlyField(source="following.id")
    username = serializers.ReadOnlyField(source="following.username")
    first_name = serializers.ReadOnlyField(source="following.first_name")
    last_name = serializers.ReadOnlyField(source="following.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(*args) -> bool:
        return True

    def get_recipes(self, obj) -> list:
        limit = self.context["request"].GET.get("recipes_limit")
        recipes = Recipe.objects.filter(author=obj.following)
        if limit and limit.isdigit():
            recipes = recipes[: int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj) -> int:
        return obj.user.recipe.count()

    def validate(self, data):
        following = self.context.get("following")
        user = self.context["request"].user
        if user.user.filter(following=following).exists():
            raise ValidationError(
                detail="Вы уже подписаны", code=status.HTTP_400_BAD_REQUEST
            )
        if user == following:
            raise ValidationError(
                detail="Нельзя подписаться на себя",
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")
        read_only_fields = ("__all__",)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = ("__all__",)


class FavoriteSerializer(serializers.ModelSerializer):

    name = serializers.ReadOnlyField(source="recipe.name", read_only=True)
    image = serializers.ImageField(source="recipe.image", read_only=True)
    cooking_time = serializers.IntegerField(
        source="recipe.cooking_time", read_only=True
    )
    id = serializers.PrimaryKeyRelatedField(source="recipe", read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "name", "image", "cooking_time")


class ShoppingListSerializer(FavoriteSerializer):
    class Meta:
        model = ShoppingList
        fields = ("id", "name", "image", "cooking_time")


class GETIngredientRecipeSerializer(serializers.ModelSerializer):
    """Serializer для связующей модели IngredientRecipe."""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeGETSerializer(serializers.ModelSerializer):
    """
    Serializer для модели Recipe для безопасных методов.
    """

    author = GETUserSerializer()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = GETIngredientRecipeSerializer(
        many=True, source="recipe_ingredients", read_only=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.favorite.exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.shopping_cart.exists()


class POSTIngredientSerializer(serializers.ModelSerializer):
    """
    Serializer для поля ingredient модели Recipe. Создание ингредиентов.
    """

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ("id", "amount")

    def validate_amount(self, value):
        if value < MIN_AMOUNT:
            raise ValidationError({"amount": "Меньше допустимого"})
        if value > MAX_AMOUNT:
            raise ValidationError({"amount": "Больше допустимого"})
        return value


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Serializer для модели Recipe для небезопасных методов"""

    ingredients = POSTIngredientSerializer(many=True, write_only=True,)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = ("id", "is_favorited", "is_in_shopping_cart")

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.favorite.exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.shopping_cart.exists()

    def validate(self, obj):
        if not obj.get("ingredients"):
            raise ValidationError({"ingredients": "Поле обязательное"})
        if not obj.get("tags"):
            raise ValidationError({"tags": "Поле обязательное"})
        return obj

    def validate_cooking_time(self, value):
        if value < MIN_AMOUNT:
            raise ValidationError({"amount": "Меньше допустимого"})
        if value > MAX_AMOUNT:
            raise ValidationError({"amount": "Больше допустимого"})
        return value

    def validate_image(self, value):
        if not value:
            raise ValidationError({"image": "Нужно добавить картинку!"})
        return value

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError({"ingredients": "Нужно выбрать ингредиент!"})
        ingredients_set = set()
        for ingredient in value:
            id_ingredient = ingredient["id"]
            if id_ingredient in ingredients_set:
                raise ValidationError(
                    {"ingredients": "Ингридиенты повторяются!"}
                )
            ingredients_set.add(id_ingredient)
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError({"tags": "Нужно выбрать тег!"})
        if len(set(value)) != len(value):
            raise ValidationError({"tags": "Теги повторяются!"})
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["ingredients"] = GETIngredientRecipeSerializer(
            instance.recipe_ingredients.all(), many=True
        ).data
        data["tags"] = TagSerializer(instance.tags.all(), many=True).data
        data["author"] = GETUserSerializer(
            instance.author, context={"request": self.context["request"]}
        ).data
        return data

    def add_ingredients_tags(self, ingredients, tags, recipe):
        obj = []
        for ingredient in ingredients:
            obj.append(
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=ingredient["id"],
                    amount=ingredient["amount"],
                )
            )
        IngredientRecipe.objects.bulk_create(obj)
        recipe.tags.set(tags)

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = super().create(validated_data)
        self.add_ingredients_tags(ingredients, tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        instance.ingredients.clear()
        self.add_ingredients_tags(ingredients, tags, instance)
        return super().update(instance, validated_data)
