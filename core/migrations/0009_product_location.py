# Generated by Django 5.2 on 2025-04-09 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='location',
            field=models.CharField(max_length=200, null=True, verbose_name='Farm Location'),
        ),
    ]
