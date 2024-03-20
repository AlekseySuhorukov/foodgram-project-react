from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError

from api.models import Follow, Tag, Ingredient, Recipe, Favorite, ShoppingList, IngredientRecipe

User = get_user_model()

class CreateUserSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True},}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class GETUserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous or (user == obj):
            return False
        return Follow.objects.filter(user=user, following=obj).exists()


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = "id", "name", "image", "cooking_time"
        read_only_fields = ("__all__",)

class FollowSerializer(serializers.ModelSerializer):

    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
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
        limit = self.context.get('request').GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.following)
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj) -> int:
        return Recipe.objects.filter(author=obj.following).count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )
        read_only_fields = '__all__',

class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер модели Ingredient."""
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )
        read_only_fields = '__all__',

class FavoriteSerializer(serializers.ModelSerializer):

    name = serializers.ReadOnlyField(
        source='recipe.name',
        read_only=True)
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True)
    coocking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='recipe',
        read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'coocking_time')


class ShoppingListSerializer(FavoriteSerializer):

    class Meta:
        model = ShoppingList
        fields = ('id', 'name', 'image', 'coocking_time')


class GETIngredientRecipeSerializer(serializers.ModelSerializer):
    """Serializer для связаной модели Recipe и Ingredient."""
    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGETSerializer(serializers.ModelSerializer):
    """
    Serializer для модели Recipe - чтение данных.
    Находится ли рецепт в избранном, списке покупок.
    Получение списка ингредиентов с добавленным полем
    amount из промежуточной модели.
    """
    author = GETUserSerializer()
    tags = TagSerializer(
        many=True,
        read_only=True)
    ingredients = GETIngredientRecipeSerializer(
        many=True,
        source='recipe_ingredients',
        read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingList.objects.filter(recipe=obj).exists()


class POSTIngredientSerializer(serializers.ModelSerializer):
    """
    Serializer для поля ingredient модели Recipe - создание ингредиентов.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Serializer для модели Recipe - запись / обновление / удаление данных."""
    ingredients = POSTIngredientSerializer(
        many=True,
        write_only=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault())

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError({'ingredients': 'Нужно выбрать ингредиент!'})
        ingredients_list = []
        for ingredient in value:
            id_ingredient = ingredient['id']
            if id_ingredient in ingredients_list:
                raise ValidationError({'ingredients': 'Ингридиенты повторяются!'})
            if int(ingredient['amount']) <= 0:
                raise ValidationError({'amount': 'Количество должно быть больше 0!'})
            ingredients_list.append(id_ingredient)
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError({'tags': 'Нужно выбрать тег!'})
        if len(set(value)) != len(value):
            raise ValidationError({'tags': 'Теги повторяются!'})
        return value

    def to_representation(self, instance):
        ingredients = super().to_representation(instance)
        print('777777777777777777777777777777777777777777777777777777')
        print(ingredients)
        ingredients['ingredients'] = GETIngredientRecipeSerializer(
            instance.recipe_ingredients.all(), many=True).data
        return ingredients

    def add_ingredients(self, ingredients, tags, recipe):
        for ingredient in ingredients:
            IngredientRecipe.objects.update_or_create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'])
            recipe.tags.set(tags)

    # def create(self, validated_data):
    #     print(validated_data)
    #     ingredients = validated_data.pop('ingredients')
    #     print(ingredients)
    #     tags = validated_data.pop('tags')
    #     # print(tags)
    #     print(validated_data)
    #     recipe = super().create(validated_data)
    #     # self.add_ingredients(self, ingredients=ingredients, tags=tags, recipe=recipe)
    #     return recipe




    def create(self, validated_data: dict) -> Recipe:
        """Создаёт рецепт.

        Args:
            validated_data (dict): Данные для создания рецепта.

        Returns:
            Recipe: Созданый рецепт.
        """
        print(validated_data)
        tags: list[int] = validated_data.pop("tags")
        print(tags)
        ingredients: dict[int, tuple] = validated_data.pop("ingredients")
        print(ingredients)
        print(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        print('777777777777777777777777777777777777777777777777777777')
        recipe.tags.set(tags)

        objs = []

        for ingredient, amount in ingredients.values():
            objs.append(
                IngredientRecipe(
                    recipe=recipe, ingredients=ingredient, amount=amount
                )
            )

        IngredientRecipe.objects.bulk_create(objs)
        return recipe


    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        self.add_ingredients(ingredients, tags, instance)
        return super().update(instance, validated_data)