/**
 * main.js - JavaScript principal para o sistema de CMS
 */

document.addEventListener('DOMContentLoaded', function () {
  // Inicialização de tooltips e popovers do Bootstrap
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  var popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Lightbox para galerias de imagens
  if (typeof Lightbox !== 'undefined') {
    Lightbox.option({
      resizeDuration: 200,
      wrapAround: true,
      albumLabel: '%1 / %2',
    });
  }

  // Animação para fade-out de mensagens de alerta
  setTimeout(function () {
    document
      .querySelectorAll('.alert:not(.alert-important)')
      .forEach(function (alert) {
        var bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      });
  }, 5000);

  // Confirmação para ações de exclusão
  document.querySelectorAll('.confirm-delete').forEach(function (button) {
    button.addEventListener('click', function (e) {
      if (
        !confirm(
          'Tem certeza que deseja excluir este item? Esta ação não pode ser desfeita.'
        )
      ) {
        e.preventDefault();
        return false;
      }
    });
  });

  // Carregamento dinâmico de campos personalizados com base no template selecionado
  const templateSelect = document.getElementById('id_template');
  if (templateSelect) {
    templateSelect.addEventListener('change', function () {
      const templateId = this.value;
      const pageId =
        document.querySelector('input[name="page_id"]')?.value || '';

      if (templateId) {
        // Redireciona para a mesma página com o novo template selecionado
        window.location.href =
          window.location.pathname +
          '?template=' +
          templateId +
          '&change_template=1' +
          (pageId ? '&page_id=' + pageId : '');
      }
    });
  }

  // Inicialização do contador de caracteres para campos com limite
  document.querySelectorAll('[data-max-length]').forEach(function (element) {
    const maxLength = parseInt(element.getAttribute('data-max-length'), 10);
    const counterId = element.getAttribute('data-counter-id');
    const counter = document.getElementById(counterId);

    if (counter) {
      // Atualiza o contador inicialmente
      counter.textContent = element.value.length + ' / ' + maxLength;

      // Atualiza o contador ao digitar
      element.addEventListener('input', function () {
        counter.textContent = element.value.length + ' / ' + maxLength;

        // Alerta visual quando ultrapassa o limite
        if (element.value.length > maxLength) {
          counter.classList.add('text-danger');
        } else {
          counter.classList.remove('text-danger');
        }
      });
    }
  });

  // Tratamento para requisições AJAX
  document.querySelectorAll('.ajax-action').forEach(function (element) {
    element.addEventListener('click', function (e) {
      e.preventDefault();

      const url = this.getAttribute('href') || this.getAttribute('data-url');
      const method = this.getAttribute('data-method') || 'GET';
      const confirmMessage = this.getAttribute('data-confirm');

      if (confirmMessage && !confirm(confirmMessage)) {
        return false;
      }

      // Mostra indicador de carregamento
      const loadingSpinner = document.createElement('span');
      loadingSpinner.className = 'spinner-border spinner-border-sm ms-2';
      loadingSpinner.setAttribute('role', 'status');
      loadingSpinner.innerHTML =
        '<span class="visually-hidden">Carregando...</span>';
      this.appendChild(loadingSpinner);
      this.classList.add('disabled');

      // Realiza a requisição AJAX
      fetch(url, {
        method: method,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrfToken(),
        },
      })
        .then((response) => response.json())
        .then((data) => {
          // Remove o indicador de carregamento
          loadingSpinner.remove();
          this.classList.remove('disabled');

          // Trata a resposta
          if (data.status === 'success') {
            // Exibe mensagem de sucesso
            showNotification(
              'success',
              data.message || 'Operação realizada com sucesso.'
            );

            // Atualiza elementos ou recarrega a página, se necessário
            if (data.redirect) {
              window.location.href = data.redirect;
            } else if (data.reload) {
              window.location.reload();
            } else if (data.update_element) {
              document.querySelector(data.update_element.selector).innerHTML =
                data.update_element.content;
            }
          } else {
            // Exibe mensagem de erro
            showNotification(
              'danger',
              data.message || 'Ocorreu um erro na operação.'
            );
          }
        })
        .catch((error) => {
          // Remove o indicador de carregamento
          loadingSpinner.remove();
          this.classList.remove('disabled');

          // Exibe mensagem de erro
          showNotification('danger', 'Erro de comunicação com o servidor.');
          console.error('Erro:', error);
        });
    });
  });

  // Função para obter o token CSRF
  function getCsrfToken() {
    return document
      .querySelector('meta[name="csrf-token"]')
      .getAttribute('content');
  }

  // Função para exibir notificações
  window.showNotification = function (type, message) {
    const container = document.createElement('div');
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1050';

    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-white bg-${type} border-0`;
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');

    toastElement.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

    container.appendChild(toastElement);
    document.body.appendChild(container);

    const toast = new bootstrap.Toast(toastElement, {
      autohide: true,
      delay: 5000,
    });

    toast.show();

    // Remove o elemento após o fechamento
    toastElement.addEventListener('hidden.bs.toast', function () {
      container.remove();
    });
  };

  // Manipulação de menus aninhados
  const dropdownMenus = document.querySelectorAll('.dropdown-menu');
  dropdownMenus.forEach(function (menu) {
    const dropdownLinks = menu.querySelectorAll(
      '.dropdown-item.dropdown-toggle'
    );
    dropdownLinks.forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        const subMenu = this.nextElementSibling;
        if (subMenu && subMenu.classList.contains('dropdown-menu')) {
          // Fecha outros submenus
          menu.querySelectorAll('.dropdown-menu').forEach(function (sub) {
            if (sub !== subMenu) {
              sub.classList.remove('show');
            }
          });

          // Alterna a visibilidade do submenu
          subMenu.classList.toggle('show');

          // Posiciona o submenu
          if (subMenu.classList.contains('show')) {
            const rect = this.getBoundingClientRect();
            subMenu.style.top = rect.top + 'px';
            subMenu.style.left = rect.right + 'px';
          }
        }
      });
    });
  });

  // Fecha submenus ao clicar fora
  document.addEventListener('click', function (e) {
    const subMenus = document.querySelectorAll(
      '.dropdown-menu .dropdown-menu.show'
    );
    if (subMenus.length > 0 && !e.target.closest('.dropdown-menu')) {
      subMenus.forEach(function (menu) {
        menu.classList.remove('show');
      });
    }
  });
});

// Conteúdo de custom.js
document.addEventListener('DOMContentLoaded', function () {
  const header = document.getElementById('main-header');

  function toggleHeaderBackground() {
    if (window.scrollY > 50) {
      header.classList.remove('transparent');
      header.classList.add('scrolled');
    } else {
      header.classList.add('transparent');
      header.classList.remove('scrolled');
    }
  }

  window.addEventListener('scroll', toggleHeaderBackground);
  toggleHeaderBackground(); // Call once to set initial state
});

// Conteúdo original de main.js
// Função para inicializar os componentes da página
function initPage() {
  console.log('Página inicializada');
  // Adicione aqui a lógica de inicialização da página
}

$(document).ready(function () {
  $('.testimonial-carousel').slick({
    dots: true,
    infinite: true,
    speed: 300,
    slidesToShow: 1,
    adaptiveHeight: true,
    autoplay: true,
    autoplaySpeed: 5000,
  });
});

// Executar a função de inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', initPage);
