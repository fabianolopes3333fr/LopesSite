from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import (
    TemplateCategory, TemplateType, DjangoTemplate, 
    TemplateRegion, LayoutTemplate, ComponentTemplate, 
    ComponentInstance, WidgetArea, Widget, WidgetInstance
)

class TemplateCategoryTests(TestCase):
    """Testes para o modelo TemplateCategory"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        self.category = TemplateCategory.objects.create(
            name='Test Category',
            description='Test category description',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_category_creation(self):
        """Testa se uma categoria é criada corretamente"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.slug, 'test-category')
        self.assertEqual(self.category.description, 'Test category description')
        self.assertTrue(self.category.is_active)
    
    def test_str_representation(self):
        """Testa a representação em string do objeto"""
        self.assertEqual(str(self.category), 'Test Category')


class TemplateTypeTests(TestCase):
    """Testes para o modelo TemplateType"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
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
    
    def test_template_type_creation(self):
        """Testa se um tipo de template é criado corretamente"""
        self.assertEqual(self.template_type.name, 'Test Type')
        self.assertEqual(self.template_type.slug, 'test-type')
        self.assertEqual(self.template_type.type, 'page')
        self.assertEqual(self.template_type.category, self.category)
        self.assertTrue(self.template_type.is_active)


class DjangoTemplateTests(TestCase):
    """Testes para o modelo DjangoTemplate"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
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
            file_path='templates/test_template.html',
            type=self.template_type,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_django_template_creation(self):
        """Testa se um template Django é criado corretamente"""
        self.assertEqual(self.django_template.name, 'Test Template')
        self.assertEqual(self.django_template.slug, 'test-template')
        self.assertEqual(self.django_template.file_path, 'templates/test_template.html')
        self.assertEqual(self.django_template.type, self.template_type)
        self.assertTrue(self.django_template.is_active)
    
    def test_get_absolute_url(self):
        """Testa o método get_absolute_url"""
        url = self.django_template.get_absolute_url()
        self.assertIn(self.django_template.slug, url)


class ComponentTemplateTests(TestCase):
    """Testes para o modelo ComponentTemplate"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        self.category = TemplateCategory.objects.create(
            name='Component Category',
            created_by=self.user,
            updated_by=self.user
        )
        self.component = ComponentTemplate.objects.create(
            name='Test Component',
            component_type='card',
            template_code='<div class="card">{{ title }}</div>',
            default_context='{"title": "Default Title"}',
            category=self.category,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_component_creation(self):
        """Testa se um componente é criado corretamente"""
        self.assertEqual(self.component.name, 'Test Component')
        self.assertEqual(self.component.slug, 'test-component')
        self.assertEqual(self.component.component_type, 'card')
        self.assertEqual(self.component.template_code, '<div class="card">{{ title }}</div>')
        self.assertEqual(self.component.category, self.category)
        self.assertTrue(self.component.is_active)
    
    def test_render_method(self):
        """Testa o método render do componente"""
        context = {'title': 'Custom Title'}
        rendered = self.component.render(context)
        self.assertIn('Custom Title', rendered)
        
        # Testa com contexto padrão
        rendered = self.component.render()
        self.assertIn('Default Title', rendered)