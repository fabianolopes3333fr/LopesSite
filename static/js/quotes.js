// Manipulação do formulário de orçamento
document.addEventListener('DOMContentLoaded', function() {
    // Máscara para telefone
    const phoneInput = document.querySelector('input[name="phone"]');
    if (phoneInput) {
        const phoneRegex = /^(\+33|0)[1-9](\d{2}){4}$/;
        
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) value = value.slice(0, 10);
            
            let formattedValue = '';
            for (let i = 0; i < value.length; i++) {
                if (i === 0) formattedValue += '0';
                if (i % 2 === 0 && i !== 0) formattedValue += ' ';
                formattedValue += value[i];
            }
            
            e.target.value = formattedValue;
        });
    }

    // Upload de fotos com preview
    const photoInput = document.querySelector('input[name="reference_photos"]');
    const previewContainer = document.querySelector('.photo-preview');
    
    if (photoInput && previewContainer) {
        photoInput.addEventListener('change', function(e) {
            previewContainer.innerHTML = '';
            
            [...e.target.files].forEach(file => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.createElement('div');
                    preview.className = 'photo-preview-item';
                    preview.innerHTML = `
                        <img src="${e.target.result}" alt="Preview">
                        <button type="button" class="remove-photo">×</button>
                    `;
                    previewContainer.appendChild(preview);
                }
                reader.readAsDataURL(file);
            });
        });
    }

    // Cálculo automático de estimativa
    const areaInput = document.querySelector('input[name="area_size"]');
    const serviceSelect = document.querySelector('select[name="service_type"]');
    const estimateDisplay = document.querySelector('.estimate-display');
    
    if (areaInput && serviceSelect && estimateDisplay) {
        const calculateEstimate = () => {
            const area = parseFloat(areaInput.value) || 0;
            const service = serviceSelect.value;
            
            let basePrice = 0;
            switch(service) {
                case 'interior': basePrice = 25; break;
                case 'exterior': basePrice = 30; break;
                case 'commercial': basePrice = 35; break;
                case 'industrial': basePrice = 40; break;
                case 'decorative': basePrice = 45; break;
            }
            
            const estimate = area * basePrice;
            estimateDisplay.textContent = `Estimation: ${estimate.toFixed(2)}€`;
        };
        
        areaInput.addEventListener('input', calculateEstimate);
        serviceSelect.addEventListener('change', calculateEstimate);
    }
});