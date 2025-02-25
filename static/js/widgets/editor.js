// static/js/editor.js

/**
 * Editor Visual para o Sistema de Templates
 * 
 * Este arquivo contém todo o código JavaScript necessário para:
 * - Adicionar componentes às regiões
 * - Remover componentes das regiões
 * - Reordenar componentes dentro de regiões
 * - Editar parâmetros de componentes
 * - Adicionar widgets às áreas de widgets
 * - Remover widgets das áreas
 * - Reordenar widgets dentro de áreas
 * - Editar parâmetros de widgets
 */

(function() {
    'use strict';

    // Token CSRF para requisições AJAX
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Inicialização
    document.addEventListener('DOMContentLoaded', function() {
        // Inicializa funcionalidades de componentes
        initComponentActions();
        
        // Inicializa funcionalidades de widgets
        initWidgetActions();
        
        // Inicializa drag and drop para reordenação
        initDragAndDrop();
        
        // Inicializa o botão de salvar alterações
        initSaveChanges();
    });

    /**
     * Inicializa as ações para componentes (adicionar, editar, remover)
     */
    function initComponentActions() {
        // Ação de adicionar componente
        document.querySelectorAll('.add-component').forEach(function(button) {
            button.addEventListener('click', function() {
                const componentSlug = this.getAttribute('data-component');
                const regionSlug = this.getAttribute('data-region');
                const templateSlug = this.getAttribute('data-template');
                
                addComponentToRegion(componentSlug, regionSlug, templateSlug, this);
            });
        });
        
        // Delega eventos para botões de edição e remoção de componentes
        // (necessário para componentes adicionados dinamicamente)
        document.addEventListener('click', function(e) {
            // Editar componente
            if (e.target.classList.contains('edit-component') || e.target.closest('.edit-component')) {
                const button = e.target.classList.contains('edit-component') ? e.target : e.target.closest('.edit-component');
                const componentWrapper = button.closest('.component-wrapper');
                const instanceId = componentWrapper.getAttribute('data-instance-id');
                
                openComponentEditor(instanceId);
            }
            
            // Remover componente
            if (e.target.classList.contains('remove-component') || e.target.closest('.remove-component')) {
                const button = e.target.classList.contains('remove-component') ? e.target : e.target.closest('.remove-component');
                const componentWrapper = button.closest('.component-wrapper');
                const instanceId = componentWrapper.getAttribute('data-instance-id');
                
                if (confirm('Tem certeza que deseja remover este componente?')) {
                    removeComponentInstance(instanceId, componentWrapper);
                }
            }
        });
    }

    /**
     * Inicializa as ações para widgets (adicionar, editar, remover)
     */
    function initWidgetActions() {
        // Ação de adicionar widget
        document.querySelectorAll('.add-widget').forEach(function(button) {
            button.addEventListener('click', function() {
                const widgetSlug = this.getAttribute('data-widget');
                const areaSlug = this.getAttribute('data-area');
                const templateSlug = this.getAttribute('data-template');
                
                addWidgetToArea(widgetSlug, areaSlug, templateSlug, this);
            });
        });
        
        // Delega eventos para botões de edição e remoção de widgets
        document.addEventListener('click', function(e) {
            // Editar widget
            if (e.target.classList.contains('edit-widget') || e.target.closest('.edit-widget')) {
                const button = e.target.classList.contains('edit-widget') ? e.target : e.target.closest('.edit-widget');
                const widgetWrapper = button.closest('.widget-wrapper');
                const instanceId = widgetWrapper.getAttribute('data-instance-id');
                
                openWidgetEditor(instanceId);
            }
            
            // Remover widget
            if (e.target.classList.contains('remove-widget') || e.target.closest('.remove-widget')) {
                const button = e.target.classList.contains('remove-widget') ? e.target : e.target.closest('.remove-widget');
                const widgetWrapper = button.closest('.widget-wrapper');
                const instanceId = widgetWrapper.getAttribute('data-instance-id');
                
                if (confirm('Tem certeza que deseja remover este widget?')) {
                    removeWidgetInstance(instanceId, widgetWrapper);
                }
            }
        });
    }

    /**
     * Inicializa drag and drop para reordenação de componentes e widgets
     */
    function initDragAndDrop() {
        // Para cada região editável
        document.querySelectorAll('.editable-region .region-content').forEach(function(container) {
            const region = container.closest('.editable-region');
            const regionSlug = region.getAttribute('data-region');
            const templateSlug = region.getAttribute('data-template');
            
            // Inicializa Sortable.js
            new Sortable(container, {
                group: 'components',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                handle: '.component-toolbar',
                onEnd: function(evt) {
                    // Quando a reordenação terminar, salva a nova ordem
                    const componentIds = Array.from(container.querySelectorAll('.component-wrapper'))
                                              .map(el => el.getAttribute('data-instance-id'));
                    
                    reorderComponents(templateSlug, regionSlug, componentIds);
                }
            });
        });
        
        // Para cada área de widgets editável
        document.querySelectorAll('.editable-widget-area .widget-area-content').forEach(function(container) {
            const area = container.closest('.editable-widget-area');
            const areaSlug = area.getAttribute('data-area');
            const templateSlug = area.getAttribute('data-template');
            
            // Inicializa Sortable.js
            new Sortable(container, {
                group: 'widgets',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                handle: '.widget-toolbar',
                onEnd: function(evt) {
                    // Quando a reordenação terminar, salva a nova ordem
                    const widgetIds = Array.from(container.querySelectorAll('.widget-wrapper'))
                                           .map(el => el.getAttribute('data-instance-id'));
                    
                    reorderWidgets(templateSlug, areaSlug, widgetIds);
                }
            });
        });
    }

    /**
     * Inicializa o botão de salvar alterações
     */
    function initSaveChanges() {
        const saveButton = document.getElementById('save-changes');
        if (saveButton) {
            saveButton.addEventListener('click', function() {
                saveAllChanges();
            });
        }
    }

    /**
     * Adiciona um componente a uma região
     */
    function addComponentToRegion(componentSlug, regionSlug, templateSlug, button) {
        // Fecha o modal
        const modal = button.closest('.modal');
        if (modal) {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            modalInstance.hide();
        }
        
        // Exibe indicador de carregamento
        showLoading();
        
        // Envia a requisição para adicionar o componente
        const formData = new FormData();
        formData.append('component_slug', componentSlug);
        
        fetch(`/templates/api/region/${templateSlug}/${regionSlug}/component/add/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao adicionar componente');
            }
            return response.json();
        })
        .then(data => {
            // Adiciona o componente renderizado à região
            const region = document.querySelector(`.editable-region[data-region="${regionSlug}"][data-template="${templateSlug}"]`);
            const regionContent = region.querySelector('.region-content');
            
            // Cria um wrapper temporário para interpretar o HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = data.rendered_component;
            
            // Adiciona o atributo de ID da instância
            const wrapper = tempDiv.querySelector('.component-wrapper');
            if (wrapper) {
                wrapper.setAttribute('data-instance-id', data.instance_id);
            }
            
            // Adiciona o componente à região
            regionContent.appendChild(tempDiv.firstChild);
            
            // Remove o placeholder se existir
            const placeholder = region.querySelector('.empty-region-placeholder');
            if (placeholder) {
                placeholder.remove();
            }
            
            // Exibe mensagem de sucesso
            showNotification('success', 'Componente adicionado com sucesso');
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        })
        .finally(() => {
            hideLoading();
        });
    }

    /**
     * Abre o editor de componente em um modal
     */
    function openComponentEditor(instanceId) {
        // Exibe indicador de carregamento
        showLoading();
        
        // Busca os dados do componente
        fetch(`/templates/api/component-instance/${instanceId}/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao carregar dados do componente');
            }
            return response.json();
        })
        .then(data => {
            // Cria um modal para editar o componente
            createComponentEditorModal(instanceId, data);
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        })
        .finally(() => {
            hideLoading();
        });
    }

    /**
     * Cria um modal para editar um componente
     */
    function createComponentEditorModal(instanceId, data) {
        // Cria o HTML do modal
        const modalId = `editComponentModal-${instanceId}`;
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}Label" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="${modalId}Label">Editar Componente: ${data.component.name}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editComponentForm-${instanceId}">
                                <ul class="nav nav-tabs" id="componentEditorTabs-${instanceId}" role="tablist">
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link active" id="content-tab-${instanceId}" data-bs-toggle="tab" 
                                                data-bs-target="#content-${instanceId}" type="button" role="tab" 
                                                aria-controls="content" aria-selected="true">
                                            Conteúdo
                                        </button>
                                    </li>
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link" id="style-tab-${instanceId}" data-bs-toggle="tab" 
                                                data-bs-target="#style-${instanceId}" type="button" role="tab" 
                                                aria-controls="style" aria-selected="false">
                                            Estilo
                                        </button>
                                    </li>
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link" id="visibility-tab-${instanceId}" data-bs-toggle="tab" 
                                                data-bs-target="#visibility-${instanceId}" type="button" role="tab" 
                                                aria-controls="visibility" aria-selected="false">
                                            Visibilidade
                                        </button>
                                    </li>
                                </ul>
                                <div class="tab-content p-3 border border-top-0 rounded-bottom" id="componentEditorTabContent-${instanceId}">
                                    <div class="tab-pane fade show active" id="content-${instanceId}" role="tabpanel" aria-labelledby="content-tab-${instanceId}">
                                        ${generateComponentDataFields(data)}
                                    </div>
                                    <div class="tab-pane fade" id="style-${instanceId}" role="tabpanel" aria-labelledby="style-tab-${instanceId}">
                                        <div class="mb-3">
                                            <label for="customClasses-${instanceId}" class="form-label">Classes CSS personalizadas</label>
                                            <input type="text" class="form-control" id="customClasses-${instanceId}" name="custom_classes" value="${data.custom_classes || ''}">
                                            <div class="form-text">Classes CSS adicionais para personalizar o componente.</div>
                                        </div>
                                        <div class="mb-3">
                                            <label for="customCSS-${instanceId}" class="form-label">CSS Personalizado</label>
                                            <textarea class="form-control" id="customCSS-${instanceId}" name="custom_css" rows="8">${data.custom_css || ''}</textarea>
                                            <div class="form-text">CSS personalizado para este componente específico.</div>
                                        </div>
                                    </div>
                                    <div class="tab-pane fade" id="visibility-${instanceId}" role="tabpanel" aria-labelledby="visibility-tab-${instanceId}">
                                        <div class="form-check form-switch mb-3">
                                            <input class="form-check-input" type="checkbox" id="isVisible-${instanceId}" name="is_visible" ${data.is_visible ? 'checked' : ''}>
                                            <label class="form-check-label" for="isVisible-${instanceId}">Componente visível</label>
                                        </div>
                                        <div class="mb-3">
                                            <label for="visibilityRules-${instanceId}" class="form-label">Regras de Visibilidade (JSON)</label>
                                            <textarea class="form-control json-editor" id="visibilityRules-${instanceId}" name="visibility_rules" rows="8">${data.visibility_rules ? JSON.stringify(data.visibility_rules, null, 2) : '{}'}</textarea>
                                            <div class="form-text">
                                                Regras para exibição condicional do componente. Exemplo: <code>{"device": ["mobile", "tablet"]}</code>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" id="saveComponent-${instanceId}">Salvar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Adiciona o modal ao DOM
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer);
        
        // Inicializa o modal
        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();
        
        // Inicializa editores avançados (CodeMirror, etc.) se necessário
        initializeAdvancedEditors(instanceId);
        
        // Manipulador para salvar as alterações
        document.getElementById(`saveComponent-${instanceId}`).addEventListener('click', function() {
            saveComponentChanges(instanceId, modal);
        });
        
        // Limpa o modal quando for fechado
        document.getElementById(modalId).addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    /**
     * Gera campos de formulário baseados nos dados do componente
     */
    function generateComponentDataFields(data) {
        let fieldsHtml = '';
        const contextData = data.context_data || {};
        
        // Para cada campo no contexto padrão do componente
        for (const [key, value] of Object.entries(data.component.default_context || {})) {
            const currentValue = contextData[key] !== undefined ? contextData[key] : value;
            const fieldId = `field-${data.id}-${key}`;
            
            // Determina o tipo de campo com base no valor
            if (typeof currentValue === 'boolean') {
                // Campo booleano (checkbox)
                fieldsHtml += `
                    <div class="form-check mb-3">
                        <input class="form-check-input" type="checkbox" id="${fieldId}" name="context_data.${key}" ${currentValue ? 'checked' : ''}>
                        <label class="form-check-label" for="${fieldId}">${formatFieldLabel(key)}</label>
                    </div>
                `;
            } else if (typeof currentValue === 'number') {
                // Campo numérico
                fieldsHtml += `
                    <div class="mb-3">
                        <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                        <input type="number" class="form-control" id="${fieldId}" name="context_data.${key}" value="${currentValue}">
                    </div>
                `;
            } else if (typeof currentValue === 'string') {
                if (currentValue.startsWith('/') || currentValue.startsWith('http')) {
                    // URL ou caminho de arquivo
                    fieldsHtml += `
                        <div class="mb-3">
                            <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                            <div class="input-group">
                                <input type="text" class="form-control" id="${fieldId}" name="context_data.${key}" value="${currentValue}">
                                <button class="btn btn-outline-secondary" type="button" onclick="openMediaBrowser('${fieldId}')">
                                    <i class="fas fa-file-image"></i>
                                </button>
                            </div>
                        </div>
                    `;
                } else if (currentValue.length > 100) {
                    // Texto longo
                    fieldsHtml += `
                        <div class="mb-3">
                            <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                            <textarea class="form-control" id="${fieldId}" name="context_data.${key}" rows="4">${currentValue}</textarea>
                        </div>
                    `;
                } else {
                    // Texto curto
                    fieldsHtml += `
                        <div class="mb-3">
                            <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                            <input type="text" class="form-control" id="${fieldId}" name="context_data.${key}" value="${currentValue}">
                        </div>
                    `;
                }
            } else if (Array.isArray(currentValue)) {
                // Array (JSON)
                fieldsHtml += `
                    <div class="mb-3">
                        <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                        <textarea class="form-control json-editor" id="${fieldId}" name="context_data.${key}" rows="4">${JSON.stringify(currentValue, null, 2)}</textarea>
                    </div>
                `;
            } else if (typeof currentValue === 'object' && currentValue !== null) {
                // Objeto (JSON)
                fieldsHtml += `
                    <div class="mb-3">
                        <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                        <textarea class="form-control json-editor" id="${fieldId}" name="context_data.${key}" rows="4">${JSON.stringify(currentValue, null, 2)}</textarea>
                    </div>
                `;
            }
        }
        
        return fieldsHtml;
    }

    /**
     * Formata um nome de campo para exibição amigável
     */
    function formatFieldLabel(key) {
        return key
            .replace(/_/g, ' ')
            .replace(/([A-Z])/g, ' $1')
            .replace(/^./, function(str) { return str.toUpperCase(); });
    }

    /**
     * Inicializa editores avançados para campos de código
     */
    function initializeAdvancedEditors(instanceId) {
        // Inicializa CodeMirror para editores de JSON
        document.querySelectorAll(`#editComponentForm-${instanceId} .json-editor`).forEach(function(textarea) {
            if (window.CodeMirror) {
                CodeMirror.fromTextArea(textarea, {
                    mode: {name: "javascript", json: true},
                    lineNumbers: true,
                    theme: "default",
                    lineWrapping: true,
                    foldGutter: true,
                    gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"]
                });
            }
        });
        
        // Inicializa CodeMirror para editor de CSS
        const cssEditor = document.getElementById(`customCSS-${instanceId}`);
        if (cssEditor && window.CodeMirror) {
            CodeMirror.fromTextArea(cssEditor, {
                mode: "css",
                lineNumbers: true,
                theme: "default",
                lineWrapping: true
            });
        }
    }

    /**
     * Salva as alterações feitas em um componente
     */
    function saveComponentChanges(instanceId, modal) {
        // Exibe indicador de carregamento
        showLoading();
        
        // Coleta os dados do formulário
        const form = document.getElementById(`editComponentForm-${instanceId}`);
        const formData = new FormData();
        
        // Dados básicos
        formData.append('custom_classes', form.querySelector('[name="custom_classes"]').value);
        formData.append('is_visible', form.querySelector('[name="is_visible"]').checked);
        
        // Dados de contexto
        const contextData = {};
        form.querySelectorAll('[name^="context_data."]').forEach(function(input) {
            const key = input.name.replace('context_data.', '');
            let value;
            
            // Processa o valor conforme o tipo de campo
            if (input.type === 'checkbox') {
                value = input.checked;
            } else if (input.classList.contains('json-editor')) {
                // Obtém o valor do CodeMirror se estiver ativo
                const editor = input.nextElementSibling && input.nextElementSibling.classList.contains('CodeMirror') 
                             ? input.nextElementSibling.CodeMirror 
                             : null;
                
                if (editor) {
                    try {
                        value = JSON.parse(editor.getValue());
                    } catch (e) {
                        console.error('Erro ao parse JSON:', e);
                        showNotification('error', `Erro no JSON do campo "${key}": ${e.message}`);
                        hideLoading();
                        return;
                    }
                } else {
                    try {
                        value = JSON.parse(input.value);
                    } catch (e) {
                        console.error('Erro ao parse JSON:', e);
                        showNotification('error', `Erro no JSON do campo "${key}": ${e.message}`);
                        hideLoading();
                        return;
                    }
                }
            } else {
                value = input.value;
                
                // Converte para número se for um campo numérico
                if (input.type === 'number') {
                    value = parseFloat(value);
                }
            }
            
            contextData[key] = value;
        });
        
        formData.append('context_data', JSON.stringify(contextData));
        
        // CSS personalizado
        const cssEditor = document.querySelector(`#customCSS-${instanceId}`);
        if (cssEditor) {
            const editor = cssEditor.nextElementSibling && cssEditor.nextElementSibling.classList.contains('CodeMirror') 
                         ? cssEditor.nextElementSibling.CodeMirror 
                         : null;
            
            if (editor) {
                formData.append('custom_css', editor.getValue());
            } else {
                formData.append('custom_css', cssEditor.value);
            }
        }
        
        // Regras de visibilidade
        const visibilityRulesEditor = document.querySelector(`#visibilityRules-${instanceId}`);
        if (visibilityRulesEditor) {
            const editor = visibilityRulesEditor.nextElementSibling && visibilityRulesEditor.nextElementSibling.classList.contains('CodeMirror') 
                         ? visibilityRulesEditor.nextElementSibling.CodeMirror 
                         : null;
            
            if (editor) {
                try {
                    const rules = JSON.parse(editor.getValue());
                    formData.append('visibility_rules', JSON.stringify(rules));
                } catch (e) {
                    console.error('Erro ao parse JSON de regras de visibilidade:', e);
                    showNotification('error', `Erro no JSON de regras de visibilidade: ${e.message}`);
                    hideLoading();
                    return;
                }
            } else {
                try {
                    const rules = JSON.parse(visibilityRulesEditor.value);
                    formData.append('visibility_rules', JSON.stringify(rules));
                } catch (e) {
                    console.error('Erro ao parse JSON de regras de visibilidade:', e);
                    showNotification('error', `Erro no JSON de regras de visibilidade: ${e.message}`);
                    hideLoading();
                    return;
                }
            }
        }
        
        // Envia a requisição para atualizar o componente
        fetch(`/templates/api/component-instance/${instanceId}/update/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao atualizar componente');
            }
            return response.json();
        })
        .then(data => {
            // Atualiza o componente na página
            const componentWrapper = document.querySelector(`.component-wrapper[data-instance-id="${instanceId}"]`);
            if (componentWrapper) {
                const componentContent = componentWrapper.querySelector('.component-content');
                if (componentContent) {
                    componentContent.innerHTML = data.rendered_component;
                }
            }
            
            // Fecha o modal
            modal.hide();
            
            // Exibe mensagem de sucesso
            showNotification('success', 'Componente atualizado com sucesso');
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        })
        .finally(() => {
            hideLoading();
        });
    }

    /**
     * Remove uma instância de componente
     */
    function removeComponentInstance(instanceId, componentWrapper) {
        // Exibe indicador de carregamento
        showLoading();
        
        fetch(`/templates/api/component-instance/${instanceId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao remover componente');
            }
            return response.json();
        })
        .then(data => {
            // Remove o componente do DOM
            componentWrapper.remove();
            
            // Verifica se a região ficou vazia
            const region = componentWrapper.closest('.editable-region');
            const regionContent = region.querySelector('.region-content');
            
            if (!regionContent.hasChildNodes()) {
                // Adiciona o placeholder de região vazia
                const placeholder = document.createElement('div');
                placeholder.className = 'empty-region-placeholder';
                placeholder.innerHTML = '<p>Adicione componentes aqui</p>';
                region.insertBefore(placeholder, regionContent);
            }
            
            // Exibe mensagem de sucesso
            showNotification('success', 'Componente removido com sucesso');
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        })
        .finally(() => {
            hideLoading();
        });
    }

    /**
     * Reordena componentes em uma região
     */
    function reorderComponents(templateSlug, regionSlug, componentIds) {
        // Envia a requisição para reordenar os componentes
        fetch(`/templates/api/region/${templateSlug}/${regionSlug}/reorder/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                component_ids: componentIds
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao reordenar componentes');
            }
            return response.json();
        })
        .then(data => {
            // Exibe mensagem de sucesso
            showNotification('success', 'Ordem dos componentes atualizada');
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        });
    }

    /**
     * Adiciona um widget a uma área
     */
    function addWidgetToArea(widgetSlug, areaSlug, templateSlug, button) {
        // Fecha o modal
        const modal = button.closest('.modal');
        if (modal) {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            modalInstance.hide();
        }
        
        // Exibe indicador de carregamento
        showLoading();
        
        // Envia a requisição para adicionar o widget
        const formData = new FormData();
        formData.append('widget_slug', widgetSlug);
        
        fetch(`/templates/api/widget-area/${templateSlug}/${areaSlug}/widget/add/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao adicionar widget');
            }
            return response.json();
        })
        .then(data => {
            // Adiciona o widget renderizado à área
            const area = document.querySelector(`.editable-widget-area[data-area="${areaSlug}"][data-template="${templateSlug}"]`);
            const areaContent = area.querySelector('.widget-area-content');
            
            // Cria um wrapper temporário para interpretar o HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = data.rendered_widget;
            
            // Adiciona o atributo de ID da instância
            const wrapper = tempDiv.querySelector('.widget-wrapper');
            if (wrapper) {
                wrapper.setAttribute('data-instance-id', data.instance_id);
            }
            
            // Adiciona o widget à área
            areaContent.appendChild(tempDiv.firstChild);
            
            // Remove o placeholder se existir
            const placeholder = area.querySelector('.empty-widget-area-placeholder');
            if (placeholder) {
                placeholder.remove();
            }
            
            // Exibe mensagem de sucesso
            showNotification('success', 'Widget adicionado com sucesso');
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        })
        .finally(() => {
            hideLoading();
        });
    }

    /**
     * Abre o editor de widget em um modal
     */
    function openWidgetEditor(instanceId) {
        // Exibe indicador de carregamento
        showLoading();
        
        // Busca os dados do widget
        fetch(`/templates/api/widget-instance/${instanceId}/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao carregar dados do widget');
            }
            return response.json();
        })
        .then(data => {
            // Cria um modal para editar o widget
            createWidgetEditorModal(instanceId, data);
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        })
        .finally(() => {
            hideLoading();
        });
    }

    /**
     * Cria um modal para editar um widget
     */
    function createWidgetEditorModal(instanceId, data) {
        // Cria o HTML do modal
        const modalId = `editWidgetModal-${instanceId}`;
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}Label" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="${modalId}Label">Editar Widget: ${data.widget.name}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editWidgetForm-${instanceId}">
                                <ul class="nav nav-tabs" id="widgetEditorTabs-${instanceId}" role="tablist">
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link active" id="settings-tab-${instanceId}" data-bs-toggle="tab" 
                                                data-bs-target="#settings-${instanceId}" type="button" role="tab" 
                                                aria-controls="settings" aria-selected="true">
                                            Configurações
                                        </button>
                                    </li>
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link" id="style-tab-${instanceId}" data-bs-toggle="tab" 
                                                data-bs-target="#style-${instanceId}" type="button" role="tab" 
                                                aria-controls="style" aria-selected="false">
                                            Estilo
                                        </button>
                                    </li>
                                    <li class="nav-item" role="presentation">
                                        <button class="nav-link" id="visibility-tab-${instanceId}" data-bs-toggle="tab" 
                                                data-bs-target="#visibility-${instanceId}" type="button" role="tab" 
                                                aria-controls="visibility" aria-selected="false">
                                            Visibilidade
                                        </button>
                                    </li>
                                </ul>
                                <div class="tab-content p-3 border border-top-0 rounded-bottom" id="widgetEditorTabContent-${instanceId}">
                                    <div class="tab-pane fade show active" id="settings-${instanceId}" role="tabpanel" aria-labelledby="settings-tab-${instanceId}">
                                        <div class="mb-3">
                                            <label for="widgetTitle-${instanceId}" class="form-label">Título do Widget</label>
                                            <input type="text" class="form-control" id="widgetTitle-${instanceId}" name="title" value="${data.title || ''}">
                                        </div>
                                        ${generateWidgetSettingsFields(data)}
                                    </div>
                                    <div class="tab-pane fade" id="style-${instanceId}" role="tabpanel" aria-labelledby="style-tab-${instanceId}">
                                        <div class="mb-3">
                                            <label for="customClasses-${instanceId}" class="form-label">Classes CSS personalizadas</label>
                                            <input type="text" class="form-control" id="customClasses-${instanceId}" name="custom_classes" value="${data.custom_classes || ''}">
                                            <div class="form-text">Classes CSS adicionais para personalizar o widget.</div>
                                        </div>
                                        <div class="mb-3">
                                            <label for="customCSS-${instanceId}" class="form-label">CSS Personalizado</label>
                                            <textarea class="form-control" id="customCSS-${instanceId}" name="custom_css" rows="8">${data.custom_css || ''}</textarea>
                                            <div class="form-text">CSS personalizado para este widget específico.</div>
                                        </div>
                                    </div>
                                    <div class="tab-pane fade" id="visibility-${instanceId}" role="tabpanel" aria-labelledby="visibility-tab-${instanceId}">
                                        <div class="form-check form-switch mb-3">
                                            <input class="form-check-input" type="checkbox" id="isVisible-${instanceId}" name="is_visible" ${data.is_visible ? 'checked' : ''}>
                                            <label class="form-check-label" for="isVisible-${instanceId}">Widget visível</label>
                                        </div>
                                        <div class="mb-3">
                                            <label for="visibilityRules-${instanceId}" class="form-label">Regras de Visibilidade (JSON)</label>
                                            <textarea class="form-control json-editor" id="visibilityRules-${instanceId}" name="visibility_rules" rows="8">${data.visibility_rules ? JSON.stringify(data.visibility_rules, null, 2) : '{}'}</textarea>
                                            <div class="form-text">
                                                Regras para exibição condicional do widget. Exemplo: <code>{"device": ["mobile", "tablet"]}</code>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" id="saveWidget-${instanceId}">Salvar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Adiciona o modal ao DOM
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer);
        
        // Inicializa o modal
        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();
        
        // Inicializa editores avançados (CodeMirror, etc.) se necessário
        initializeWidgetAdvancedEditors(instanceId);
        
        // Manipulador para salvar as alterações
        document.getElementById(`saveWidget-${instanceId}`).addEventListener('click', function() {
            saveWidgetChanges(instanceId, modal);
        });
        
        // Limpa o modal quando for fechado
        document.getElementById(modalId).addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }

    /**
     * Gera campos de formulário baseados nas configurações do widget
     */
    function generateWidgetSettingsFields(data) {
        let fieldsHtml = '';
        const settings = data.settings || {};
        
        // Para cada campo nas configurações padrão do widget
        for (const [key, value] of Object.entries(data.widget.default_settings || {})) {
            const currentValue = settings[key] !== undefined ? settings[key] : value;
            const fieldId = `field-${data.id}-${key}`;
            
            // Determina o tipo de campo com base no valor
            if (typeof currentValue === 'boolean') {
                // Campo booleano (checkbox)
                fieldsHtml += `
                    <div class="form-check mb-3">
                        <input class="form-check-input" type="checkbox" id="${fieldId}" name="settings.${key}" ${currentValue ? 'checked' : ''}>
                        <label class="form-check-label" for="${fieldId}">${formatFieldLabel(key)}</label>
                    </div>
                `;
            } else if (typeof currentValue === 'number') {
                // Campo numérico
                fieldsHtml += `
                    <div class="mb-3">
                        <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                        <input type="number" class="form-control" id="${fieldId}" name="settings.${key}" value="${currentValue}">
                    </div>
                `;
            } else if (typeof currentValue === 'string') {
                if (currentValue.startsWith('/') || currentValue.startsWith('http')) {
                    // URL ou caminho de arquivo
                    fieldsHtml += `
                        <div class="mb-3">
                            <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                            <div class="input-group">
                                <input type="text" class="form-control" id="${fieldId}" name="settings.${key}" value="${currentValue}">
                                <button class="btn btn-outline-secondary" type="button" onclick="openMediaBrowser('${fieldId}')">
                                    <i class="fas fa-file-image"></i>
                                </button>
                            </div>
                        </div>
                    `;
                } else if (currentValue.length > 100) {
                    // Texto longo
                    fieldsHtml += `
                        <div class="mb-3">
                            <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                            <textarea class="form-control" id="${fieldId}" name="settings.${key}" rows="4">${currentValue}</textarea>
                        </div>
                    `;
                } else {
                    // Texto curto
                    fieldsHtml += `
                        <div class="mb-3">
                            <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                            <input type="text" class="form-control" id="${fieldId}" name="settings.${key}" value="${currentValue}">
                        </div>
                    `;
                }
            } else if (Array.isArray(currentValue)) {
                // Array (JSON)
                fieldsHtml += `
                    <div class="mb-3">
                        <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                        <textarea class="form-control json-editor" id="${fieldId}" name="settings.${key}" rows="4">${JSON.stringify(currentValue, null, 2)}</textarea>
                    </div>
                `;
            } else if (typeof currentValue === 'object' && currentValue !== null) {
                // Objeto (JSON)
                fieldsHtml += `
                    <div class="mb-3">
                        <label for="${fieldId}" class="form-label">${formatFieldLabel(key)}</label>
                        <textarea class="form-control json-editor" id="${fieldId}" name="settings.${key}" rows="4">${JSON.stringify(currentValue, null, 2)}</textarea>
                    </div>
                `;
            }
        }
        
        return fieldsHtml;
    }

    /**
     * Inicializa editores avançados para campos de código em widgets
     */
    function initializeWidgetAdvancedEditors(instanceId) {
        // Inicializa CodeMirror para editores de JSON
        document.querySelectorAll(`#editWidgetForm-${instanceId} .json-editor`).forEach(function(textarea) {
            if (window.CodeMirror) {
                CodeMirror.fromTextArea(textarea, {
                    mode: {name: "javascript", json: true},
                    lineNumbers: true,
                    theme: "default",
                    lineWrapping: true,
                    foldGutter: true,
                    gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"]
                });
            }
        });
        
        // Inicializa CodeMirror para editor de CSS
        const cssEditor = document.getElementById(`customCSS-${instanceId}`);
        if (cssEditor && window.CodeMirror) {
            CodeMirror.fromTextArea(cssEditor, {
                mode: "css",
                lineNumbers: true,
                theme: "default",
                lineWrapping: true
            });
        }
    }

    /**
     * Salva as alterações feitas em um widget
     */
    function saveWidgetChanges(instanceId, modal) {
        // Exibe indicador de carregamento
        showLoading();
        
        // Coleta os dados do formulário
        const form = document.getElementById(`editWidgetForm-${instanceId}`);
        const formData = new FormData();
        
        // Dados básicos
        formData.append('title', form.querySelector('[name="title"]').value);
        formData.append('custom_classes', form.querySelector('[name="custom_classes"]').value);
        formData.append('is_visible', form.querySelector('[name="is_visible"]').checked);
        
        // Configurações do widget
        const settingsData = {};
        form.querySelectorAll('[name^="settings."]').forEach(function(input) {
            const key = input.name.replace('settings.', '');
            let value;
            
            // Processa o valor conforme o tipo de campo
            if (input.type === 'checkbox') {
                value = input.checked;
            } else if (input.classList.contains('json-editor')) {
                // Obtém o valor do CodeMirror se estiver ativo
                const editor = input.nextElementSibling && input.nextElementSibling.classList.contains('CodeMirror') 
                             ? input.nextElementSibling.CodeMirror 
                             : null;
                
                if (editor) {
                    try {
                        value = JSON.parse(editor.getValue());
                    } catch (e) {
                        console.error('Erro ao parse JSON:', e);
                        showNotification('error', `Erro no JSON do campo "${key}": ${e.message}`);
                        hideLoading();
                        return;
                    }
                } else {
                    try {
                        value = JSON.parse(input.value);
                    } catch (e) {
                        console.error('Erro ao parse JSON:', e);
                        showNotification('error', `Erro no JSON do campo "${key}": ${e.message}`);
                        hideLoading();
                        return;
                    }
                }
            } else {
                value = input.value;
                
                // Converte para número se for um campo numérico
                if (input.type === 'number') {
                    value = parseFloat(value);
                }
            }
            
            settingsData[key] = value;
        });
        
        formData.append('settings', JSON.stringify(settingsData));
        
        // CSS personalizado
        const cssEditor = document.querySelector(`#customCSS-${instanceId}`);
        if (cssEditor) {
            const editor = cssEditor.nextElementSibling && cssEditor.nextElementSibling.classList.contains('CodeMirror') 
                         ? cssEditor.nextElementSibling.CodeMirror 
                         : null;
            
            if (editor) {
                formData.append('custom_css', editor.getValue());
            } else {
                formData.append('custom_css', cssEditor.value);
            }
        }
        
        // Regras de visibilidade
        const visibilityRulesEditor = document.querySelector(`#visibilityRules-${instanceId}`);
        if (visibilityRulesEditor) {
            const editor = visibilityRulesEditor.nextElementSibling && visibilityRulesEditor.nextElementSibling.classList.contains('CodeMirror') 
                         ? visibilityRulesEditor.nextElementSibling.CodeMirror 
                         : null;
            
            if (editor) {
                try {
                    const rules = JSON.parse(editor.getValue());
                    formData.append('visibility_rules', JSON.stringify(rules));
                } catch (e) {
                    console.error('Erro ao parse JSON de regras de visibilidade:', e);
                    showNotification('error', `Erro no JSON de regras de visibilidade: ${e.message}`);
                    hideLoading();
                    return;
                }
            } else {
                try {
                    const rules = JSON.parse(visibilityRulesEditor.value);
                    formData.append('visibility_rules', JSON.stringify(rules));
                } catch (e) {
                    console.error('Erro ao parse JSON de regras de visibilidade:', e);
                    showNotification('error', `Erro no JSON de regras de visibilidade: ${e.message}`);
                    hideLoading();
                    return;
                }
            }
        }
        
        // Envia a requisição para atualizar o widget
        fetch(`/templates/api/widget-instance/${instanceId}/update/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao atualizar widget');
            }
            return response.json();
        })
        .then(data => {
            // Atualiza o widget na página
            const widgetWrapper = document.querySelector(`.widget-wrapper[data-instance-id="${instanceId}"]`);
            if (widgetWrapper) {
                const widgetContent = widgetWrapper.querySelector('.widget-content');
                if (widgetContent) {
                    widgetContent.innerHTML = data.rendered_widget;
                }
            }
            
            // Fecha o modal
            modal.hide();
            
            // Exibe mensagem de sucesso
            showNotification('success', 'Widget atualizado com sucesso');
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        })
        .finally(() => {
            hideLoading();
        });
    }

    /**
     * Remove uma instância de widget
     */
    function removeWidgetInstance(instanceId, widgetWrapper) {
        // Exibe indicador de carregamento
        showLoading();
        
        fetch(`/templates/api/widget-instance/${instanceId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao remover widget');
            }
            return response.json();
        })
        .then(data => {
            // Remove o widget do DOM
            widgetWrapper.remove();
            
            // Verifica se a área ficou vazia
            const area = widgetWrapper.closest('.editable-widget-area');
            const areaContent = area.querySelector('.widget-area-content');
            
            if (!areaContent.hasChildNodes()) {
                // Adiciona o placeholder de área vazia
                const placeholder = document.createElement('div');
                placeholder.className = 'empty-widget-area-placeholder';
                placeholder.innerHTML = '<p>Adicione widgets aqui</p>';
                area.insertBefore(placeholder, areaContent);
            }
            
            // Exibe mensagem de sucesso
            showNotification('success', 'Widget removido com sucesso');
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        })
        .finally(() => {
            hideLoading();
        });
    }

    /**
     * Reordena widgets em uma área
     */
    function reorderWidgets(templateSlug, areaSlug, widgetIds) {
        // Envia a requisição para reordenar os widgets
        fetch(`/templates/api/widget-area/${templateSlug}/${areaSlug}/reorder/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                widget_ids: widgetIds
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao reordenar widgets');
            }
            return response.json();
        })
        .then(data => {
            // Exibe mensagem de sucesso
            showNotification('success', 'Ordem dos widgets atualizada');
        })
        .catch(error => {
            console.error('Erro:', error);
            showNotification('error', error.message);
        });
    }

    /**
     * Salva todas as alterações pendentes
     */
    function saveAllChanges() {
        // Exibe indicador de carregamento
        showLoading();
        
        // Aqui podemos implementar qualquer lógica adicional
        // para garantir que todas as alterações sejam salvas
        
        // Por exemplo, podemos forçar uma atualização na página
        setTimeout(function() {
            hideLoading();
            showNotification('success', 'Todas as alterações foram salvas com sucesso');
            
            // Opcional: recarrega a página
            // window.location.reload();
        }, 1000);
    }

    /**
     * Abre o navegador de mídia
     */
    function openMediaBrowser(fieldId) {
        // Implementar a lógica para abrir o navegador de mídia
        // e popular o campo com o arquivo selecionado
        console.log('Abrir navegador de mídia para o campo:', fieldId);
        
        // Exemplo de implementação simples:
        window.open('/admin/media/browser/?field=' + fieldId, 'mediaBrowser', 'width=800,height=600');
    }

    /**
     * Manipulador para receber a seleção do navegador de mídia
     */
    window.setMediaFile = function(fieldId, fileUrl) {
        document.getElementById(fieldId).value = fileUrl;
    };

    /**
     * Exibe uma notificação
     */
    function showNotification(type, message) {
        // Cria o elemento de notificação
        const notification = document.createElement('div');
        notification.className = `toast show bg-${type === 'success' ? 'success' : 'danger'} text-white`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.setAttribute('aria-atomic', 'true');
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '1050';
        
        notification.innerHTML = `
            <div class="toast-header bg-${type === 'success' ? 'success' : 'danger'} text-white">
                <strong class="me-auto">${type === 'success' ? 'Sucesso' : 'Erro'}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Fechar"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Adiciona a notificação ao DOM
        document.body.appendChild(notification);
        
        // Adiciona o manipulador para fechar a notificação
        notification.querySelector('.btn-close').addEventListener('click', function() {
            notification.remove();
        });
        
        // Remove a notificação após alguns segundos
        setTimeout(function() {
            notification.remove();
        }, 5000);
    }

    /**
     * Exibe o indicador de carregamento
     */
    function showLoading() {
        // Verifica se já existe um indicador de carregamento
        if (document.getElementById('loading-indicator')) {
            return;
        }
        
        // Cria o elemento de carregamento
        const loading = document.createElement('div');
        loading.id = 'loading-indicator';
        loading.style.position = 'fixed';
        loading.style.top = '0';
        loading.style.left = '0';
        loading.style.width = '100%';
        loading.style.height = '100%';
        loading.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        loading.style.display = 'flex';
        loading.style.justifyContent = 'center';
        loading.style.alignItems = 'center';
        loading.style.zIndex = '1060';
        
        loading.innerHTML = `
            <div class="spinner-border text-light" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Carregando...</span>
            </div>
        `;
        
        // Adiciona o loading ao DOM
        document.body.appendChild(loading);
    }

    /**
     * Oculta o indicador de carregamento
     */
    function hideLoading() {
        const loading = document.getElementById('loading-indicator');
        if (loading) {
            loading.remove();
        }
    }

})();// static/js/editor.js

