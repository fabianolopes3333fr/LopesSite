# LopesSite

# Briefing para Desenvolvimento de CONFIG Personalizado em Django

# Prompt para Claude VSCode - Implementação de CMS Personalizado

Olá Claude, estou desenvolvendo um sistema completo de gerenciamento  em Django e preciso implementar um sistema de CMS CONFIG personalizado que permita ao cliente editar todo o conteúdo e estilo do site através de um painel administrativo. Por favor, me ajude com esta implementação seguindo estas especificações:

## Visão Geral do Projeto
- **Nome do Projeto**: CONFIG Personalizado para Serviços de Pintura
- **Objetivo Principal**: Desenvolver uma plataforma que permita ao cliente gerenciar todo o conteúdo e estilo do site de forma intuitiva
- **Público-alvo**: Administradores do site sem conhecimentos técnicos avançados
- **Prazo Estimado**: [Inserir prazo]
- **Orçamento**: [Inserir orçamento se aplicável]

## Stack Tecnológico
### Backend
- **Framework**: Django 4.2+
- **Banco de Dados**: PostgreSQL 14+
- **Cache**: Redis 6+
- **Task Queue**: Celery (para processamento assíncrono)
- **Search Engine**: Elasticsearch (opcional)

### Frontend
- **Framework Base**: Django Templates + JavaScript
- **Bibliotecas JS**:
  - jQuery 3.6+
  - Sortable.js 1.14+
  - Alpine.js (para interatividade leve)
  - htmx (para atualizações parciais sem recarregar a página)

### Editores e UI Components
- **Editor WYSIWYG**: CKEditor 5
- **Seletor de Cores**: Spectrum.js ou ColorPicker
- **Gerenciador de Arquivos**: Django-FileBrowser ou implementação personalizada
- **Grid System**: Bootstrap Grid ou TailwindCSS

### Storage
- **Mídia Local**: Django Media
- **Mídia em Nuvem**: AWS S3 ou similar
- **CDN**: Cloudflare, AWS CloudFront ou similar

### DevOps
- **Controle de Versão**: Git (GitHub/GitLab)
- **CI/CD**: GitHub Actions, GitLab CI ou similar
- **Deployment**: Docker + Docker Compose
- **Monitoramento**: Sentry para erros, Prometheus + Grafana para métricas

## Arquitetura do Sistema
- **Padrão MVC/MTV**: Seguir o padrão Django (Model-Template-View)
- **Modularidade**: Dividir em apps Django conforme funcionalidade
- **API**: Endpoints REST para funcionalidades dinâmicas
- **Microserviços**: Considerar isolar funcionalidades complexas (como processamento de imagem) em serviços separados

## Funcionalidades Detalhadas

### 1. Sistema de Gestão de Páginas
- **Modelo de Dados**:
  - Hierarquia de páginas (parent/child)
  - Metadados completos (SEO, Open Graph, Schema.org)
  - Versionamento de conteúdo
  - Sistema de status (rascunho, revisão, agendado, publicado, arquivado)
  - Permalinks customizáveis e redirecionamentos automáticos
- **Campos Personalizáveis**:
  - Tipos de campo (texto, rich text, imagem, galeria, vídeo, arquivo, mapa, etc.)
  - Validação por tipo de campo
  - Grupos de campos para organização

### 2. Sistema de Templates
- **Arquitetura**:
  - Templates base (header, footer, sidebar, content, main, section)
  - Blocos de conteúdo dinâmicos
  - Componentes reutilizáveis (cards, sliders, galerias, Accordion, Alerts, Badge, Breadcrumb, Buttons, Button, group,
Carousel, Close button, Collapse, Dropdowns, List group, Modal, Navbar, Navs & tabs, Offcanvas, Pagination, Placeholders,
Popovers, Progress, Scrollspy, Spinners, Toasts, Tooltips)
  - Áreas de widgets
- **Implementação**:
  - Sistema de herança de templates Django
  - Blocos editáveis por região
  - Variantes de layout por tipo de página
  - Sistema para override de templates por usuários não-técnicos
  
### Implementacao 

# Sistema de Templates para Django CMS

Este módulo implementa um sistema completo de templates para o Django CMS, permitindo aos administradores criar, personalizar e gerenciar layouts, componentes e widgets de forma flexível e intuitiva.

## Características

### Arquitetura de Templates
- **Templates Base**: Header, footer, sidebar, content, main, section
- **Blocos de Conteúdo Dinâmicos**: Regiões editáveis dentro dos templates
- **Componentes Reutilizáveis**: Cards, sliders, galerias, accordions, etc.
- **Áreas de Widgets**: Regiões especiais para adição de widgets

