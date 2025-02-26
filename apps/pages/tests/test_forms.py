from django.test import TestCase
from django.contrib.auth.models import User
from ..models import (
    PageCategory, PageTemplate, FieldGroup, FieldDefinition, 
    Page, PageComment
)
from ..forms import (
    PageBaseForm, PageCommentForm
)

class PageBaseFormTests(TestCase):
    """Testes para o formulário PageBaseForm"""
    
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
        
        # Cria grupos de campos e definições de campos
        self.field_group = FieldGroup.objects.create(
            name='Basic Fields',
            slug='basic-fields',
            template=self.template
        )
        
        self.text_field = FieldDefinition.objects.create(
            name='Subtitle',
            slug='subtitle',
            field_type='text',
            is_required=True,
            group=self.field_group,
            order=0
        )
        
        self.textarea_field = FieldDefinition.objects.create(
            name='Extra Content',
            slug='extra-content',
            field_type='textarea',
            is_required=False,
            group=self.field_group,
            order=1
        )
    
    def test_form_initialization(self):
        """Testa a inicialização do formulário"""
        # Testa formulário para nova página
        form = PageBaseForm(user=self.user)
        self.assertIn('title', form.fields)
        self.assertIn('slug', form.fields)
        self.assertIn('template', form.fields)
        self.assertIn('status', form.fields)
        
        # Testa inicialização com instância
        page = Page.objects.create(
            title='Test Page',
            template=self.template,
            status='draft',
            created_by=self.user,
            updated_by=self.user
        )
        form = PageBaseForm(instance=page, user=self.user)
        self.assertEqual(form.instance, page)
    
    def test_custom_fields_loading(self):
        """Testa o carregamento de campos personalizados"""
        # Cria uma página
        page = Page.objects.create(
            title='Test Page',
            template=self.template,
            status='draft',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Inicializa o formulário com a página existente
        form = PageBaseForm(instance=page, user=self.user)
        
        # Verifica se os campos personalizados foram carregados
        self.assertTrue(hasattr(form, 'custom_fields'))
        self.assertEqual(len(form.custom_fields), 2)
        
        # Verifica se os campos estão presentes no formulário
        self.assertIn(f'custom_{self.text_field.id}', form.fields)
        self.assertIn(f'custom_{self.textarea_field.id}', form.fields)
    
    def test_form_validation(self):
        """Testa a validação do formulário"""
        data = {
            'title': 'Test Page',
            'slug': 'test-page',
            'template': self.template.id,
            'status': 'draft',
            f'custom_{self.text_field.id}': 'Test Subtitle',  # Campo obrigatório
            # f'custom_{self.textarea_field.id}' não é fornecido, mas é opcional
        }
        
        form = PageBaseForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())
        
        # Teste sem campo obrigatório
        data_invalid = data.copy()
        data_invalid.pop(f'custom_{self.text_field.id}')
        form = PageBaseForm(data=data_invalid, user=self.user)
        self.assertFalse(form.is_valid())
    
    def test_save_method(self):
        """Testa o método save do formulário"""
        data = {
            'title': 'New Test Page',
            'slug': 'new-test-page',
            'template': self.template.id,
            'status': 'draft',
            f'custom_{self.text_field.id}': 'Test Subtitle',
            f'custom_{self.textarea_field.id}': 'Extra content text',
        }
        
        form = PageBaseForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())
        
        # Salva a página
        page = form.save()
        
        # Verifica se a página foi criada corretamente
        self.assertEqual(page.title, 'New Test Page')
        self.assertEqual(page.slug, 'new-test-page')
        self.assertEqual(page.status, 'draft')
        self.assertEqual(page.created_by, self.user)
        
        # Verifica se os campos personalizados foram salvos
        self.assertEqual(page.field_values.count(), 2)
        subtitle_value = page.field_values.get(field=self.text_field)
        self.assertEqual(subtitle_value.value, 'Test Subtitle')
        
        extra_content_value = page.field_values.get(field=self.textarea_field)
        self.assertEqual(extra_content_value.value, 'Extra content text')


class PageCommentFormTests(TestCase):
    """Testes para o formulário PageCommentForm"""
    
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
            template=self.template,
            status='published',
            created_by=self.user,
            updated_by=self.user,
            enable_comments=True
        )
    
    def test_form_initialization(self):
        """Testa a inicialização do formulário de comentários"""
        # Para usuário anônimo
        form = PageCommentForm(page=self.page)
        self.assertIn('author_name', form.fields)
        self.assertIn('author_email', form.fields)
        self.assertIn('comment', form.fields)
        
        # Para usuário autenticado
        form = PageCommentForm(page=self.page, user=self.user)
        self.assertEqual(form.fields['author_name'].initial, 'testuser')
        self.assertEqual(form.fields['author_email'].initial, 'test@example.com')
        
        # Campos devem ser readonly para usuários autenticados
        self.assertTrue(form.fields['author_name'].widget.attrs.get('readonly'))
        self.assertTrue(form.fields['author_email'].widget.attrs.get('readonly'))
    
    def test_form_validation(self):
        """Testa a validação do formulário de comentários"""
        # Dados válidos
        data = {
            'author_name': 'Test Commenter',
            'author_email': 'commenter@example.com',
            'author_url': 'http://example.com',
            'comment': 'This is a test comment.'
        }
        
        form = PageCommentForm(data=data, page=self.page)
        self.assertTrue(form.is_valid())
        
        # Dados inválidos (sem nome do autor)
        invalid_data = data.copy()
        invalid_data.pop('author_name')
        form = PageCommentForm(data=invalid_data, page=self.page)
        self.assertFalse(form.is_valid())
        self.assertIn('author_name', form.errors)
    
    def test_save_method(self):
        """Testa o método save do formulário de comentários"""
        data = {
            'author_name': 'Test Commenter',
            'author_email': 'commenter@example.com',
            'author_url': 'http://example.com',
            'comment': 'This is a test comment.'
        }
        
        form = PageCommentForm(data=data, page=self.page)
        self.assertTrue(form.is_valid())
        
        # Testa save para usuário anônimo
        comment = form.save()
        self.assertEqual(comment.page, self.page)
        self.assertEqual(comment.author_name, 'Test Commenter')
        self.assertEqual(comment.comment, 'This is a test comment.')
        self.assertFalse(comment.is_approved)  # Comentários anônimos precisam de aprovação
        
        # Testa save para usuário staff (aprovação automática)
        self.user.is_staff = True
        self.user.save()
        form = PageCommentForm(data=data, page=self.page, user=self.user)
        self.assertTrue(form.is_valid())
        comment = form.save()
        self.assertTrue(comment.is_approved)  # Comentários de staff são aprovados automaticamente