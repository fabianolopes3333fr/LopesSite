from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from ..models import (
    PageCategory, PageTemplate, Page, PageVersion
)

class PageListViewTests(TestCase):
    """Testes para a view PageListView"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        
        # Cria template para os testes
        self.template = PageTemplate.objects.create(
            name='Test Template',
            layout='default',
            template_file='templates/page_templates/default.html',
            created_by=self.user
        )
        
        # Cria categoria para os testes
        self.category = PageCategory.objects.create(
            name='Test Category'
        )
        
        # Cria páginas para testes
        for i in range(5):
            page = Page.objects.create(
                title=f'Test Page {i}',
                summary=f'Summary for test page {i}',
                template=self.template,
                status='published',
                created_by=self.user,
                updated_by=self.user
            )
            page.categories.add(self.category)
    
    def test_page_list_view(self):
        """Testa a visualização da lista de páginas"""
        url = reverse('pages:page_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('pages', response.context)
        self.assertEqual(len(response.context['pages']), 5)
        
        # Verifica o conteúdo HTML
        for i in range(5):
            self.assertContains(response, f'Test Page {i}')
    
    def test_category_filter(self):
        """Testa o filtro por categoria"""
        url = reverse('pages:page_category', args=[self.category.slug])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('pages', response.context)
        self.assertEqual(len(response.context['pages']), 5)
        self.assertIn('current_category', response.context)
        self.assertEqual(response.context['current_category'], self.category)


class PageDetailViewTests(TestCase):
    """Testes para a view PageDetailView"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        
        # Cria template para os testes
        self.template = PageTemplate.objects.create(
            name='Test Template',
            layout='default',
            template_file='templates/page_templates/default.html',
            created_by=self.user
        )
        
        # Cria uma página pública
        self.public_page = Page.objects.create(
            title='Public Page',
            content='<p>Public content</p>',
            summary='Public summary',
            template=self.template,
            status='published',
            visibility='public',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Cria uma página privada
        self.private_page = Page.objects.create(
            title='Private Page',
            content='<p>Private content</p>',
            summary='Private summary',
            template=self.template,
            status='published',
            visibility='private',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Cria uma página protegida por senha
        self.password_page = Page.objects.create(
            title='Password Page',
            content='<p>Password protected content</p>',
            summary='Password summary',
            template=self.template,
            status='published',
            visibility='password',
            password='testpassword',
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_public_page_view(self):
        """Testa a visualização de uma página pública"""
        url = reverse('pages:page_detail', args=[self.public_page.slug])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page', response.context)
        self.assertEqual(response.context['page'], self.public_page)
        self.assertContains(response, 'Public Page')
        self.assertContains(response, '<p>Public content</p>')
    
    def test_private_page_view(self):
        """Testa a visualização de uma página privada"""
        url = reverse('pages:page_detail', args=[self.private_page.slug])
        response = self.client.get(url)
        
        # Sem login, deve retornar 404
        self.assertEqual(response.status_code, 404)
        
        # Adiciona permissão para visualizar página
        content_type = ContentType.objects.get_for_model(Page)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='view_page'
        )
        self.user.user_permissions.add(permission)
        
        # Faz login e tenta novamente
        self.client.login(username='testuser', password='password')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Private Page')
    
    def test_password_protected_page(self):
        """Testa a visualização de uma página protegida por senha"""
        url = reverse('pages:page_detail', args=[self.password_page.slug])
        
        # Primeira tentativa sem senha
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('password_required', response.context)
        self.assertTrue(response.context['password_required'])
        
        # Envia senha incorreta
        response = self.client.post(url, {'password': 'wrongpassword'})
        self.assertContains(response, 'Senha incorreta')
        
        # Envia senha correta
        response = self.client.post(url, {'password': 'testpassword'})
        self.assertRedirects(response, url)
        
        # Agora deve conseguir acessar a página
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('password_required', response.context)
        self.assertContains(response, 'Password Page')


class PageCreateViewTests(TestCase):
    """Testes para a view PageCreateView"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='password'
        )
        
        # Adiciona permissão para criar páginas
        content_type = ContentType.objects.get_for_model(Page)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='add_page'
        )
        self.user.user_permissions.add(permission)
        
        # Cria template para os testes
        self.template = PageTemplate.objects.create(
            name='Test Template',
            layout='default',
            template_file='templates/page_templates/default.html',
            created_by=self.user
        )
    
    def test_login_required(self):
        """Testa se a view requer login"""
        url = reverse('pages:page_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirecionamento para login
    
    def test_page_creation(self):
        """Testa a criação de uma página"""
        self.client.login(username='testuser', password='password')
        url = reverse('pages:page_create')
        
        # GET request - deve mostrar o formulário
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        
        # POST request - cria a página
        data = {
            'title': 'New Test Page',
            'slug': 'new-test-page',
            'summary': 'New test summary',
            'content': '<p>New test content</p>',
            'template': self.template.id,
            'status': 'draft'
        }
        response = self.client.post(url, data)
        
        # Verifica se a página foi criada
        self.assertEqual(Page.objects.count(), 1)
        page = Page.objects.first()
        self.assertEqual(page.title, 'New Test Page')
        self.assertEqual(page.created_by, self.user)
        
        # Verifica redirecionamento para página de edição
        self.assertRedirects(response, reverse('pages:page_update', args=[page.pk]))