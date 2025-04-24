function searchFriends() {
    const query = document.getElementById('searchInput').value.trim();

    if (query.length === 0) {
        document.getElementById('searchResults').innerHTML = "";
        return;
    }

    fetch(`/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            const resultsDiv = document.getElementById('searchResults');
            resultsDiv.innerHTML = '';

            if (data.length === 0) {
                resultsDiv.innerHTML = '<div class="search-item"><span>Ничего не найдено</span></div>';
            } else {
                data.forEach(friend => {
                    const item = document.createElement('div');
                    item.classList.add('search-item');

                    const buttonText = friend.requested ? 'Отправлено' : 'Добавить';
                    const buttonDisabled = friend.requested ? 'disabled' : '';

                    item.innerHTML = `
                        <div class="search-item-user">
                            <img src="${friend.photo}" alt="avatar" class="avatar">
                            <span>${friend.full_name}</span>
                            <span class="search-username">@${friend.username}</span>
                        </div>
                        <button class="friend-add" 
                                data-telegram-id="${friend.telegram_id}" 
                                ${buttonDisabled}>
                            ${buttonText}
                        </button>
                    `;
                    resultsDiv.appendChild(item);
                });

                document.querySelectorAll('.friend-add:not([disabled])').forEach(button => {
                    button.addEventListener('click', () => {
                        const telegramId = button.getAttribute('data-telegram-id');
                        console.log('Sending request with telegram_id:', telegramId);  // Логируем значение
                        button.disabled = true;
                        button.textContent = 'Отправлено';

                        fetch('/add_friend', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                            },
                            body: JSON.stringify({ telegram_id: telegramId })
                        })
                        .then(async response => {
                            if (!response.ok) {
                                const text = await response.text();  // Попытка получить ответ как текст, а не JSON
                                console.error("Server error:", response.status, response.statusText);
                                console.error("Response body:", text);  // Тут будет виден HTML ошибки
                                return;
                            }
                            const data = await response.json();
                            if (data.success) {
                                console.log("Friend request sent successfully");
                            } else {
                                console.log("Server returned error:", data.error);
                            }
                        })
                        .catch(error => {
                            console.error("Request failed:", error);
                        });
                        
                        
                    });
                });
            }
        });
}
