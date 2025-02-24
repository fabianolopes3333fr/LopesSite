# apps/config/migrations/XXXX_create_config_permissions.py
from django.db import migrations

def create_config_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # Criar grupos
    editor_group, _ = Group.objects.get_or_create(name='Config Editor')
    style_editor_group, _ = Group.objects.get_or_create(name='Style Editor')
    
    # Adicionar permissões aos grupos
    page_content_type = ContentType.objects.get_for_model(apps.get_model('config', 'Page'))
    style_content_type = ContentType.objects.get_for_model(apps.get_model('config', 'SiteStyle'))
    
    editor_permissions = Permission.objects.filter(content_type=page_content_type)
    editor_group.permissions.add(*editor_permissions)
    
    style_permissions = Permission.objects.filter(content_type=style_content_type)
    style_editor_group.permissions.add(*style_permissions)

def reverse_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Config Editor', 'Style Editor']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('config', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_config_permissions, reverse_permissions),
    ]