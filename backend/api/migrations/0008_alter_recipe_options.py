# Generated by Django 3.2.16 on 2024-03-23 13:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0007_auto_20240322_1831"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="recipe",
            options={
                "default_related_name": "recipe",
                "ordering": ["-pub_date"],
                "verbose_name": "Рецепт",
                "verbose_name_plural": "Рецепты",
            },
        ),
    ]
