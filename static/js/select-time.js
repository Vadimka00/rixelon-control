// Генерация вариантов времени
function generateTimeOptions(pickerId, initialTime) {
    const picker = document.getElementById(pickerId);
    picker.innerHTML = '';
    
    for (let hour = 0; hour < 24; hour++) {
        for (let minute = 0; minute < 60; minute += 15) {
            const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
            const option = document.createElement('div');
            option.className = 'time-option';
            option.textContent = timeString;
            option.dataset.time = timeString;
            
            if (timeString === initialTime) {
                option.style.background = 'rgba(141, 114, 225, 0.4)';
            }
            
            option.addEventListener('click', function() {
                const inputId = pickerId.replace('-picker', '');
                document.getElementById(inputId).value = timeString;
                document.querySelectorAll('.time-picker').forEach(p => p.classList.remove('active'));
            });
            
            picker.appendChild(option);
        }
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    // Установка начального времени
    const startTime = '09:00';
    const endTime = '10:00';
    
    document.getElementById('time-start').value = startTime;
    document.getElementById('time-end').value = endTime;
    
    // Генерация вариантов
    generateTimeOptions('time-start-picker', startTime);
    generateTimeOptions('time-end-picker', endTime);
    
    // Обработчики кликов
    document.querySelectorAll('.time-input-field').forEach(input => {
        input.addEventListener('click', function() {
            const pickerId = this.parentElement.querySelector('.time-picker').id;
            document.querySelectorAll('.time-picker').forEach(p => {
                if (p.id === pickerId) {
                    p.classList.toggle('active');
                } else {
                    p.classList.remove('active');
                }
            });
        });
    });
    
    // Закрытие при клике вне
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.time-input')) {
            document.querySelectorAll('.time-picker').forEach(p => p.classList.remove('active'));
        }
    });
});