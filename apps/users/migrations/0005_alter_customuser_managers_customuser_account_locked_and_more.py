# Generated by Django 5.1.6 on 2025-02-20 20:43

import apps.users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_remove_customuser_address_and_more'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='customuser',
            managers=[
                ('objects', apps.users.models.CustomUserManager()),
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='account_locked',
            field=models.BooleanField(default=False, verbose_name='account locked'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='email_verified',
            field=models.BooleanField(default=False, verbose_name='email verified'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='failed_login_attempts',
            field=models.IntegerField(default=0, verbose_name='failed login attempts'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='last_failed_login',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last failed login'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='two_factor_enabled',
            field=models.BooleanField(default=False, verbose_name='two-factor authentication'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='two_factor_secret',
            field=models.CharField(blank=True, max_length=32, verbose_name='two-factor secret'),
        ),
    ]
