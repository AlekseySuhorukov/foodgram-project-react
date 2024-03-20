from datetime import datetime as dt
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status, mixins
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.shortcuts import render
from djoser.serializers import SetPasswordSerializer
from django.db.models import F, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend

from api.serializers import CreateUserSerializer, GETUserSerializer, FollowSerializer, TagSerializer, IngredientSerializer, FavoriteSerializer, ShoppingListSerializer, RecipeWriteSerializer, RecipeGETSerializer
from api.paginations import CustomPagination
from api.models import Tag, Follow, Ingredient, Favorite, Recipe
from api.filters import IngredientSearchFilter, RecipeFilter
from api.permissions import IsOwnerOrAdminOrReadOnly, IsCurrentUserOrAdminOrReadOnly


User = get_user_model()

def favorite_shopping(self, user, request, post_serializer, id, post_400_message, delete_204_message):
    recipe = get_object_or_404(Recipe, id)
    favorite_recipe = get_object_or_404(Favorite, user=user, recipe=recipe)
    if request.method == 'POST':
        if favorite_recipe.exists():
            return Response({'errors': post_400_message},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = post_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=user, recipe=recipe)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)
    if favorite_recipe.exists():
        favorite_recipe.delete()
        return Response(delete_204_message,
                    status=status.HTTP_204_NO_CONTENT)
    return Response({'errors': 'Объект не найден'},
                        status=status.HTTP_404_NOT_FOUND)


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    permission_classes = (IsCurrentUserOrAdminOrReadOnly, )
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return GETUserSerializer
        return CreateUserSerializer

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me'
    )
    def get_me(self, request):
        serializer = GETUserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['POST'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            self.request.user.set_password(serializer.data["new_password"])
            self.request.user.save()
            return Response('Пароль успешно изменен',
                            status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        following = get_object_or_404(User, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            serializer = FollowSerializer(
                data=request.data,
                context={'request': request, 'following': following}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(following=following, user=user)
                return Response({'Подписка создана': serializer.data},
                                status=status.HTTP_201_CREATED)
            return Response({'errors': 'Объект не найден'},
                            status=status.HTTP_404_NOT_FOUND)
        follow = get_object_or_404(Follow, following=following, user=user)
        follow.delete()
        return Response('Вы отписались', status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        follows = Follow.objects.filter(user=self.request.user)
        pages = self.paginate_queryset(follows)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Функция для модели тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny, )

class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Функция для модели ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (IngredientSearchFilter, )
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет модели Recipe: [GET, POST, DELETE, PATCH]."""
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrAdminOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    pagination_class = CustomPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeGETSerializer
        return RecipeWriteSerializer



    @action(detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, **kwargs):
        favorite_shopping(
            self,
            user=self.request.user,
            request=request,
            post_serializer=FavoriteSerializer,
            id=self.kwargs.get('pk'),
            post_400_message='Рецепт уже в избранном',
            delete_204_message='Рецепт удалён из избранного'
        )

    @action(detail=True,
            methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        favorite_shopping(
            self,
            user=self.request.user,
            request=request,
            post_serializer=ShoppingListSerializer,
            id=self.kwargs.get('pk'),
            post_400_message='Рецепт уже в списке покупок',
            delete_204_message='Рецепт удалён из списка покупок'
        )


    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):

        user = User.objects.get(id=self.request.user.pk)
        if user.shopping_list.exists():
            ingredients = (
                Ingredient.objects.filter(recipe_ingredients__recipe__shopping_list__user=user)
                .values("name", measurement=F('measurement_unit'))
                .annotate(amount=Sum('recipe_ingredients__amount'))
            )
            shopping_list = [
                f'Список покупок для рецептов\n'
                f'{dt.now().strftime("%d-%m-%Y")}\n'
            ]
            for ingredient in ingredients:
                shopping_list += (
                    f'{ingredient["ingredient__name"]} '
                    f'({ingredient["ingredient__measurement_unit"]}) - '
                    f'{ingredient["amounts"]}\n'
                )
            filename = 'shopping_list.txt'
            response = HttpResponse(shopping_list, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response

        return Response('Список покупок пуст.',
                        status=status.HTTP_404_NOT_FOUND)
