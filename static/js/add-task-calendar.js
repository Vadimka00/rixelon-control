let currentDate = new Date();
const today = new Date();
const calendarDays = document.querySelector('.days');
const currentMonthElement = document.querySelector('.current-month');
const taskFormContent = document.getElementById('task-form-content');
let taskFormVisible = false;
let showWeekOnly = false;

// Генерация календаря
function generateCalendar(month, year, selectedDate = today, weekOnly = false) {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const prevLastDay = new Date(year, month, 0).getDate();

  calendarDays.innerHTML = '';

  const days = [];

  for (let i = firstDay.getDay() - 1; i >= 0; i--) {
    days.push({
      day: prevLastDay - i,
      otherMonth: true
    });
  }

  for (let i = 1; i <= lastDay.getDate(); i++) {
    days.push({
      day: i,
      otherMonth: false
    });
  }

  const nextDays = 7 - (days.length % 7);
  if (nextDays < 7) {
    for (let i = 1; i <= nextDays; i++) {
      days.push({
        day: i,
        otherMonth: true
      });
    }
  }

  // Фильтрация недели
  let displayDays = days;
  if (weekOnly) {
    const selected = new Date(selectedDate);
    const startOfWeek = new Date(selected);
    startOfWeek.setDate(selected.getDate() - ((selected.getDay() + 6) % 7));
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);

    displayDays = [];

    for (let date = new Date(startOfWeek); date <= endOfWeek; date.setDate(date.getDate() + 1)) {
      const isOtherMonth = date.getMonth() !== month;
      displayDays.push({
        day: date.getDate(),
        otherMonth: isOtherMonth,
        date: new Date(date)
      });
    }
  }

  displayDays.forEach(({ day, otherMonth, date }) => {
    const dayElem = document.createElement('div');
    dayElem.className = 'day';
    dayElem.textContent = day;
  
    // Добавляем атрибут data-date в формате 01.04.2025
    const dayDate = date || new Date(year, month, day);
    const formattedDate = `${String(dayDate.getDate()).padStart(2, '0')}.${String(dayDate.getMonth() + 1).padStart(2, '0')}.${dayDate.getFullYear()}`;
    dayElem.setAttribute('data-date', formattedDate);
  
    if (otherMonth) {
      dayElem.classList.add('other-month');
    }
  
    if (
      dayDate.getDate() === today.getDate() &&
      dayDate.getMonth() === today.getMonth() &&
      dayDate.getFullYear() === today.getFullYear()
    ) {
      dayElem.classList.add('selected');
    }
  
    dayElem.addEventListener('click', () => {
      selectDate(dayDate);
    });
  
    calendarDays.appendChild(dayElem);
  });

  currentMonthElement.textContent = new Date(year, month).toLocaleDateString('ru-RU', {
    month: 'long',
    year: 'numeric'
  }).replace(' г.', '');

  selectDate(selectedDate);
}

// Анимация при смене вида
function fadeCalendar(callback) {
  calendarDays.classList.add('fade-out');
  setTimeout(() => {
    callback();
    calendarDays.classList.remove('fade-out');
  }, 400);
}

