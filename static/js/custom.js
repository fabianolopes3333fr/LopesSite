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