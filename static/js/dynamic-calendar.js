document.addEventListener('DOMContentLoaded', () => {
  let currentDate = new Date();
  let selectedDate = null;
  
  function initCalendar() {
    renderCalendar(currentDate.getFullYear(), currentDate.getMonth());
    setupNavigation();
    loadAllTasks();
  }

  window.initCalendar = initCalendar;

  async function loadAllTasks() {
    try {
      const response = await fetch('/tasks-main');
      const tasks = await response.json();
      processTasks(tasks);
    } catch (error) {
      console.error('Ошибка загрузки задач:', error);
    }
  }

  function processTasks(tasks) {
    // Группируем задачи по датам
    const tasksByDate = tasks.reduce((acc, task) => {
      const dateKey = formatDate(new Date(task.task_date));
      if (!acc[dateKey]) acc[dateKey] = [];
      acc[dateKey].push(task);
      return acc;
    }, {});

    // Обрабатываем каждую дату
    Object.entries(tasksByDate).forEach(([date, tasks]) => {
      const tasksContainer = document.querySelector(`.tasks[data-date="${date}"]`);
      if (!tasksContainer) return;

      tasksContainer.innerHTML = '';
      tasks.forEach((task, index) => {
        const taskElement = createTaskElement(task, index, tasks.length);
        tasksContainer.appendChild(taskElement);
      });
    });
  }

  function formatDate(date) {
    return [
      String(date.getDate()).padStart(2, '0'),
      String(date.getMonth() + 1).padStart(2, '0'),
      date.getFullYear()
    ].join('.');
  }

  function createTaskElement(task, index, totalTasks) {
    const isLast = index === totalTasks - 1;
    const li = document.createElement('li');
    li.className = `task-list${isLast ? ' end' : ''}`;
    
    const hasCategory = task.category_filter && task.category;
    const hasCollaborator = task.collaborator_info;
    
    const startTime = task.start_time ? task.start_time.slice(0, 5) : '';
    const endTime = task.end_time ? task.end_time.slice(0, 5) : '';

    let taskHTML = `
      <div class="task-main">
        <div class="time">
          <span class="time-start">${startTime}</span>
          <span class="time-end">${endTime}</span>
        </div>
        <div class="task-status${hasCategory ? ` ${task.category_filter}` : ' status'}">`;

    if (hasCategory) {
      taskHTML += `
        ${hasCollaborator ? '<i class="fa-solid fa-user-group" title="Совместная задача"></i>' : ''}
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

    li.innerHTML = taskHTML;
    return li;
  }

  function renderCalendar(year, month) {
    const calendarGrid = document.getElementById("calendar-grid");
    calendarGrid.innerHTML = '';
    
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const monthName = new Intl.DateTimeFormat('ru-RU', { 
      month: 'long' 
    }).format(new Date(year, month));
    
    const currentMonth = document.getElementById('current-month');
    currentMonth.textContent = `${monthName[0].toUpperCase() + monthName.slice(1)} ${year}`;

    const monthDiv = document.createElement('div');
    monthDiv.className = 'month';
    calendarGrid.appendChild(monthDiv);

    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const weekDays = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
      const formattedDate = formatDate(date);
      
      const dayHTML = `
        <div class="day-task" data-date="${formattedDate}" onclick="taskAddContainer(this)">
          <div class="day-header">
            <span class="date">${formattedDate}</span>
            <span class="weekday">${weekDays[date.getDay()]}</span>
          </div>
          <ul class="tasks" data-date="${formattedDate}"></ul>
        </div>
      `;
      
      monthDiv.insertAdjacentHTML('beforeend', dayHTML);
    }
  }

  // Остальные функции остаются без изменений
  function changeMonth(offset) {
    currentDate.setMonth(currentDate.getMonth() + offset);
    renderCalendar(currentDate.getFullYear(), currentDate.getMonth());
    loadAllTasks(); // Обновляем задачи при смене месяца
  }

  function setupNavigation() {
    document.getElementById('prev-month').addEventListener('click', () => changeMonth(-1));
    document.getElementById('next-month').addEventListener('click', () => changeMonth(1));
  }

  initCalendar();
});