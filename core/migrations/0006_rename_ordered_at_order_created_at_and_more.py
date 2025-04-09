# Generated by Django 5.2 on 2025-04-08 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='ordered_at',
            new_name='created_at',
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending', max_length=10),
        ),
        migrations.AlterField(
            model_name='order',
            name='total_price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
