document.getElementById('newsletterForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const button = this.querySelector('button');
    const formData = new FormData(this);

    try {
        button.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
        button.disabled = true;

        const response = await fetch('{% url "newsletter_signup" %}', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': '{{ csrf_token }}'
            }
        });

        const data = await response.json();

        if (data.status === 'success') {
            button.innerHTML = '<i class="fas fa-check me-2"></i>Inscrit!';
            this.reset();

            // Mostra mensagem de sucesso
            const alert = document.createElement('div');
            alert.className = 'alert alert-success mt-3';
            alert.innerHTML = data.message;
            this.appendChild(alert);

            setTimeout(() => {
                alert.remove();
            }, 5000);
        } else {
            throw new Error(data.message);
        }

    } catch (error) {
        button.innerHTML = '<i class="fas fa-times me-2"></i>Erreur';
        
        // Mostra mensagem de erro
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger mt-3';
        alert.innerHTML = error.message;
        this.appendChild(alert);

        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    setTimeout(() => {
        button.innerHTML = '<i class="fas fa-paper-plane me-2"></i>S\'inscrire';
        button.disabled = false;
    }, 3000);
});