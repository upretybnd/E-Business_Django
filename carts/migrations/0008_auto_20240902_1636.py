# Generated by Django 3.1 on 2024-09-02 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_variation'),
        ('carts', '0007_auto_20240831_2132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='variations',
            field=models.ManyToManyField(blank=True, to='store.Variation'),
        ),
    ]
