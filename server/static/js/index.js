// Get current page URL path
const currentPath = window.location.pathname;

// Get all nav links
const navLinks = document.querySelectorAll('.nav-link');

// Remove active class from all links
navLinks.forEach(link => {
    link.classList.remove('active');
});

// Add active class to current page link
navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href && currentPath.includes(href)) {
        link.classList.add('active');
    }
});


// fonction show password
function showPassword() {
    const passwordInput = document.getElementById('password');
    const passwordToggle = document.getElementById('password-toggle');
    const passwordConfirmInput = document.getElementById('password_confirm');
    const passwordConfirmToggle = document.getElementById('password_confirm-toggle');
    const eyeIcons = document.querySelectorAll('.fa-eye');

    passwordToggle.addEventListener('click', function() {
        passwordInput.type = passwordInput.type === 'password' ? 'text' : 'password';
        eyeIcons[0].classList.toggle('fa-eye-slash');
        eyeIcons[0].classList.toggle('fa-eye');
    });

    passwordConfirmToggle.addEventListener('click', function() {
        passwordConfirmInput.type = passwordConfirmInput.type === 'password' ? 'text' : 'password';
        eyeIcons[1].classList.toggle('fa-eye-slash');
        eyeIcons[1].classList.toggle('fa-eye');
    });
}


// dropdown menu

document.addEventListener('DOMContentLoaded', function() {
    // Get all dropdown toggles
    const dropdownToggles = document.querySelectorAll('[data-bs-toggle="collapse"]');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            // Prevent default behavior
            e.preventDefault();
            
            // Get the target submenu
            const targetSubmenu = document.querySelector(this.getAttribute('data-bs-target'));
            
            // Close all other submenus
            document.querySelectorAll('.collapse').forEach(submenu => {
                if (submenu !== targetSubmenu && submenu.classList.contains('show')) {
                    submenu.classList.remove('show');
                }
            });
            
            // Toggle the clicked submenu
            targetSubmenu.classList.toggle('show');
        });
    });
});



