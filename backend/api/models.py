from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()

MIN_AMOUNT = 1
MAX_AMOUNT = 32000


class Follow(models.Model):
    """
    Модель подписок
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )

    class Meta:
        ordering = ["following"]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F("following")),
                name="user_not_followed_himself",
            ),
            models.UniqueConstraint(
                fields=["user", "following"], name="unique follow"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.following}"


class Tag(models.Model):
    """
    Модель тэгов
    """

    COLOR_CHOICES = [
        ("#32CD32", "GREEN"),
        ("#FFFF00", "YELLOW"),
        ("#800080", "PURPLE"),
    ]

    name = models.CharField(verbose_name="Тэг", max_length=150, unique=True,)

    color = models.CharField(
        verbose_name="Цвет", max_length=7, unique=True, choices=COLOR_CHOICES,
    )
    slug = models.CharField(
        verbose_name="Слаг тэга", max_length=150, unique=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name}"


class Ingredient(models.Model):
    """
    Модель ингредиентов
    """

    name = models.CharField(
        verbose_name="Название ингредиента",
        max_length=150,
        db_index=True,
        help_text="Введите название ингредиента",
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения",
        max_length=150,
        help_text="Введите единицу измерения",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self) -> str:
        return f"{self.name}"


class Recipe(models.Model):
    """
    Модель рецептов
    """

    author = models.ForeignKey(
        User,
        verbose_name="Автор рецепта",
        on_delete=models.CASCADE,
        help_text="Автор рецепта",
    )
    ingredients = models.ManyToManyField(
        Ingredient, through="IngredientRecipe", verbose_name="Ингредиент"
    )
    tags = models.ManyToManyField(
        Tag, verbose_name="Название тега", help_text="Выберите tag"
    )
    text = models.TextField(
        verbose_name="Описание рецепта",
        help_text="Опишите приготовление рецепта",
    )
    name = models.CharField(
        verbose_name="Название рецепта",
        max_length=150,
        help_text="Введите название рецепта",
        db_index=True,
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления",
        validators=[
            MinValueValidator(MIN_AMOUNT, "Минимальное время приготовления"),
            MaxValueValidator(MAX_AMOUNT, "Максимальное время приготовления")
        ],
        help_text="Укажите время приготовления рецепта в минутах",
    )
    image = models.ImageField(
        verbose_name="Картинка рецепта",
        upload_to="media/",
        help_text="Добавьте изображение рецепта",
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True
    )

    class Meta:
        ordering = ["-pub_date"]
        default_related_name = "recipe"
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "author"], name="unique_recipe"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name}"


class IngredientRecipe(models.Model):
    """
    Связующая модель ингредиентов и рецептов
    с дополнительным полем 'количество'
    """

    recipe = models.ForeignKey(
        Recipe,
        related_name="recipe_ingredients",
        verbose_name="Название рецепта",
        on_delete=models.CASCADE,
        help_text="Выберите рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name="recipe_ingredients",
        verbose_name="Ингредиент",
        on_delete=models.CASCADE,
        help_text="Укажите ингредиенты",
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_AMOUNT, "Минимальное время приготовления"),
            MaxValueValidator(MAX_AMOUNT, "Максимальное время приготовления")
        ],
        verbose_name="Количество",
        help_text="Укажите количество ингредиента",
    )

    class Meta:
        ordering = ["ingredient"]
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_ingredients"
            )
        ]

    def __str__(self) -> str:
        return f"{self.ingredient} {self.amount}"


class Favorite(models.Model):
    """
    Связующая модель пользователя и рецепта. Список избранных рецептов
    """

    user = models.ForeignKey(
        User,
        related_name="favorite",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="favorite",
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        ordering = ["recipe"]
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite"
            )
        ]

    def __str__(self) -> str:
        return f"{self.recipe}"


class ShoppingList(models.Model):
    """
    Связующая модель пользователя и рецепта.
    Список рецептов, добавленных в список покупок
    """

    user = models.ForeignKey(
        User,
        related_name="shopping_cart",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name="shopping_cart",
        verbose_name="Рецепт для приготовления",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["recipe"]
        verbose_name = "Рецепт для покупки"
        verbose_name_plural = "Рецепты для покупки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_cart"
            )
        ]

    def __str__(self) -> str:
        return f"{self.recipe}"
