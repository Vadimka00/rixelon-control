window.addEventListener('DOMContentLoaded', () => {
    fetch('/friend-tasks')
      .then(response => response.json())
      .then(data => {
        const friendInput = document.getElementById('friend-select');
        const friendPicker = document.getElementById('friend-picker');
        const friendList = document.querySelector('.friends-list');
  
        // Отображение списка друзей при клике
        friendInput.addEventListener('click', () => {
          friendPicker.style.display = friendPicker.style.display === 'block' ? 'none' : 'block';
        });
  
        // Закрытие списка при клике вне
        document.addEventListener('click', (e) => {
          if (!e.target.closest('.friend-el') && !e.target.closest('#friend-select')) {
            friendPicker.style.display = 'none';
          }
        });
  
        // Добавляем друзей
        function renderFriends(friends) {
          friendList.innerHTML = '';
  
          if (friends.length === 0) {
            const li = document.createElement('li');
            li.className = 'no-friends';
            li.innerHTML = `<div class="no-friends-message">У тебя пока нет друзей</div>`;
            friendList.appendChild(li);
            return;
          }
  
          friends.forEach(friend => {
            const li = document.createElement('li');
            li.className = 'friends friend-el';
            li.setAttribute('data-friend-id', friend.telegram_id);
  
            li.innerHTML = `
              <div class="friend-name">${friend.name}</div>
            `;
  
            li.addEventListener('click', () => {
              friendInput.value = friend.name;
              friendInput.setAttribute('data-friend-id', friend.telegram_id);
              friendPicker.style.display = 'none';
            });
  
            friendList.appendChild(li);
          });
        }
  
        renderFriends(data.friends);
      });
  });
  