// Выбор даты
function selectDate(date) {
  document.querySelectorAll('.day').forEach(day => day.classList.remove('selected'));

  const selectedDay = [...calendarDays.children].find(child =>
    parseInt(child.textContent) === date.getDate() &&
    !child.classList.contains('other-month')
  );

  if (selectedDay) {
    selectedDay.classList.add('selected');
  }

  const isoDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

  fetch(`/tasks?date=${isoDate}`)
    .then(response => response.json())
    .then(data => {
      const tasksList = document.querySelector('.tasks-list');
      tasksList.innerHTML = '';

      if (!data || data.length === 0) {
        tasksList.innerHTML = '<p>Список задач пуст</p>';
        return;
      }

      data.forEach((task, index) => {
        const isLast = index === data.length - 1;
        const hasCategory = task.category_filter;
        const hasCollaborator = task.collaborator_info;

        const startTime = task.start_time.slice(0, 5);
        const endTime = task.end_time.slice(0, 5);

        let taskHTML = `
            <li class="task-list${isLast ? ' end' : ''}">
              <div class="task-main">
                <div class="time">
                  <span class="time-start">${startTime}</span>
                  <span class="time-end">${endTime}</span>
                </div>
                <div class="task-status${hasCategory ? ` ${task.category_filter}` : 'task-status status'}">`;

        if (hasCategory) {
          taskHTML += `${hasCollaborator ? '<i class="fa-solid fa-user-group" title="Совместная задача"></i>' : ''}
                       <p class="task-filter">${task.category}</p>`;
        }

        taskHTML += `
                </div>
                <span class="title">${task.title}</span>
              </div>`;

        if (hasCollaborator) {
          taskHTML += `
              <div class="task-collaborator-content">
                <div class="task-collaborator">
                  <div class="collaborator-avatar">
                    <img src="${task.collaborator_info.photo}" alt="${task.collaborator_info.first_name}">
                  </div>
                  <div class="collaborator-name">
                    ${task.collaborator_info.first_name}
                    ${task.collaborator_info.last_name || ''}
                  </div>
                </div>
              </div>`;
        }

        taskHTML += `</li>`;
        tasksList.insertAdjacentHTML('beforeend', taskHTML);
      });
    })
    .catch(error => console.error('Ошибка загрузки задач:', error));
}

// Обработка интерфейса
document.addEventListener('DOMContentLoaded', () => {
  document.querySelector('.prev-month').addEventListener('click', () => {
    if (showWeekOnly) {
      currentDate.setDate(currentDate.getDate() - 7);
    } else {
      currentDate.setMonth(currentDate.getMonth() - 1);
    }
  
    fadeCalendar(() => generateCalendar(currentDate.getMonth(), currentDate.getFullYear(), currentDate, showWeekOnly));
  });
  
  document.querySelector('.next-month').addEventListener('click', () => {
    if (showWeekOnly) {
      currentDate.setDate(currentDate.getDate() + 7);
    } else {
      currentDate.setMonth(currentDate.getMonth() + 1);
    }
  
    fadeCalendar(() => generateCalendar(currentDate.getMonth(), currentDate.getFullYear(), currentDate, showWeekOnly));
  });
  

  document.getElementById('toggleViewBtn').addEventListener('click', () => {
    showWeekOnly = !showWeekOnly;
    const btn = document.getElementById('toggleViewBtn');
    btn.textContent = showWeekOnly ? 'Показать месяц' : 'Показать неделю';
  
    // Вызов нужной функции
    if (showWeekOnly) {
      showTaskForm();
    } else {
      hideTaskForm();
    }
  
    fadeCalendar(() => generateCalendar(currentDate.getMonth(), currentDate.getFullYear(), currentDate, showWeekOnly));
  });
  
  generateCalendar(currentDate.getMonth(), currentDate.getFullYear(), currentDate, showWeekOnly);
  
});


// Функция открытия формы добавления задачи
function taskAddContainer(element = null) {
  const container = document.querySelector('.add-task-container');
  container.style.display = 'flex';
  container.style.position = 'fixed';
  document.body.style.overflow = 'hidden';

  let date = today; // Значение по умолчанию — сегодняшняя дата

  if (element) {
    const dateStr = element.getAttribute('data-date'); // формат "день.месяц.год"
    if (dateStr) {
      console.log('Дата из атрибута:', dateStr);
      const [day, month, year] = dateStr.split('.').map(Number);
      date = new Date(year, month - 1, day);
    } else {
      console.log('Атрибут data-date не найден. Используется сегодняшняя дата.');
    }
  } else {
    console.log('Элемент не передан. Используется сегодняшняя дата.');
  }

  selectDate(date);
}

function showTaskForm() {
  taskFormContent.style.display = 'flex';
  taskFormVisible = true;
  document.getElementById('toggleViewBtn').disabled = false; // Запрещаем смену режима
}

function hideTaskForm() {
  taskFormContent.style.display = 'none';
  taskFormVisible = false;
  document.getElementById('toggleViewBtn').disabled = false; // Разрешаем смену режима
}

document.getElementById('toggleTaskFormBtn').addEventListener('click', () => {
  if (taskFormVisible) {
    hideTaskForm();
  } else {
    showWeekOnly = !showWeekOnly;
    showTaskForm();
  }
});

