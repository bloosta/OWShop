const button = document.querySelector('.submit-button');
const inputs = document.querySelectorAll('.feedback-form input, .feedback-form textarea, .feedback-form select');

button.addEventListener('mouseover', () => {
    button.style.backgroundColor = '#333';
    button.style.color = 'white';
});

button.addEventListener('mouseout', () => {
    button.style.backgroundColor = '#f99e1a ';
    button.style.color = 'white';
});

inputs.forEach(input => {
    input.addEventListener('focus', () => {
        input.style.backgroundColor = '#f0f0f0';
    });

    input.addEventListener('blur', () => {
        input.style.backgroundColor = 'white';
    });

    input.addEventListener('mouseover', () => {
        input.style.backgroundColor = '#e0e0e0';
    });

    input.addEventListener('mouseout', () => {
        input.style.backgroundColor = 'white';
    });
});