# your_cms_app/templates/tests/test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from ..models import (
    TemplateCategory, TemplateType, DjangoTemplate, 
    ComponentTemplate, LayoutTemplate
)

class TemplateListViewTests(TestCase):
    """Testes para a view TemplateListView"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        
        # Adiciona permissão para visualizar templates
        content_type = ContentType.objects.get_for_model(DjangoTemplate)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='view_djangotemplate'
        )
        self.user.user_permissions.add(permission)
        
        # Cria templates para teste
        self.category = TemplateCategory.objects.create(
            name='Test Category',
            created_by=self.user,
            updated_by=self.user
        )
        self.template_type = TemplateType.objects.create(
            name='Test Type',
            type='page',
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
        
        for i in range(5):
            DjangoTemplate.objects.create(
                name=f'Test Template {i}',
                file_path=f'templates/test_template_{i}.html',
                type=self.template_type,
                created_by=self.user,
                updated_by=self.user,
                is_active=True
            )
    
    def test_login_required(self):
        """Testa se a view requer login"""
        url = reverse('templates:template_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirecionamento para login
        
        # Faz login e tenta novamente
        self.client.login(username='testuser', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_templates_in_context(self):
        """Testa se os templates são passados corretamente para o contexto"""
        self.client.login(username='testuser', password='password')
        url = reverse('templates:template_list')
        response = self.client.get(url)
        
        self.assertIn('templates', response.context)
        self.assertEqual(len(response.context['templates']), 5)


class ComponentPreviewViewTests(TestCase):
    """Testes para a view ComponentPreviewView"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        
        # Adiciona permissão para visualizar componentes
        content_type = ContentType.objects.get_for_model(ComponentTemplate)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='view_componenttemplate'
        )
        self.user.user_permissions.add(permission)
        
        # Cria um componente para teste
        self.component = ComponentTemplate.objects.create(
            name='Test Component',
            slug='test-component',
            component_type='card',
            template_code='<div class="card">{{ title }}</div>',
            default_context='{"title": "Default Title"}',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_component_preview(self):
        """Testa a visualização da prévia do componente"""
        self.client.login(username='testuser', password='password')
        url = reverse('templates:component_preview', args=[self.component.slug])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('component', response.context)
        self.assertEqual(response.context['component'], self.component)
        self.assertIn('rendered_component', response.context)
        self.assertIn('Default Title', response.context['rendered_component'])