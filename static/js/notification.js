function notificationList() {
    fetch('/notifications')
    .then(response => response.json())
    .then(notifications => {
        const notificationContainer = document.getElementById('notif-content');
        notificationContainer.innerHTML = '';
        
        notifications.forEach(notification => {
            let notifElement;
            
            if (notification.title === 'Заявка в друзья') {
                notifElement = createFriendRequestNotification(notification);
            } else if (notification.title === 'Заявка принята') {
                notifElement = createFriendRequestAcceptedNotification(notification);
            } else {
                notifElement = createDefaultNotification(notification);
            }
            
            notificationContainer.appendChild(notifElement);
        });
    })
    .catch(error => console.error('Error fetching notifications:', error));
}

function createFriendRequestNotification(notification) {
    const notifDiv = document.createElement('div');
    notifDiv.className = 'notif';
    
    notifDiv.innerHTML = `
        <div class="notif-header">
            <div class="notif-icon">
                <i class="fa-solid fa-user-group"></i>
            </div>
            <h3 class="notif-name">${notification.title}</h3>
        </div>
        <div class="notif-body">
            <p>Привет у тебя новая заявка в друзья от <span class="notif-friend-name">${notification.sender_name || 'Неизвестный пользователь'}</span>!</p>
        </div>
        <div class="notif-footer">
            <button class="friend-accept button-class" data-from-id="${notification.from_telegram_id}">Принять</button>
            <button class="friend-reject button-class" data-from-id="${notification.from_telegram_id}">Отклонить</button>
        </div>
    `;
    
    return notifDiv;
}

function createFriendRequestAcceptedNotification(notification) {
    const notifDiv = document.createElement('div');
    notifDiv.className = 'notif';
    
    notifDiv.innerHTML = `
        <div class="notif-header">
            <div class="notif-icon">
                <i class="fa-solid fa-user-group"></i>
            </div>
            <h3 class="notif-name">${notification.title}</h3>
        </div>
        <div class="notif-body">
            <p><span class="notif-friend-name">${notification.sender_name || 'Неизвестный пользователь'}</span> принял вашу заявку в друзья!</p>
        </div>
        <div class="notif-footer">
        </div>
    `;
    
    return notifDiv;
}

function createDefaultNotification(notification) {
    const notifDiv = document.createElement('div');
    notifDiv.className = 'notif';
    
    notifDiv.innerHTML = `
        <div class="notif-header">
            <div class="notif-icon">
                <i class="fa-solid fa-bell"></i>
            </div>
            <h3 class="notif-name">${notification.title}</h3>
        </div>
        <div class="notif-body">
            <p>${notification.message}</p>
        </div>
        <div class="notif-footer">
            <small>${new Date(notification.timestamp).toLocaleString()}</small>
        </div>
    `;
    
    return notifDiv;
}

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('friend-accept')) {
        const fromTelegramId = e.target.getAttribute('data-from-id');
        acceptFriendRequest(fromTelegramId);
        console.log('Принята заявка от:', fromTelegramId);
    }
    
    if (e.target.classList.contains('friend-reject')) {
        const fromTelegramId = e.target.getAttribute('data-from-id');
        rejectFriendRequest(fromTelegramId);
        console.log('Отклонена заявка от:', fromTelegramId);
    }
});

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
            notificationList(); // Обновляем список
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
            notificationList(); // Обновляем список
        }
    })
    .catch(error => console.error('Error:', error));
}