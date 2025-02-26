from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from ..models import (
    PageCategory, PageTemplate, FieldGroup, FieldDefinition, 
    Page, PageVersion, PageFieldValue, PageComment
)

class PageCategoryTests(TestCase):
    """Testes para o modelo PageCategory"""
    
    def setUp(self):
        self.category = PageCategory.objects.create(
            name='Test Category',
            description='Test category description'
        )
    
    def test_category_creation(self):
        """Testa se uma categoria de página é criada corretamente"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.slug, 'test-category')
        self.assertEqual(self.category.description, 'Test category description')
        self.assertTrue(self.category.is_active)
    
    def test_str_representation(self):
        """Testa a representação em string do objeto"""
        self.assertEqual(str(self.category), 'Test Category')


class PageTemplateTests(TestCase):
    """Testes para o modelo PageTemplate"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        self.template = PageTemplate.objects.create(
            name='Test Template',
            layout='default',
            template_file='templates/page_templates/default.html',
            created_by=self.user
        )
    
    def test_template_creation(self):
        """Testa se um template de página é criado corretamente"""
        self.assertEqual(self.template.name, 'Test Template')
        self.assertEqual(self.template.slug, 'test-template')
        self.assertEqual(self.template.layout, 'default')
        self.assertEqual(self.template.template_file, 'templates/page_templates/default.html')
        self.assertTrue(self.template.is_active)
    
    def test_str_representation(self):
        """Testa a representação em string do objeto"""
        self.assertEqual(str(self.template), 'Test Template')


class PageTests(TestCase):
    """Testes para o modelo Page"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        self.category = PageCategory.objects.create(
            name='Test Category'
        )
        self.template = PageTemplate.objects.create(
            name='Test Template',
            layout='default',
            template_file='templates/page_templates/default.html',
            created_by=self.user
        )
        self.page = Page.objects.create(
            title='Test Page',
            content='<p>Test content</p>',
            summary='Test summary',
            template=self.template,
            status='draft',
            created_by=self.user,
            updated_by=self.user
        )
        self.page.categories.add(self.category)
    
    def test_page_creation(self):
        """Testa se uma página é criada corretamente"""
        self.assertEqual(self.page.title, 'Test Page')
        self.assertEqual(self.page.slug, 'test-page')
        self.assertEqual(self.page.content, '<p>Test content</p>')
        self.assertEqual(self.page.summary, 'Test summary')
        self.assertEqual(self.page.template, self.template)
        self.assertEqual(self.page.status, 'draft')
        self.assertIsNone(self.page.published_at)
    
    def test_is_published_method(self):
        """Testa o método is_published"""
        # Página em rascunho
        self.assertFalse(self.page.is_published())
        
        # Página publicada
        self.page.status = 'published'
        self.page.published_at = timezone.now()
        self.page.save()
        self.assertTrue(self.page.is_published())
        
        # Página agendada para o futuro
        self.page.status = 'scheduled'
        self.page.scheduled_at = timezone.now() + timedelta(days=1)
        self.page.save()
        self.assertFalse(self.page.is_published())
        
        # Página agendada para o passado (deve ser publicada)
        self.page.scheduled_at = timezone.now() - timedelta(days=1)
        self.page.save()
        self.assertTrue(self.page.is_published())
    
    def test_get_absolute_url(self):
        """Testa o método get_absolute_url"""
        url = self.page.get_absolute_url()
        self.assertIn(self.page.slug, url)
    
    def test_effective_meta_title(self):
        """Testa a propriedade effective_meta_title"""
        # Sem meta_title específico
        self.assertEqual(self.page.effective_meta_title, 'Test Page')
        
        # Com meta_title específico
        self.page.meta_title = 'SEO Title'
        self.assertEqual(self.page.effective_meta_title, 'SEO Title')


class PageVersionTests(TestCase):
    """Testes para o modelo PageVersion"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        self.template = PageTemplate.objects.create(
            name='Test Template',
            layout='default',
            template_file='templates/page_templates/default.html',
            created_by=self.user
        )
        self.page = Page.objects.create(
            title='Test Page',
            content='<p>Original content</p>',
            summary='Original summary',
            template=self.template,
            status='draft',
            created_by=self.user,
            updated_by=self.user
        )
        self.version = PageVersion.objects.create(
            page=self.page,
            title='Test Page',
            content='<p>Original content</p>',
            summary='Original summary',
            version_number=1,
            created_by=self.user,
            status='draft'
        )
    
    def test_version_creation(self):
        """Testa se uma versão de página é criada corretamente"""
        self.assertEqual(self.version.page, self.page)
        self.assertEqual(self.version.title, 'Test Page')
        self.assertEqual(self.version.content, '<p>Original content</p>')
        self.assertEqual(self.version.summary, 'Original summary')
        self.assertEqual(self.version.version_number, 1)
        self.assertEqual(self.version.status, 'draft')
    
    def test_restore_method(self):
        """Testa o método restore"""
        # Altera a página original
        self.page.title = 'Updated Title'
        self.page.content = '<p>Updated content</p>'
        self.page.summary = 'Updated summary'
        self.page.save()
        
        # Restaura a versão anterior
        self.version.restore()
        
        # Recarrega a página do banco de dados
        self.page.refresh_from_db()
        
        # Verifica se os dados foram restaurados
        self.assertEqual(self.page.title, 'Test Page')
        self.assertEqual(self.page.content, '<p>Original content</p>')
        self.assertEqual(self.page.summary, 'Original summary')