document.addEventListener('DOMContentLoaded', function() {
    const emailInput = document.getElementById('emailInput');
    const authButton = document.querySelector('.auth-button');

    // Запрет неанглийских символов
    emailInput.addEventListener('keydown', function(e) {
        const allowedChars = /^[a-zA-Z0-9@._-]$/;
        if (!allowedChars.test(e.key) && e.key !== 'Backspace') {
            e.preventDefault();
        }
});

    // Проверка в реальном времени
    emailInput.addEventListener('input', function() {
        // Удаляем все неанглийские символы
        this.value = this.value.replace(/[^a-zA-Z0-9@._-]/g, '');
        
        const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        const isValid = emailRegex.test(this.value);
        
        if(isValid) {
            authButton.style.display = 'block';
            authButton.classList.add('active');
        } else {
            authButton.classList.remove('active');
            // Убираем transitionend для мгновенного скрытия
            authButton.style.display = 'none';
        }
    });
});

document.querySelector('.auth-button').addEventListener('click', async () => {
    const email = document.getElementById('emailInput').value;
    const authContainer = document.querySelector('.auth-container');

    try {
        const response = await fetch('/check_email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content // Получаем токен из мета-тега
            },
            body: JSON.stringify({email})
        });

        const data = await response.json();
        authContainer.dataset.tempEmail = email;
        
        switch(data.status) {
            case 'confirmation':
                authContainer.innerHTML = `
                    <div class="reg-content active">
                        <h2>Авторизация</h2>
                        <p>На ваш телеграм отправлен проверочный код от Rixelon Bot</p>
                        <div class="code-container">
                            <label>Введите 6-значный код</label>
                            <div class="code-inputs">
                                ${Array.from({length: 6}, (_, i) => `
                                    <input type="text" 
                                           maxlength="1" 
                                           class="code-digit" 
                                           data-index="${i + 1}"
                                           inputmode="numeric">
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
                initCodeInputs();
                break;

            case 'not_found':
                authContainer.innerHTML = `
                    <div class="reg-content active">
                        <h2>Регистрация</h2>
                        <p>Запустите <a href="https://t.me/rixelon_bot?start=AUTH=${data.email_code}" target="_blank">Telegram бота</a> <br>и введите код:</p>
                        <div class="code-container">
                            <label>Введите 6-значный код</label>
                            <div class="code-inputs">
                                ${Array.from({length: 6}, (_, i) => `
                                    <input type="text" 
                                           maxlength="1" 
                                           class="code-digit" 
                                           data-index="${i + 1}"
                                           inputmode="numeric">
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
                initCodeInputs();
                break;

            case 'error':
                console.error('Server error:', data.message);
                break;
        }
    } catch (error) {
        console.error('Network error:', error);
    }
});

function initCodeInputs() {
    const inputs = document.querySelectorAll('.code-digit');
    
    inputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Фильтрация только цифр
            this.value = this.value.replace(/\D/g, '');
            
            // Добавляем обводку при вводе
            if(this.value.length > 0) {
                this.classList.add('active');
            } else {
                this.classList.remove('active');
            }
            
            // Автопереход к следующему полю
            if(this.value.length === 1) {
                const nextIndex = parseInt(this.dataset.index) + 1;
                const nextInput = document.querySelector(`[data-index="${nextIndex}"]`);
                if(nextInput) {
                    nextInput.focus();
                } else {
                    submitCode();
                }
            }
        });

        input.addEventListener('keydown', function(e) {
            // Обработка Backspace
            if(e.key === 'Backspace' && this.value === '') {
                const prevIndex = parseInt(this.dataset.index) - 1;
                const prevInput = document.querySelector(`[data-index="${prevIndex}"]`);
                if(prevInput) prevInput.focus();
            }
        });
    });
}

async function submitCode() {
    const authContainer = document.querySelector('.auth-container');
    const codeInputs = document.querySelectorAll('.code-digit');
    const code = Array.from(codeInputs).map(input => input.value).join('');
    
    if(code.length !== 6) return;

    try {
        const email = document.querySelector('.auth-container').dataset.tempEmail;
        const response = await fetch('/verify_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content // Токен для второго запроса
            },
            body: JSON.stringify({email, code})
        });

        const result = await response.json();
        
        if(result.success) {
            window.location.href = '/dashboard';
            authContainer.classList.remove('active');
        } else {
            // Анимация тряски
            codeInputs.forEach(input => {
                input.classList.add('shake-animation');
                input.classList.remove('active');
                setTimeout(() => {
                    input.classList.remove('shake-animation');
                }, 400);
            });
            setTimeout(() => {
                // Очистка полей
                codeInputs.forEach(input => input.value = '');
                codeInputs[0].focus();
            }, 1000);
        }
    } catch (error) {
        console.error('Ошибка при проверке кода:', error);
    }
}