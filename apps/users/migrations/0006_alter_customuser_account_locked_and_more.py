# Generated by Django 5.1.6 on 2025-02-20 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_customuser_managers_customuser_account_locked_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='account_locked',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='two_factor_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
