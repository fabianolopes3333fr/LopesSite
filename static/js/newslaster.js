document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('newsletterForm');
    const alert = document.getElementById('newsletterAlert');
    const submitBtn = document.getElementById('newsletterSubmit');

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Desabilita o botão durante o envio
        submitBtn.disabled = true;

        try {
        const response = await fetch(form.dataset.action, {
            method: 'POST',
            headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')
                .value,
            'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams(new FormData(form)),
        });

        const data = await response.json();

        alert.className = `alert alert-${
            data.status === 'success' ? 'success' : 'danger'
        }`;
        alert.textContent = data.message;
        alert.classList.remove('d-none');

        if (data.status === 'success') {
            form.reset();
        }
        } catch (error) {
        alert.className = 'alert alert-danger';
        alert.textContent =
            "{% trans 'Une erreur est survenue. Veuillez réessayer.' %}";
        alert.classList.remove('d-none');
        } finally {
        submitBtn.disabled = false;
        }
    });
});
