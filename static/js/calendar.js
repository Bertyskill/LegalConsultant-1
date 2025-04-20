/**
 * Календарь мероприятий
 * Скрипт для работы с календарем в системе юридической компании
 */

// Типы мероприятий для календаря
const EVENT_TYPES = {
    MEETING: {
        name: 'Встреча',
        backgroundColor: '#3788d8',
        borderColor: '#2c6faf'
    },
    COURT: {
        name: 'Суд',
        backgroundColor: '#d83737',
        borderColor: '#af2c2c'
    },
    CONSULTATION: {
        name: 'Консультация',
        backgroundColor: '#37d882',
        borderColor: '#2caf6b'
    },
    OTHER: {
        name: 'Прочее',
        backgroundColor: '#6c757d',
        borderColor: '#495057'
    }
};

/**
 * Инициализирует календарь и настраивает его функционал
 * @param {string} calendarElementId - ID HTML элемента для календаря
 * @param {Array} events - Массив событий для отображения
 */
function initCalendar(calendarElementId, events) {
    const calendarEl = document.getElementById(calendarElementId);
    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        locale: 'ru',
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },
        weekNumbers: true,
        navLinks: true,
        editable: true,
        dayMaxEvents: true,
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        },
        events: events,
        eventClick: function(info) {
            showEventDetails(info.event);
        },
        dateClick: function(info) {
            // Можно открыть форму создания события на выбранную дату
            console.log('Clicked on: ' + info.dateStr);
        },
        eventDrop: function(info) {
            // Обработка перетаскивания события
            updateEventDates(info.event.id, info.event.start, info.event.end);
        },
        eventResize: function(info) {
            // Обработка изменения размера события
            updateEventDates(info.event.id, info.event.start, info.event.end);
        }
    });

    calendar.render();
    return calendar;
}

/**
 * Отображает детали события в модальном окне
 * @param {Object} event - Объект события FullCalendar
 */
function showEventDetails(event) {
    const eventModal = new bootstrap.Modal(document.getElementById('eventModal'));
    
    // Заполняем данные о событии
    document.getElementById('eventTitle').textContent = event.title;
    
    // Форматируем дату и время
    const start = event.start;
    const end = event.end;
    let dateTimeStr = '';
    
    if (start) {
        const formattedStart = start.toLocaleString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        dateTimeStr = formattedStart;
        
        if (end) {
            const formattedEnd = end.toLocaleString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit'
            });
            dateTimeStr += ' - ' + formattedEnd;
        }
    }
    
    document.getElementById('eventDateTime').textContent = dateTimeStr;
    document.getElementById('eventLocation').textContent = event.extendedProps.location || 'Не указано';
    document.getElementById('eventDescription').textContent = event.extendedProps.description || 'Описание отсутствует';
    
    // Отображаем информацию об участниках
    const participantsContainer = document.getElementById('eventParticipants');
    participantsContainer.innerHTML = '';
    
    if (event.extendedProps.participants && event.extendedProps.participants.length > 0) {
        const participantsList = document.createElement('ul');
        participantsList.className = 'list-group';
        
        event.extendedProps.participants.forEach(participant => {
            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.textContent = participant.name;
            
            const badge = document.createElement('span');
            badge.className = 'badge rounded-pill bg-primary';
            badge.textContent = participant.role;
            
            item.appendChild(badge);
            participantsList.appendChild(item);
        });
        
        participantsContainer.appendChild(participantsList);
    } else {
        participantsContainer.textContent = 'Участники не указаны';
    }
    
    // Настраиваем кнопку редактирования
    document.getElementById('editEventBtn').onclick = function() {
        window.location.href = `/manager/edit_event/${event.id}`;
    };
    
    eventModal.show();
}

/**
 * Отправляет запрос на обновление дат события после перетаскивания или изменения размера
 * @param {string} eventId - ID события
 * @param {Date} startDate - Новая дата начала
 * @param {Date} endDate - Новая дата окончания
 */
function updateEventDates(eventId, startDate, endDate) {
    const formData = new FormData();
    formData.append('event_id', eventId);
    formData.append('start_time', startDate.toISOString());
    
    if (endDate) {
        formData.append('end_time', endDate.toISOString());
    }
    
    fetch('/manager/update_event_dates', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('Даты события успешно обновлены');
        } else {
            console.error('Ошибка при обновлении дат события:', data.message);
            // Можно добавить отображение уведомления об ошибке
        }
    })
    .catch(error => {
        console.error('Ошибка при отправке запроса:', error);
    });
}

/**
 * Фильтрует события календаря по типу
 * @param {Object} calendar - Объект календаря FullCalendar
 * @param {string} type - Тип события для фильтрации
 * @param {boolean} show - Показывать (true) или скрывать (false) события данного типа
 */
function filterEventsByType(calendar, type, show) {
    const events = calendar.getEvents();
    
    events.forEach(event => {
        if (event.extendedProps.type === type) {
            event.setProp('display', show ? 'auto' : 'none');
        }
    });
}

/**
 * Загружает и отображает ближайшие события в боковой панели
 * @param {Object} calendar - Объект календаря FullCalendar
 * @param {string} containerId - ID контейнера для отображения ближайших событий
 * @param {number} limit - Максимальное количество отображаемых событий
 */
function loadUpcomingEvents(calendar, containerId, limit = 5) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const events = calendar.getEvents();
    const now = new Date();
    
    // Фильтруем и сортируем события
    const futureEvents = events
        .filter(event => event.start >= now)
        .sort((a, b) => a.start - b.start)
        .slice(0, limit);
    
    // Очищаем контейнер
    container.innerHTML = '';
    
    if (futureEvents.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i data-feather="calendar" style="width: 48px; height: 48px; color: var(--bs-secondary);"></i>
                <p class="mt-3">Нет предстоящих событий</p>
            </div>
        `;
        feather.replace();
        return;
    }
    
    // Создаем элементы списка событий
    futureEvents.forEach(event => {
        const eventItem = document.createElement('a');
        eventItem.href = '#';
        eventItem.className = 'list-group-item list-group-item-action';
        eventItem.onclick = function(e) {
            e.preventDefault();
            showEventDetails(event);
        };
        
        const formattedDate = event.start.toLocaleString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        eventItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${event.title}</h6>
                <small>${formattedDate}</small>
            </div>
            <p class="mb-1 small">
                ${event.extendedProps.location ? `<i data-feather="map-pin" class="feather-sm me-1"></i> ${event.extendedProps.location}` : ''}
            </p>
        `;
        
        container.appendChild(eventItem);
    });
    
    // Инициализация иконок Feather
    feather.replace({
        'class': 'feather-sm',
        'width': 16,
        'height': 16
    });
}
