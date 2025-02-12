// Função para inicializar os componentes da página
function initPage() {
    console.log('Página inicializada');
    // Adicione aqui a lógica de inicialização da página
}
$(document).ready(function(){
    $('.testimonial-carousel').slick({
        dots: true,
        infinite: true,
        speed: 300,
        slidesToShow: 1,
        adaptiveHeight: true,
        autoplay: true,
        autoplaySpeed: 5000
    });
});

// Executar a função de inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', initPage);