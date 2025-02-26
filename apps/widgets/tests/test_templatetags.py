from django.test import TestCase
from django.template import Context, Template
from django.contrib.auth.models import User
from ..models import (
    TemplateCategory, TemplateType, DjangoTemplate, 
    TemplateRegion, ComponentTemplate, ComponentInstance
)

class TemplateTagsTests(TestCase):
    """Testes para as template tags do sistema de templates"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        
        # Cria estrutura de dados para teste
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
        self.django_template = DjangoTemplate.objects.create(
            name='Test Template',
            slug='test-template',
            file_path='templates/test_template.html',
            type=self.template_type,
            created_by=self.user,
            updated_by=self.user
        )
        self.region = TemplateRegion.objects.create(
            name='Test Region',
            slug='test-region',
            template=self.django_template
        )
        self.component = ComponentTemplate.objects.create(
            name='Test Component',
            slug='test-component',
            component_type='card',
            template_code='<div class="card">{{ title }}</div>',
            default_context='{"title": "Default Title"}',
            created_by=self.user,
            updated_by=self.user
        )
        self.instance = ComponentInstance.objects.create(
            component=self.component,
            region=self.region,
            order=0,
            context_data='{"title": "Test Title"}',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_render_region_tag(self):
        """Testa a tag render_region"""
        template = Template(
            '{% load template_tags %}'
            '{% render_region "test-region" "test-template" %}'
        )
        context = Context({})
        rendered = template.render(context)
        self.assertIn('Test Title', rendered)
    
    def test_component_tag(self):
        """Testa a tag component"""
        template = Template(
            '{% load template_tags %}'
            '{% component "test-component" title="Custom Title" %}'
        )
        context = Context({})
        rendered = template.render(context)
        self.assertIn('Custom Title', rendered)