/**
 * Editor Visual para o Sistema de Templates
 * 
 * Este arquivo contém todo o código JavaScript necessário para:
 * - Adicionar componentes às regiões
 * - Remover componentes das regiões
 * - Reordenar componentes dentro de regiões
 * - Editar parâmetros de componentes
 * - Adicionar widgets às áreas de widgets
 * - Remover widgets das áreas
 * - Reordenar widgets dentro de áreas
 * - Editar parâmetros de widgets
 */

(function() {
    'use strict';

    // Token CSRF para requisições AJAX
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Inicialização
    document.addEventListener('DOMContentLoaded', function() {
        // Inicializa funcionalidades de componentes
        initComponentActions();
        
        // Inicializa funcionalidades de widgets
        initWidgetActions();
        
        // Inicializa drag and drop para reordenação
        initDragAndDrop();
        
        // Inicializa o botão de salvar alterações
        initSaveChanges();
    });

    /**
     * Inicializa as ações para componentes (adicionar, editar, remover)
     */
    function initComponentActions() {
        // Ação de adicionar componente
        document.querySelectorAll('.add-component').forEach(function(button) {
            button.addEventListener('click', function() {
                const componentSlug = this.getAttribute('data-component');
                const regionSlug = this.getAttribute('data-region');
                const templateSlug = this.getAttribute('data-template');
                
                addComponentToRegion(componentSlug, regionSlug, templateSlug, this);
            });
        });
        
        // Delega eventos para botões de edição e remoção de componentes
        // (necessário para componentes adicionados dinamicamente)
        document.addEventListener('click', function(e) {
            // Editar componente
            if (e.target.classList.contains('edit-component') || e.target.closest('.edit-component')) {
                const button = e.target.classList.contains('edit-component') ? e.target : e.target.closest('.edit-component');
                const componentWrapper = button.closest('.component-wrapper');
                const instanceId = componentWrapper.getAttribute('data-instance-id');
                
                openComponentEditor(instanceId);
            }
            
            // Remover componente
            if (e.target.classList.contains('remove-component') || e.target.closest('.remove-component')) {
                const button = e.target.classList.contains('remove-component') ? e.target : e.target.closest('.remove-component');
                const componentWrapper = button.closest('.component-wrapper');
                const instanceId = componentWrapper.getAttribute('data-instance-id');
                
                if (confirm('Tem certeza que deseja remover este componente?')) {
                    removeComponentInstance(instanceId, componentWrapper);
                }
            }
        });
    }

    /**
     * Inicializa as ações para widgets (adicionar, editar, remover)
     */
    function initWidgetActions() {
        // Ação de adicionar widget
        document.querySelectorAll('.add-widget').forEach(function(button) {
            button.addEventListener('click', function() {
                const widgetSlug = this.getAttribute('data-widget');
                const areaSlug = this.getAttribute('data-area');
                const templateSlug = this.getAttribute('data-template');
                
                addWidgetToArea(widgetSlug, areaSlug, templateSlug, this);
            });
        });
        
        // Delega eventos para botões de edição e remoção de widgets
        document.addEventListener('click', function(e) {
            // Editar widget
            if (e.target.classList.contains('edit-widget') || e.target.closest('.edit-widget')) {
                const button = e.target.classList.contains('edit-widget') ? e.target : e.target.closest('.edit-widget');
                const widgetWrapper = button.closest('.widget-wrapper');
                const instanceId = widgetWrapper.getAttribute('data-instance-id');
                
                openWidgetEditor(instanceId);
            }
            
            // Remover widget
            if (e.target.classList.contains('remove-widget') || e.target.closest