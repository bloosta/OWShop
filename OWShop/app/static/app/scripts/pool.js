const button = document.querySelector('.submit-button');
const inputs = document.querySelectorAll('.feedback-form input, .feedback-form textarea, .feedback-form select');

// Изменение цвета текста кнопки при наведении
button.addEventListener('mouseover', () => {
    button.style.backgroundColor = '#333';
    button.style.color = 'white';
});

button.addEventListener('mouseout', () => {
    button.style.backgroundColor = '#222';
    button.style.color = 'white';
});

// Изменение цвета фона полей ввода при фокусе И при наведении
inputs.forEach(input => {
    input.addEventListener('focus', () => {
        input.style.backgroundColor = '#f0f0f0';
    });

    input.addEventListener('blur', () => {
        input.style.backgroundColor = 'white';
    });

    input.addEventListener('mouseover', () => {
        input.style.backgroundColor = '#e0e0e0'; // Более светлый оттенок для наведения
    });

    input.addEventListener('mouseout', () => {
        input.style.backgroundColor = 'white'; // Возврат к исходному цвету
    });
});