### Sistema de Herança
- **Herança de Templates Django**: Aproveita o sistema nativo do Django
- **Blocos Editáveis por Região**: Define áreas específicas que podem ser personalizadas
- **Variantes de Layout**: Diferentes layouts para diferentes tipos de página
- **Override de Templates**: Permite que usuários não-técnicos personalizem templates

## Modelos de Dados

### Templates
- `TemplateCategory`: Categorias para organizar os templates
- `TemplateType`: Tipos de templates (página, seção, header, footer, etc.)
- `DjangoTemplate`: Representa um template Django físico
- `TemplateRegion`: Regiões editáveis dentro de um template
- `LayoutTemplate`: Layouts completos combinando diferentes templates

### Componentes
- `ComponentTemplate`: Componentes reutilizáveis (card, slider, etc.)
- `ComponentInstance`: Instância de um componente em uma região

### Widgets
- `WidgetArea`: Áreas destinadas a conter widgets
- `Widget`: Widgets reutilizáveis (texto, menu, busca, etc.)
- `WidgetInstance`: Instância de um widget em uma área de widgets

## Uso

### Renderização de Templates

```html
{% load template_tags %}

<!-- Renderiza uma região com componentes -->
{% render_region 'content' 'home_page' %}

<!-- Renderiza uma área de widgets -->
{% render_widget_area 'sidebar' 'home_page' %}

<!-- Renderiza um componente específico -->
{% component 'alert' type='success' message='Operação realizada com sucesso!' %}

<!-- Inclui um componente com contexto adicional -->
{% include_component 'card' title='Meu Card' content='Conteúdo do card' %}

<!-- Renderiza um layout completo -->
{% render_layout 'default' %}
```

### Modo de Edição

Em modo de edição, regiões e áreas de widgets podem ser editadas:

```html
{% if is_edit_mode and user.is_staff %}
    {% editable_region 'content' %}
    {% editable_widget_area 'sidebar' %}
{% else %}
    {% render_region 'content' %}
    {% render_widget_area 'sidebar' %}
{% endif %}
```

## APIs

O sistema fornece APIs para:

1. Adicionar/remover componentes às regiões
2. Reordenar componentes dentro de regiões
3. Adicionar/remover widgets às áreas
4. Reordenar widgets dentro de áreas
5. Atualizar configurações de componentes e widgets

## Interface do Administrador

- **Biblioteca de Componentes**: Visualização e gestão de todos os componentes disponíveis
- **Editor de Regiões**: Interface para editar o conteúdo das regiões
- **Editor de Áreas de Widget**: Interface para gerenciar os widgets nas áreas
- **Gerenciador de Layouts**: Interface para criar e personalizar layouts completos

## Editor Visual

O sistema inclui um editor visual WYSIWYG que permite:

- Drag-and-drop de componentes e widgets
- Edição inline de conteúdo
- Visualização em tempo real das alterações
- Configuração visual de estilos e comportamentos

## Componentes Incluídos

O sistema vem com vários componentes pré-configurados:

1. **Card**: Para exibir conteúdo em formato de cartão
2. **Carousel/Slider**: Para exibir múltiplas imagens em slideshow
3. **Accordion**: Para conteúdo expansível/retrátil
4. **Alert**: Para mensagens de alerta e notificação
5. **Tabs**: Para organizar conteúdo em abas
6. **Modal**: Para janelas pop-up
7. **Progress**: Barras de progresso
8. **Gallery**: Para exibir galerias de imagens
9. **Button Group**: Grupos de botões relacionados
10. **Breadcrumb**: Para navegação hierárquica

## Widgets Incluídos

O sistema inclui widgets comuns:

1. **Text/HTML**: Para conteúdo de texto livre
2. **Menu**: Para exibir menus de navegação
3. **Recent Posts**: Lista de posts recentes
4. **Categories**: Lista de categorias
5. **Tags**: Nuvem de tags
6. **Search**: Campo de busca
7. **Login**: Formulário de login
8. **Social Media**: Links para redes sociais
9. **Contact**: Informações de contato
10. **Media**: Imagens, vídeos, mapas, etc.

## Instalação

1. Adicione `'your_cms_app.templates'` ao `INSTALLED_APPS` no `settings.py`
2. Execute as migrações: `python manage.py migrate your_cms_app.templates`
3. Colete os arquivos estáticos: `python manage.py collectstatic`
4. Adicione os URLs ao arquivo principal de URLs:

