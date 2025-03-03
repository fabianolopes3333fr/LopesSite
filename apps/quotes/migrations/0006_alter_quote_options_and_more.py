# Generated by Django 5.1.6 on 2025-02-22 12:07

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotes', '0005_quotephoto_rename_area_quote_area_size_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='quote',
            options={'ordering': ['-created_at'], 'verbose_name': 'devis', 'verbose_name_plural': 'devis'},
        ),
        migrations.RenameField(
            model_name='quote',
            old_name='project_description',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='quote',
            old_name='phone',
            new_name='phone_number',
        ),
        migrations.RemoveField(
            model_name='quote',
            name='admin_notes',
        ),
        migrations.RemoveField(
            model_name='quote',
            name='budget_range',
        ),
        migrations.RemoveField(
            model_name='quote',
            name='email',
        ),
        migrations.RemoveField(
            model_name='quote',
            name='estimated_price',
        ),
        migrations.RemoveField(
            model_name='quote',
            name='name',
        ),
        migrations.RemoveField(
            model_name='quote',
            name='preferred_date',
        ),
        migrations.RemoveField(
            model_name='quote',
            name='reference_photos',
        ),
        migrations.RemoveField(
            model_name='quote',
            name='service_type',
        ),
        migrations.AddField(
            model_name='quote',
            name='contact_preference',
            field=models.CharField(choices=[('email', 'Email'), ('phone', 'Téléphone'), ('both', 'Les deux')], default='email', max_length=20, verbose_name='préférence de contact'),
        ),
        migrations.AddField(
            model_name='quote',
            name='desired_start_date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='date de début souhaitée'),
        ),
        migrations.AddField(
            model_name='quote',
            name='project_type',
            field=models.CharField(choices=[('interior', 'Peinture Intérieure'), ('exterior', 'Peinture Extérieure'), ('commercial', 'Peinture Commerciale'), ('industrial', 'Peinture Industrielle'), ('decorative', 'Peinture Décorative'), ('floor', 'Parquet Flottant'), ('wallpaper', 'Papier Peint'), ('glass', 'Toile de Verre')], default='interior', max_length=50, verbose_name='type de projet'),
        ),
        migrations.AddField(
            model_name='quote',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quotes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='quote',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
