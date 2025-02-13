 // Conteúdo de custom.js
 document.addEventListener('DOMContentLoaded', function() {
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