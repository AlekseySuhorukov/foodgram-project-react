from django.utils.html import format_html
from django.contrib.admin import (
    display,
    ModelAdmin,
    TabularInline,
    register,
    site
)

from api.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingList,
    Tag,
)

class IngredientsInline(TabularInline):

    model = IngredientRecipe
    extra = 3


@register(Follow)
class FollowAdmin(ModelAdmin):

    list_display = ('user', 'user')
    list_filter = ('user',)
    search_fields = ('user',)


@register(Favorite)
class FavoriteAdmin(ModelAdmin):

    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user',)


@register(ShoppingList)
class ShoppingListAdmin(ModelAdmin):

    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user',)


@register(IngredientRecipe)
class IngredientRecipeAdmin(ModelAdmin):

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('name',)


@register(Recipe)
class RecipeAdmin(ModelAdmin):

    list_display = ('id', 'name', 'author', 'count_favorites')
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('name', 'author__username', 'tags__name')
    inlines = [IngredientsInline]

    def count_favorites(self, obj):
        return obj.favorite.count()

    count_favorites.short_description = 'Количество добавлений в избранное'


@register(Tag)
class TagAdmin(ModelAdmin):

    list_display = ('id', 'name', 'slug', 'color')
    list_filter = ('name',)
    search_fields = ('name',)

    @display(description="Colored")
    def color_code(self, obj):
        return format_html(
            '<span style="color: #{};">{}</span>', obj.color[1:], obj.color
        )

@register(Ingredient)
class IngredientAdmin(ModelAdmin):

    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)
