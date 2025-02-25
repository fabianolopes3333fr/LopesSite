# Sistema de CMS - Documentação

Este documento fornece uma visão geral do sistema de CMS, explicando sua arquitetura, funcionalidades principais e como estendê-lo para atender a requisitos específicos.

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Sistema de Templates](#sistema-de-templates)
4. [Sistema de Gestão de Páginas](#sistema-de-gestão-de-páginas)
5. [Instalação](#instalação)
6. [Configuração](#configuração)
7. [Uso Básico](#uso-básico)
8. [Recursos Avançados](#recursos-avançados)
9. [Extensão e Personalização](#extensão-e-personalização)
10. [Melhores Práticas](#melhores-práticas)
11. [Solução de Problemas](#solução-de-problemas)
12. [API de Referência](#api-de-referência)

## Visão Geral

O Sistema de CMS é uma solução completa para gerenciamento de conteúdo web construída em Django. Ele fornece uma interface intuitiva para criar, editar e publicar conteúdo sem necessidade de conhecimentos técnicos avançados.

### Principais Modelos

- **Page**: Modelo principal para páginas com hierarquia e metadados.
- **PageCategory**: Categorias para organizar páginas.
- **PageTemplate**: Define templates disponíveis para criar páginas.
- **FieldGroup**: Grupos para organizar campos personalizados.
- **FieldDefinition**: Define campos personalizados disponíveis para um template.
- **PageFieldValue**: Armazena valores de campos personalizados para uma página.
- **PageVersion**: Mantém histórico de versões de páginas.
- **PageGallery**: Galerias de imagens para páginas.
- **PageImage**: Imagens em galerias.
- **PageComment**: Comentários em páginas.
- **PageRevisionRequest**: Solicitações de revisão para publicação.
- **PageNotification**: Notificações sobre atividades em páginas.

### Fluxo de Publicação

```
Rascunho → Revisão → Agendado → Publicado
      ↑                    ↓
      └───────── Arquivado ←
```

## Instalação

### Requisitos

- Python 3.8+
- Django 4.2+
- Banco de dados (PostgreSQL recomendado)
- Pillow para processamento de imagens
- CKEditor para edição de conteúdo
- MPTT para gerenciar hierarquias

### Passos de Instalação

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Adicione os aplicativos ao seu arquivo `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'mptt',
    'ckeditor',
    'ckeditor_uploader',
    'colorfield',
    'your_cms_app.templates',
    'your_cms_app.pages',
]
```

3. Configure o middleware:

```python
MIDDLEWARE = [
    # ...
    'your_cms_app.templates.middleware.TemplateOverrideMiddleware',
    'your_cms_app.templates.middleware.DynamicTemplateLoaderMiddleware',
    'your_cms_app.templates.middleware.LayoutMiddleware',
]
```

4. Execute as migrações:

```bash
python manage.py migrate
```

## Configuração

### Configurações Básicas

Adicione estas configurações ao seu arquivo `settings.py`:

```python
# Configurações para o CKEditor
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Full',
        'height': 300,
        'width': '100%',
    },
}

# Configurações para o sistema de templates
DEFAULT_TEMPLATE = 'default'
TEMPLATE_CACHE_TTL = 3600  # Tempo de cache para templates em segundos

# Configurações para o sistema de páginas
PAGE_CACHE_TTL = 3600  # Tempo de cache para páginas em segundos
PAGE_UPLOAD_PATH = 'pages/'

# Configurações para thumbnails
THUMBNAIL_SIZES = {
    'small': (150, 150),
    'medium': (300, 300),
    'large': (800, 600),
}
```

### Configuração de URLs

Adicione as URLs ao seu arquivo `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path('templates/', include('your_cms_app.templates.urls', namespace='templates')),
    path('pages/', include('your_cms_app.pages.urls', namespace='pages')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]
```

## Uso Básico

### Criação de Páginas

1. Acesse o painel administrativo
2. Navegue até "Páginas" > "Adicionar Página"
3. Selecione um template
4. Preencha os campos básicos (título, slug, conteúdo)
5. Configure os campos SEO e metadados
6. Adicione campos personalizados conforme o template selecionado
7. Salve como rascunho ou publique diretamente

### Gerenciamento de Templates

1. Acesse o painel administrativo
2. Navegue até "Templates" > "Adicionar Template"
3. Define as regiões editáveis e componentes permitidos
4. Configure as áreas de widgets
5. Associe campos personalizados ao template

### Uso de Componentes

1. Edite uma página
2. Na seção de regiões editáveis, clique em "Adicionar Componente"
3. Selecione o tipo de componente desejado
4. Configure os parâmetros do componente
5. Arraste-o para reordenar dentro da região

### Criação de Galerias

1. Edite uma página
2. Na aba "Galerias", clique em "Criar Galeria"
3. Dê um nome e descrição para a galeria
4. Faça upload de imagens
5. Configure os metadados de cada imagem (título, descrição, alt text)

## Recursos Avançados

### Agendamento de Publicação

Para agendar a publicação de uma página:

1. Edite a página
2. Selecione o status "Agendado"
3. Defina a data e hora de publicação
4. Salve a página

O sistema publicará automaticamente a página na data/hora especificada.

### Controle de Versão

Cada vez que uma página é editada, uma nova versão é criada. Para gerenciar versões:

1. Edite uma página
2. Na aba "Versões", visualize o histórico de alterações
3. Clique em "Visualizar" para ver uma versão específica
4. Clique em "Restaurar" para reverter para uma versão anterior

### Workflow de Revisão

Para implementar um fluxo de aprovação:

1. Editor cria/edita uma página
2. Seleciona "Solicitar Revisão"
3. Revisor recebe notificação
4. Revisor aprova ou rejeita a solicitação
5. Se aprovada, a página é publicada automaticamente

### Campos Personalizados

Os campos personalizados permitem estender o modelo de dados para atender às necessidades específicas de cada tipo de página. Tipos de campos disponíveis:

- Texto curto e longo
- Rich text (WYSIWYG)
- Números (inteiros e decimais)
- Data e hora
- Imagens e arquivos
- Seleção simples e múltipla
- Checkboxes e botões de rádio
- Cor
- Código
- JSON
- Relacionamentos com outros objetos

## Extensão e Personalização

### Criação de Novos Componentes

Para criar um novo componente:

1. Crie uma entrada no modelo `ComponentTemplate`
2. Defina o HTML, CSS e JavaScript do componente
3. Configure os parâmetros aceitos pelo componente
4. Adicione-o às regiões dos templates

Exemplo:

```python
from your_cms_app.templates.models import ComponentTemplate

ComponentTemplate.objects.create(
    name='Call to Action',
    slug='cta',
    component_type='custom',
    template_code='<div class="cta-box {{ color_scheme }}"><h3>{{ title }}</h3><p>{{ text }}</p><a href="{{ button_url }}" class="btn btn-{{ button_style }}">{{ button_text }}</a></div>',
    css_code='.cta-box { padding: 20px; border-radius: 5px; }',
    default_context={
        'title': 'Call to Action',
        'text': 'Click the button below',
        'button_text': 'Click Here',
        'button_url': '#',
        'button_style': 'primary',
        'color_scheme': 'bg-light'
    }
)
```

### Criação de Novos Widgets

Similar aos componentes, os widgets podem ser criados para funcionalidades específicas:

```python
from your_cms_app.templates.models import Widget

Widget.objects.create(
    name='Formulário de Contato',
    slug='contact-form',
    widget_type='custom',
    template_code='<form method="post" action="{{ form_action }}">...',
    default_settings={
        'form_action': '/contact/',
        'subject': 'Novo contato do site',
        'recipient_email': 'contact@example.com'
    }
)
```

### Hooks e Eventos

O sistema fornece hooks para estender funcionalidades:

```python
from your_cms_app.pages.signals import page_published, page_updated

@receiver(page_published)
def on_page_published(sender, instance, **kwargs):
    # Lógica a ser executada quando uma página é publicada
    # Por exemplo, enviar notificação, atualizar cache, etc.
    pass

@receiver(page_updated)
def on_page_updated(sender, instance, **kwargs):
    # Lógica a ser executada quando uma página é atualizada
    pass
```

## Melhores Práticas

### Organização de Templates

- Agrupe templates por funcionalidade ou seção do site
- Use categorias para facilitar a navegação
- Mantenha componentes genéricos para reutilização
- Documente parâmetros e uso de cada componente

### Otimização de Desempenho

- Utilize o cache para templates e páginas frequentemente acessados
- Otimize imagens antes do upload
- Prefetche dados relacionados nas consultas
- Use lazy loading para imagens e conteúdo pesado

### SEO

- Sempre preencha metadados (título, descrição, palavras-chave)
- Use URLs amigáveis (slugs significativos)
- Adicione dados estruturados Schema.org
- Configure corretamente as tags Open Graph para compartilhamento

### Segurança

- Valide todos os dados de entrada, especialmente em campos personalizados
- Sanitize conteúdo HTML para evitar XSS
- Implemente controle de acesso granular
- Audite todas as alterações em páginas e templates

## Solução de Problemas

### Problemas Comuns

1. **Templates não aparecem**: Verifique se estão marcados como ativos e se pertencem à categoria correta.
2. **Componentes não renderizam**: Verifique se o código do template está correto e se o contexto está sendo passado corretamente.
3. **Campos personalizados não aparecem**: Verifique se o grupo de campos está associado corretamente ao template.
4. **Problemas com upload de imagens**: Verifique as permissões de diretório e as configurações do Pillow.

### Logs

O sistema registra eventos importantes em logs específicos:

```python
import logging
logger = logging.getLogger('your_cms_app.pages')
```

Consulte os logs para diagnóstico de problemas:

```
tail -f logs/cms_debug.log
```

## API de Referência

### API REST

O sistema fornece uma API REST para integração com outros sistemas:

- `/api/pages/` - Lista todas as páginas
- `/api/pages/<id>/` - Detalhes de uma página específica
- `/api/templates/` - Lista todos os templates
- `/api/components/` - Lista todos os componentes

### Programação

```python
# Obter uma página pelo slug
from your_cms_app.pages.models import Page
page = Page.objects.get(slug='pagina-exemplo')

# Renderizar uma região
from your_cms_app.templates.utils import render_region
html = render_region('content', 'home_page')

# Criar uma nova página
from your_cms_app.pages.models import Page, PageTemplate
template = PageTemplate.objects.get(slug='article')
page = Page.objects.create(
    title='Título da Página',
    slug='titulo-da-pagina',
    template=template,
    status='draft',
    created_by=request.user
)
```

### Template Tags

```html
{% load cms_tags %}

{# Renderiza uma região com componentes #}
{% render_region 'content' %}

{# Renderiza um menu com base na hierarquia de páginas #}
{% render_menu 'main_menu' %}

{# Exibe um breadcrumb #}
{% breadcrumb %}

{# Lista páginas filhas #}
{% child_pages page %}

{# Exibe formulário de comentários #}
{% comments_form page %}
```

## Conclusão

Este sistema de CMS fornece uma base sólida para criar sites dinâmicos com interface amigável para os administradores. Sua arquitetura modular permite fácil extensão e personalização para atender às necessidades específicas de cada projeto.

Para suporte e contribuições, acesse o repositório do projeto no GitHub ou entre em contato com a equipe de desenvolvimento.

---

© 2025 Your Company Características

- **Sistema de Templates Flexível**: Templates reutilizáveis e componentes que podem ser combinados para criar layouts personalizados.
- **Gestão Hierárquica de Páginas**: Estrutura de páginas em árvore com controle de versão.
- **Campos Personalizáveis**: Diferentes tipos de campos podem ser definidos para cada template.
- **Sistema de Workflow**: Suporte para rascunhos, revisão, agendamento e publicação.
- **SEO Integrado**: Ferramentas para otimização de metatags, URLs amigáveis e integração com Schema.org.
- **Gestão de Mídia**: Organização de imagens em galerias com suporte para upload em massa.
- **Sistema de Comentários**: Comentários com moderação e notificações.
- **Sistema de Notificações**: Alertas sobre atividades relevantes.

## Arquitetura

O sistema é dividido em dois módulos principais:

1. **Sistema de Templates**: Define a estrutura visual e os componentes reutilizáveis.
2. **Sistema de Gestão de Páginas**: Gerencia o conteúdo, controle de versão e metadados.

### Diagrama de Componentes

```
┌─────────────────────────────┐
│       Interface Admin       │
└───────────────┬─────────────┘
                │
┌───────────────┴─────────────┐
│    Middleware de Templates  │
└───────────────┬─────────────┘
                │
┌─────────┬─────┴─────┬───────┐
│Templates│  Páginas  │ Mídia │
└─────────┴───────────┴───────┘
```

## Sistema de Templates

O Sistema de Templates fornece a estrutura visual do site, permitindo a definição de layouts, componentes e widgets reutilizáveis.

### Principais Modelos

- **BaseTemplate**: Modelo base para todos os templates.
- **TemplateCategory**: Categorias para organizar templates.
- **TemplateType**: Define o tipo de template (página, seção, cabeçalho, etc.).
- **DjangoTemplate**: Representa um arquivo de template físico.
- **TemplateRegion**: Define regiões editáveis dentro de um template.
- **LayoutTemplate**: Layouts completos combinando diferentes templates.
- **ComponentTemplate**: Componentes reutilizáveis (cards, sliders, etc.).
- **ComponentInstance**: Instância de um componente em uma região.
- **Widget**: Widgets reutilizáveis (texto, menu, busca, etc.).
- **WidgetInstance**: Instância de um widget em uma área.

### Exemplo de Uso de Template Tags

```html
{% load template_tags %}

<!-- Renderiza uma região com componentes -->
{% render_region 'content' 'home_page' %}

<!-- Renderiza uma área de widgets -->
{% render_widget_area 'sidebar' 'home_page' %}

<!-- Renderiza um componente específico -->
{% component 'alert' type='success' message='Operação realizada com sucesso!' %}
```

## Sistema de Gestão de Páginas

O Sistema de Gestão de Páginas gerencia o conteúdo, metadados e controle de versão das páginas.

### Principais