```python
urlpatterns = [
    # Outras URLs
    path('templates/', include('your_cms_app.templates.urls', namespace='templates')),
]
```

5. Adicione os middlewares necessários:

```python
MIDDLEWARE = [
    # Outros middlewares
    'your_cms_app.templates.middleware.TemplateOverrideMiddleware',
    'your_cms_app.templates.middleware.DynamicTemplateLoaderMiddleware',
    'your_cms_app.templates.middleware.LayoutMiddleware',
]
```

## Personalização

### Estendendo Componentes

Para criar novos componentes:

1. Crie uma entrada no banco de dados usando o admin ou via código:

```python
from your_cms_app.templates.models import ComponentTemplate

component = ComponentTemplate.objects.create(
    name='Meu Componente',
    slug='meu-componente',
    component_type='custom',
    template_code='<div class="meu-componente">{{ content }}</div>',
    default_context={'content': 'Conteúdo padrão'}
)
```

### Estendendo Widgets

De forma similar, para criar novos widgets:

```python
from your_cms_app.templates.models import Widget

widget = Widget.objects.create(
    name='Meu Widget',
    slug='meu-widget',
    widget_type='custom',
    template_code='<div class="meu-widget">{{ content }}</div>',
    default_settings={'content': 'Conteúdo padrão'}
)
```

## Considerações de Performance

- O sistema utiliza cache para templates, componentes e widgets
- Invalidação seletiva de cache quando alterações são feitas
- Lazy loading de componentes e widgets quando apropriado
- Minificação de CSS e JS específicos de componentes

## Requisitos

- Django 4.2+
- jQuery 3.6+ (para a interface de editor)
- Bootstrap 5+ (para os componentes padrão)
- CodeMirror (para editor de código)
- Sortable.js (para drag-and-drop)

## Licença

MIT

### 3. Editor Visual
- **Interface**:
  - Editor WYSIWYG completo (CKEditor ou TinyMCE)
  - Modo de edição inline (edição no local)
  - Drag-and-drop para ordenar elementos
  - Biblioteca de mídia integrada
- **Recursos Avançados**:
  - Componentes customizados (shortcodes)
  - Preview em múltiplos dispositivos
  - Histórico de alterações com diff visual
  - Colaboração em tempo real (opcional)
  - Rollback para versões anteriores

### 4. Personalização de Estilos
- **Sistema de Temas**:
  - Temas base com variantes
  - Variáveis CSS customizáveis (cores, fontes, espaçamentos)
  - Override de CSS por página ou seção
- **Ferramentas de Edição**:
  - Painel visual para customização
  - Preview em tempo real
  - Export/import de configurações
  - Presets salvos para reutilização

### 5. Gestão de Mídia
- **Funcionalidades Básicas**:
  - Upload múltiplo
  - Organização em pastas e coleções
  - Metadados e tags
  - Versionamento
- **Processamento Automático**:
  - Resize adaptativo para diferentes dispositivos
  - Compressão inteligente
  - Conversão de formatos (WebP, AVIF)
  - Extração de cores dominantes
  - Geração de thumbnails
- **Recursos Avançados**:
  - Edição básica de imagem (crop, rotate, filters)
  - Reconhecimento de conteúdo via ML (opcional)
  - CDN integration
  - Lazy loading automático

### 6. Sistema de Menus
- **Estrutura**:
  - Menus hierárquicos (MPTT)
  - Múltiplos menus por site
  - Drag-and-drop para organização
- **Tipos de Itens**:
  - Links para páginas internas
  - Links externos
  - Arquivos para download
  - Dropdowns e mega menus
  - Widgets customizados
- **Personalização**:
  - Ícones por item
  - Classes CSS customizáveis
  - Condições de exibição (device, user role, etc.)

### 7. Cache e Performance
- **Estratégias de Cache**:
  - Cache por página
  - Cache por fragment/componente
  - Cache por usuário/grupo
  - Invalidação inteligente baseada em dependências
- **Otimizações Frontend**:
  - Bundling e minificação de CSS/JS
  - Critical CSS automático
  - Lazy loading de imagens e componentes
  - Preload de recursos críticos
- **Monitoramento**:
  - Métricas de performance
  - Web Vitals tracking
  - Alertas de degradação

### 8. SEO Avançado
- **Metadados**:
  - Title, description, keywords editáveis
  - Open Graph e Twitter Cards
  - Schema.org markup
- **Ferramentas de Análise**:
  - Análise de conteúdo on-page
  - Sugestões de melhorias
  - Verificação de links quebrados
  - Sitemap.xml dinâmico
  - Integração com Google Search Console (opcional)

