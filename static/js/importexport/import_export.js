/**
 * import_export.js - Funções auxiliares para importação e exportação
 */

// Inicializa os elementos da página
document.addEventListener('DOMContentLoaded', function() {
    // Validação de arquivo de importação
    const importFileInput = document.getElementById('import_file');
    if (importFileInput) {
        importFileInput.addEventListener('change', function() {
            validateImportFile(this);
        });
    }
    
    // Progresso de exportação
    const exportButton = document.getElementById('export-button');
    if (exportButton) {
        exportButton.addEventListener('click', function() {
            handleExport();
        });
    }
});

/**
 * Valida o arquivo de importação selecionado
 */
function validateImportFile(input) {
    const file = input.files[0];
    if (!file) return;
    
    const fileSize = file.size / 1024 / 1024; // tamanho em MB
    const fileName = file.name;
    const fileExt = fileName.split('.').pop().toLowerCase();
    
    // Verifica o tipo de arquivo
    const validExts = ['json', 'csv', 'zip'];
    if (!validExts.includes(fileExt)) {
        showErrorMessage(`Formato de arquivo inválido. Formatos suportados: ${validExts.join(', ')}`);
        input.value = '';
        return;
    }
    
    // Verifica o tamanho do arquivo
    const maxSize = fileExt === 'zip' ? 50 : 10; // 50MB para ZIP, 10MB para outros
    if (fileSize > maxSize) {
        showErrorMessage(`O arquivo é muito grande (${fileSize.toFixed(2)}MB). Tamanho máximo: ${maxSize}MB`);
        input.value = '';
        return;
    }
    
    // Mostra informações sobre o arquivo
    showFileInfo(file);
}

/**
 * Manipula o clique no botão de exportação
 */
function handleExport() {
    const selectedPages = document.querySelectorAll('.page-checkbox:checked');
    if (selectedPages.length === 0) {
        showErrorMessage('Selecione pelo menos uma página para exportação');
        return;
    }
    
    // Mostra indicador de progresso
    const exportButton = document.getElementById('export-button');
    const originalText = exportButton.innerHTML;
    exportButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exportando...';
    exportButton.disabled = true;
    
    // A exportação real ocorrerá via submit do formulário
    // Este código apenas melhora a experiência do usuário mostrando um indicador de progresso
    
    // Em uma implementação real, poderíamos usar AJAX para monitorar o progresso da exportação,
    // mas como este é um download direto, apenas simulamos o feedback visual
    
    // Restaura o botão após um pequeno atraso
    setTimeout(function() {
        exportButton.innerHTML = originalText;
        exportButton.disabled = false;
    }, 3000);
}

/**
 * Mostra informações sobre o arquivo selecionado
 */
function showFileInfo(file) {
    const infoContainer = document.createElement('div');
    infoContainer.className = 'alert alert-info mt-3';
    infoContainer.id = 'file-info';
    
    const fileSize = (file.size / 1024 / 1024).toFixed(2); // tamanho em MB
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    let message = `
        <h6>Arquivo selecionado:</h6>
        <p><strong>Nome:</strong> ${file.name}</p>
        <p><strong>Tamanho:</strong> ${fileSize} MB</p>
        <p><strong>Tipo:</strong> ${fileExt.toUpperCase()}</p>
    `;
    
    // Adiciona dicas específicas para cada formato
    if (fileExt === 'json') {
        message += '<p><em>Este formato preserva todos os metadados e campos personalizados.</em></p>';
    } else if (fileExt === 'csv') {
        message += '<p><em>Este formato contém apenas campos básicos de página.</em></p>';
    } else if (fileExt === 'zip') {
        message += '<p><em>Este formato inclui arquivos de mídia junto com os dados de página.</em></p>';
    }
    
    infoContainer.innerHTML = message;
    
    // Remove qualquer info existente e adiciona a nova
    const existingInfo = document.getElementById('file-info');
    if (existingInfo) {
        existingInfo.remove();
    }
    
    const fileInput = document.getElementById('import_file');
    fileInput.parentNode.appendChild(infoContainer);
}

/**
 * Mostra uma mensagem de erro
 */
function showErrorMessage(message) {
    const errorContainer = document.createElement('div');
    errorContainer.className = 'alert alert-danger mt-3';
    errorContainer.id = 'file-error';
    errorContainer.innerHTML = message;
    
    // Remove qualquer erro existente e adiciona o novo
    const existingError = document.getElementById('file-error');
    if (existingError) {
        existingError.remove();
    }
    
    const fileInput = document.getElementById('import_file');
    fileInput.parentNode.appendChild(errorContainer);
    
    // Remove a mensagem após 5 segundos
    setTimeout(function() {
        errorContainer.remove();
    }, 5000);
}