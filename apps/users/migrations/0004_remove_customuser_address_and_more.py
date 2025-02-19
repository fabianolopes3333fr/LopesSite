# Generated by Django 5.1.6 on 2025-02-19 18:02

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_newslettersubscription'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='address',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='phone_number',
        ),
        migrations.AddField(
            model_name='customuser',
            name='frist_name',
            field=models.CharField(blank=True, max_length=100, validators=[django.core.validators.RegexValidator(message='Ce champ doit contenir uniquement des lettres, des espaces et des tirets.', regex='^[a-zA-ZÀ-ÿ\\s\\-]+$')], verbose_name='first name'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=255, unique=True, validators=[django.core.validators.EmailValidator(message='Entrez une adresse email valide.')], verbose_name='email address'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='active'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='is_staff',
            field=models.BooleanField(default=False, verbose_name='staff status'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='last_name',
            field=models.CharField(blank=True, max_length=100, validators=[django.core.validators.RegexValidator(message='Ce champ doit contenir uniquement des lettres, des espaces et des tirets.', regex='^[a-zA-ZÀ-ÿ\\s\\-]+$')], verbose_name='last name'),
        ),
        migrations.CreateModel(
            name='ClientProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(blank=True, max_length=15, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')], verbose_name='phone number')),
                ('address', models.TextField(verbose_name='Adresse')),
                ('postal_code', models.CharField(max_length=10, verbose_name='Code Postal')),
                ('city', models.CharField(max_length=100, verbose_name='Ville')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profile',
                'verbose_name_plural': 'Profiles',
            },
        ),
    ]