### 9. Internacionalização
- **Funcionalidades Multilíngue**:
  - Tradução de conteúdo via interface
  - Detecção automática de idioma
  - Alternância entre idiomas
  - URLs específicas por idioma
- **Localização**:
  - Formatos de data/hora/moeda
  - Configurações de fuso horário
  - Tradução de UI

### 10. Analytics e Relatórios
- **Integração**:
  - Google Analytics
  - Tag Manager
  - Matomo/Piwik
  - Custom analytics
- **Dashboard**:
  - Métricas principais
  - Relatórios customizáveis
  - Exportação de dados
  - Alertas e notificações

### 11. Formulários Dinâmicos
- **Construtor de Formulários**:
  - Interface drag-and-drop
  - Tipos de campo customizáveis
  - Validação por campo
  - Lógica condicional
- **Gerenciamento**:
  - Armazenamento de submissões
  - Notificações por email
  - Export de dados (CSV, Excel)
  - Integração com CRM/Email marketing

### 12. API RESTful
- **Endpoints**:
  - CRUD para todos os modelos principais
  - Autenticação via token/JWT
  - Rate limiting
  - Documentação automática (Swagger/OpenAPI)
- **Webhooks**:
  - Eventos customizáveis
  - Retry mechanism
  - Logs de eventos

### 13. Sistema de Permissões
- **Níveis de Acesso**:
  - Super Admin: acesso completo
  - Admin de Conteúdo: gerencia páginas e mídia
  - Editor: edita conteúdo existente
  - Designer: personaliza estilos
  - Visualizador: acesso somente leitura
- **Permissões Granulares**:
  - Por app/módulo
  - Por tipo de conteúdo
  - Por instância de objeto
  - Por ação (criar, ler, atualizar, deletar)
- **Features**:
  - Grupos de permissões
  - Herança de permissões
  - Log de atividades por usuário

### 14. Workflows de Aprovação
- **Processo Editorial**:
  - Submissão para revisão
  - Ciclo de aprovação multi-nível
  - Comentários e anotações
  - Publicação agendada
- **Notificações**:
  - Email, in-app, Slack/Teams
  - Lembretes automáticos
  - Escalação por inatividade

### 15. Segurança
- **Proteções**:
  - CSRF, XSS, SQL Injection
  - Rate limiting
  - Proteção contra força bruta
  - Sanitização de HTML
- **Políticas**:
  - Senha forte
  - 2FA (opcional)
  - Sessões seguras
  - Auditoria de ações sensíveis

### 16. Backups e Disaster Recovery
- **Estratégia de Backup**:
  - Backup completo diário
  - Backup incremental a cada hora
  - Retenção configurável
- **Disaster Recovery**:
  - Procedimento documentado
  - Testes periódicos
  - Ambiente de staging para validação

### 17. Acessibilidade
- **Conformidade**:
  - WCAG 2.1 AA
  - Testes automáticos
  - Audit trail
- **Features**:
  - Alertas de problemas no editor
  - Sugestões de melhoria
  - Verificação de contraste

### 18. Integrações
- **Serviços de Terceiros**:
  - Social media
  - Email marketing
  - CRM
  - ERP
  - Ferramentas de chat/suporte
- **Método de Integração**:
  - API
  - Webhooks
  - Plugins/extensões

### 19. Extensibilidade
- **Sistema de Plugins**:
  - API para extensões
  - Hooks e filters
  - Marketplace interno (opcional)
- **Customização**:
  - Override de templates
  - Injeção de CSS/JS
  - Settings configuráveis

### 20. Mobile Optimization
- **Responsividade**:
  - Design adaptativo
  - Preview por dispositivo
  - Touch-friendly UI
- **PWA Features** (opcional):
  - Service workers
  - Offline mode
  - Add to home screen

## Requisitos Técnicos

### Dependências Django
```python
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    
    # CMS core
    'your_cms_app.core',
    'your_cms_app.pages',
    'your_cms_app.media',
    'your_cms_app.templates',
    'your_cms_app.styles',
    'your_cms_app.menus',
    'your_cms_app.forms',
    'your_cms_app.seo',
    
    # Third-party
    'ckeditor',
    'ckeditor_uploader',
    'colorfield',
    'mptt',
    'rest_framework',
    'sorl.thumbnail',
    'django_cleanup',
    'compressor',
    'webpack_loader',
    'taggit',
    'django_celery_results',
    'django_celery_beat',
    'import_export',
    'crispy_forms',
    'allauth',
    'allauth.account',
]
```

