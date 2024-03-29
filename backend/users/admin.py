from django.contrib.admin import ModelAdmin, register

from users.models import User


@register(User)
class UserAdmin(ModelAdmin):

    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "role",
    )
    search_fields = ("username", "email")
    list_filter = (
        "username",
        "email",
    )
