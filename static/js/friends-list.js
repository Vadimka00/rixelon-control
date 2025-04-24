function friendsOpenContainer() {
    const container = document.querySelector('.friends-list-container');
    container.style.display = 'flex';
    container.style.position = 'fixed';
    document.body.style.overflow = 'hidden';
    
    fetch('/friends')
      .then(response => response.json())
      .then(data => {
        const friendsContainer = document.getElementById('friendsContainer');
        const ul = friendsContainer.querySelector('ul');
        ul.innerHTML = '';
        
        if (data.friends.length === 0 && 
            data.outgoing_requests.length === 0 && 
            data.incoming_requests.length === 0) {
          ul.innerHTML = '<p>Список пуст</p>';
          return;
        }
        
        // Добавляем друзей
        data.friends.forEach((friend, index) => {
          const li = document.createElement('li');
          li.className = 'friend' + (index === data.friends.length - 1 ? ' end' : '');
          li.innerHTML = `
            <div class="friend-avatar">
              <img src="${friend.photo}" alt="${friend.name}">
            </div>
            <div class="friend-name">
              <span>${friend.name}</span>
              <span class="friend-username">@${friend.username}</span>
            </div>
          `;
          ul.appendChild(li);
        });
        
        // Добавляем исходящие запросы (Отправлено)
        data.outgoing_requests.forEach((request, index) => {
          const li = document.createElement('li');
          li.className = 'friend' + (index === data.outgoing_requests.length - 1 ? ' end' : '');
          li.innerHTML = `
            <div class="friend-avatar">
              <img src="${request.photo}" alt="${request.name}">
            </div>
            <div class="friend-name">
              <span>${request.name}</span>
              <span class="friend-username">@${request.username}</span>
            </div>
            <button class="friend-request sent">Отправлено</button>
          `;
          ul.appendChild(li);
        });
        
        // Добавляем входящие запросы (Принять)
        data.incoming_requests.forEach((request, index) => {
          const li = document.createElement('li');
          li.className = 'friend request' + (index === data.incoming_requests.length - 1 ? ' end' : '');
          li.innerHTML = `
            <div class="friend-avatar">
              <img src="${request.photo}" alt="${request.name}">
            </div>
            <div class="friend-name">
              <span>${request.name}</span>
              <span class="friend-username">@${request.username}</span>
            </div>
            <button class="friend-request accept" 
                    data-request-id="${request.telegram_id}">
              Принять
            </button>
            <button class="friend-request reject" 
                    data-request-id="${request.telegram_id}">
              Принять
            </button>
          `;
          ul.appendChild(li);
        });
        
        // Добавляем обработчики для кнопок "Принять"
        document.querySelectorAll('.friend-request.accept').forEach(button => {
          button.addEventListener('click', function() {
            const userId = this.getAttribute('data-request-id');
            acceptFriendRequest(userId);
          });
        });
        // Добавляем обработчики для кнопок "Отклонить"
        document.querySelectorAll('.friend-request.reject').forEach(button => {
            button.addEventListener('click', function() {
              const userId = this.getAttribute('data-request-id');
              rejectFriendRequest(userId);
            });
          });
      })
      .catch(error => {
        console.error('Error loading friends:', error);
      });
}

function acceptFriendRequest(userId) {
    fetch('/accept_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({
            user_id: userId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            friendsOpenContainer(); // Обновляем список
        }
    })
    .catch(error => console.error('Error:', error));
}

function rejectFriendRequest(userId) {
    fetch('/reject_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({
            user_id: userId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            friendsOpenContainer(); // Обновляем список
        }
    })
    .catch(error => console.error('Error:', error));
}