### Estrutura do Projeto
```
your_cms_project/
├── config/                   # Configurações do projeto
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── prod.py
│   │   └── test.py
│   ├── urls.py
│   └── wsgi.py
├── your_cms_app/             # Módulos do CMS
│   ├── core/                 # Funcionalidades centrais
│   ├── pages/                # Sistema de páginas
│   ├── media/                # Gestão de mídia
│   ├── templates/            # Sistema de templates
│   ├── styles/               # Personalização de estilos
│   ├── menus/                # Sistema de menus
│   ├── forms/                # Formulários dinâmicos
│   └── seo/                  # Ferramentas de SEO
├── static/                   # Arquivos estáticos
│   ├── css/
│   ├── js/
│   ├── admin/
│   └── fonts/
├── media/                    # Uploads de usuários
├── templates/                # Templates do projeto
│   ├── base.html
│   ├── components/
│   └── pages/
├── docs/                     # Documentação
├── tests/                    # Testes
├── utils/                    # Utilitários
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

### Estratégia de Testes
- **Testes Unitários**:
  - Cobertura mínima: 80%
  - Testes para models, forms, views, templatetags
- **Testes de Integração**:
  - Fluxos de trabalho completos
  - API endpoints
- **Testes de UI**:
  - Selenium ou Cypress
  - Cenários de uso principais
- **Testes de Performance**:
  - Load testing (JMeter)
  - Time to first byte
  - Web Vitals
- **Testes de Segurança**:
  - OWASP top 10
  - Penetration testing

### Estratégia de Deployment
- **Ambientes**:
  - Desenvolvimento
  - Staging
  - Produção
- **Processo**:
  - CI/CD pipeline
  - Testes automatizados
  - Deploy atômico
  - Rollback automático em falha

## Documentação

### Documentação Técnica
- **Arquitetura do Sistema**
- **API Reference**
- **Guia de Desenvolvimento**
- **Guia de Contribuição**
- **Testes e Qualidade de Código**

### Documentação de Usuário
- **Manual do Administrador**
- **Guia de Uso para Editores**
- **Guia de Customização de Estilos**
- **Tutoriais em Vídeo**
- **FAQ**

### Documentação de Operação
- **Guia de Instalação**
- **Guia de Upgrade**
- **Monitoramento e Alertas**
- **Backup e Recuperação**
- **Troubleshooting**

## Plano de Desenvolvimento

### Fase 1: Fundação
- Setup do projeto e infraestrutura
- Implementação dos modelos core
- Sistema básico de administração
- Autenticação e autorização

### Fase 2: Funcionalidades Core
- Sistema de páginas
- Editor visual
- Gestão de mídia
- Menus básicos
- Templates simples

### Fase 3: Personalização
- Sistema de estilos
- Templates avançados
- Componentes reutilizáveis
- Formulários dinâmicos

### Fase 4: Performance e SEO
- Implementação de cache
- Otimizações de performance
- Ferramentas de SEO
- Otimização de mídia

### Fase 5: Features Avançadas
- Workflows de aprovação
- Sistema de relatórios
- Internacionalização
- API REST

### Fase 6: Finalização
- Testes abrangentes
- Documentação completa
- Treinamento de usuários
- Lançamento

## Critérios de Aceitação

### Qualidade de Código
- Adesão aos padrões PEP 8
- Documentação inline completa
- Type hints
- Testes abrangentes

### Performance
- Tempo de carregamento < 2s
- Pontuação Lighthouse > 90
- Otimização para mobile
- Capacidade para lidar com [X] usuários simultâneos

### Usabilidade
- Interface intuitiva para usuários não-técnicos
- Tempo para aprendizado < 2 horas
- Feedback claro sobre ações
- Prevenção de erros

### Segurança
- Proteção contra vulnerabilidades OWASP top 10
- Auditorias regulares
- Validação e sanitização de inputs
- Backup automático

## Definições de Pronto
- Código revisado e aprovado
- Testes passando
- Documentação atualizada
- Funciona em todos os navegadores alvo
- Responsivo em todos os dispositivos alvo
- Acessível segundo WCAG 2.1 AA
- Performance dentro dos limites estabelecidos

## Comunicação e Governança
- Daily standup (15 min)
- Sprint planning (bi-semanal)
- Demo/review ao final de cada sprint
- Gestão de backlog contínua
- Processo de pull request com code review

---

Este briefing é um documento vivo e será atualizado conforme o projeto evolui. Todas as partes interessadas devem revisar e fornecer feedback para garantir que o produto final atenda às expectativas e necessidades dos usuários.

