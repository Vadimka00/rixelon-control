
document.addEventListener('DOMContentLoaded', () => {
  const timeStart = document.getElementById('time-start');
  const timeEnd = document.getElementById('time-end');
  const descriptionField = document.querySelector('textarea');
  const categoryHeader = document.querySelector('.select-header span');
  const addButton = document.querySelector('.create-tasks-btn');
  const friendInput = document.getElementById('friend-select');

  const categoryMap = {
    'Работа': 'work',
    'Учеба': 'study',
    'Дом': 'home',
    'Здоровье': 'health',
    'Встреча': 'social',
    'Хобби': 'hobby',
    'Сон': 'sleep'
  };

  function checkRequiredFields() {
    const timeStartFilled = timeStart.value.trim() !== '';
    const timeEndFilled = timeEnd.value.trim() !== '';
    const descriptionFilled = descriptionField.value.trim() !== '';
    addButton.disabled = !(timeStartFilled && timeEndFilled && descriptionFilled);
  }

  // Выбор категории
  const categoryOptions = document.querySelectorAll('.select-options .option');
  categoryOptions.forEach(option => {
    option.addEventListener('click', () => {
      categoryHeader.textContent = option.textContent;
      checkRequiredFields();
    });
  });

  timeStart.addEventListener('input', checkRequiredFields);
  timeEnd.addEventListener('input', checkRequiredFields);
  descriptionField.addEventListener('input', checkRequiredFields);

  addButton.addEventListener('click', () => {
    const startTime = timeStart.value.trim();
    const endTime = timeEnd.value.trim();
    const description = descriptionField.value.trim();
    const categoryText = categoryHeader.textContent.trim();
    const category = categoryMap[categoryText] || null;
    const friendId = friendInput.dataset.friendId || null;
  
    // Получаем дату из активного блока
    const activeDay = document.querySelector('.day.selected');
    const taskDate = activeDay ? activeDay.dataset.date : null;

    if (!taskDate) {
      console.error('Дата задачи не выбрана!');
      return;
    }

    // Преобразуем дату из DD.MM.YYYY в YYYY-MM-DD
    const [day, month, year] = taskDate.split('.');
    const formattedDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;

    const taskData = {
      time_start: startTime,
      time_end: endTime,
      description: description,
      category: category,
      friend_id: friendId,
      task_date: formattedDate  // Используем отформатированную дату
    };
  
    console.log('📤 Отправка задачи:', taskData);
  
    fetch('/add/new_task', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
      },
      body: JSON.stringify(taskData)
    })
    .then(response => {
      if (!response.ok) throw new Error('Ошибка при отправке задачи');
      return response.json();
    })
    .then(data => {
      console.log('✅ Ответ сервера:', data);
  
      if (data.status === 'success') {
        // Сброс формы
        timeStart.value = '';
        timeEnd.value = '';
        descriptionField.value = '';
        categoryHeader.textContent = 'Категория';
        friendInput.value = '';
  
        checkRequiredFields(); // Обновляем кнопку
  
        console.log('🧹 Форма очищена после добавления задачи');
      } else {
        console.warn('⚠️ Ответ сервера без статуса "success":', data);
      }
    })
    .catch(error => {
      console.error('❌ Ошибка:', error);
    });
  });
  

  checkRequiredFields();
});