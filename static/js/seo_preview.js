document.addEventListener('DOMContentLoaded', function () {
  // Função para atualizar o preview de busca
  function updateSearchPreview() {
    const title =
      document.getElementById('id_meta_title').value ||
      document.getElementById('id_title').value;
    const description = document.getElementById('id_meta_description').value;
    const url = window.location.origin + '/page-url/'; // Substitua com a lógica real de URL

    document.getElementById('search-preview-title').textContent = title;
    document.getElementById('search-preview-url').textContent = url;
    document.getElementById('search-preview-description').textContent =
      description;
  }

  // Função para atualizar o preview de compartilhamento social
  function updateSocialPreview() {
    const title =
      document.getElementById('id_og_title').value ||
      document.getElementById('id_title').value;
    const description =
      document.getElementById('id_og_description').value ||
      document.getElementById('id_meta_description').value;
    const image = document.getElementById('id_og_image').value;

    document.getElementById('social-preview-title').textContent = title;
    document.getElementById('social-preview-description').textContent =
      description;
    if (image) {
      document.getElementById('social-preview-image').src = image;
      document.getElementById('social-preview-image').style.display = 'block';
    } else {
      document.getElementById('social-preview-image').style.display = 'none';
    }
  }

  // Adicionar event listeners para campos relevantes
  const seoFields = [
    'id_meta_title',
    'id_meta_description',
    'id_og_title',
    'id_og_description',
    'id_og_image',
  ];
  seoFields.forEach((fieldId) => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.addEventListener('input', function () {
        updateSearchPreview();
        updateSocialPreview();
      });
    }
  });

  // Inicializar previews
  updateSearchPreview();
  updateSocialPreview();
});
