from datetime import datetime as dt

from api.filters import IngredientSearchFilter, RecipeFilter
from api.models import Favorite, Follow, Ingredient, Recipe, ShoppingList, Tag
from api.paginations import CustomPagination
from api.permissions import IsCurrentUserOrReadOnly, IsOwnerOrReadOnly
from api.serializers import (
    CreateUserSerializer,
    FavoriteSerializer,
    FollowSerializer,
    GETUserSerializer,
    IngredientSerializer,
    RecipeGETSerializer,
    RecipeWriteSerializer,
    ShoppingListSerializer,
    TagSerializer,
)
from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    Вьюсет модели User и Follow с возможностью смены пороля.
    """

    queryset = User.objects.all()
    permission_classes = (IsCurrentUserOrReadOnly,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return GETUserSerializer
        return CreateUserSerializer

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path="me",
    )
    def get_me(self, request):
        serializer = GETUserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["POST"], detail=False, permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid(raise_exception=True):
            self.request.user.set_password(serializer.data["new_password"])
            self.request.user.save()
            return Response(
                "Пароль успешно изменен", status=status.HTTP_204_NO_CONTENT
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, *args, **kwargs):
        following = get_object_or_404(User, id=self.kwargs.get("pk"))
        user = self.request.user
        if request.method == "POST":
            serializer = FollowSerializer(
                data=request.data,
                context={"request": request, "following": following},
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(following=following, user=user)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                {"errors": "Объект не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )
        follow = Follow.objects.filter(following=following, user=user)
        if not follow:
            return Response(
                {"errors": "Подписка не найдена"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        follow.delete()
        return Response("Вы отписались", status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        follows = Follow.objects.filter(user=self.request.user)
        pages = self.paginate_queryset(follows)
        serializer = FollowSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Вьюсет для модели тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Вьюсет для модели ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ("^name",)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет модели Recipe, Favorite, ShoppingList
    с возможностью скачивания списка покупок в формате txt файла
    """

    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeGETSerializer
        return RecipeWriteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def favorite_shopping(
        self,
        request,
        model,
        post_serializer,
        post_400_message,
        delete_204_message,
    ):
        user = self.request.user
        id = self.kwargs.get("pk")
        try:
            recipe = get_object_or_404(Recipe, id=id)
        except Exception:
            if request.method == "POST":
                return Response(
                    {"errors": "Рецепт не найден"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"errors": "Рецепт не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )
        favorite_recipe = model.objects.filter(user=user, recipe=recipe)
        if request.method == "POST":
            if favorite_recipe.exists():
                return Response(
                    {"errors": post_400_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = post_serializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(user=user, recipe=recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        if favorite_recipe.exists():
            favorite_recipe.delete()
            return Response(
                delete_204_message, status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {"errors": "Объект не найден"}, status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, **kwargs):
        response = self.favorite_shopping(
            request,
            Favorite,
            FavoriteSerializer,
            "Рецепт уже в избранном",
            "Рецепт удалён из избранного",
        )
        return response

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, **kwargs):
        response = self.favorite_shopping(
            request,
            ShoppingList,
            ShoppingListSerializer,
            "Рецепт уже в списке покупок",
            "Рецепт удалён из списка покупок",
        )
        return response

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):

        user = User.objects.get(id=self.request.user.pk)
        if user.shopping_cart.exists():
            ingredients = (
                (
                    Ingredient.objects.filter(
                        recipe_ingredients__recipe__shopping_cart__user=user
                    )
                )
                .values("name", measurement=F("measurement_unit"))
                .annotate(amount=Sum("recipe_ingredients__amount"))
            )
            shopping_list = [
                f"Список покупок для рецептов\n"
                f'{dt.now().strftime("%d-%m-%Y")}\n'
            ]
            for ingredient in ingredients:
                print(ingredient)
                shopping_list += (
                    f'{ingredient["name"]} '
                    f'({ingredient["measurement"]}) - '
                    f'{ingredient["amount"]}\n'
                )
            filename = "shopping_list.txt"
            response = HttpResponse(shopping_list, content_type="text/plain")
            response[
                "Content-Disposition"
            ] = f"attachment; filename={filename}"
            return response

        return Response(
            "Список покупок пуст.", status=status.HTTP_404_NOT_FOUND
        )
