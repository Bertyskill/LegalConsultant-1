/**
 * Основной JavaScript файл для системы ЮрКонсалт
 */

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всплывающих подсказок
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Инициализация всплывающих сообщений
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Обработка формы с выбором категории и темы
    const categorySelect = document.getElementById('category_id');
    const topicSelect = document.getElementById('topic_id');
    
    if (categorySelect && topicSelect) {
        categorySelect.addEventListener('change', function() {
            const categoryId = this.value;
            
            if (categoryId) {
                // Очищаем список тем
                topicSelect.innerHTML = '<option value="">Загрузка...</option>';
                
                // Загружаем темы для выбранной категории
                fetch(`/get_topics/${categoryId}`)
                    .then(response => response.json())
                    .then(data => {
                        topicSelect.innerHTML = '';
                        
                        // Добавляем варианты выбора
                        data.forEach(topic => {
                            const option = document.createElement('option');
                            option.value = topic.id;
                            option.textContent = topic.name;
                            topicSelect.appendChild(option);
                        });
                        
                        // Если тем нет, показываем сообщение
                        if (data.length === 0) {
                            const option = document.createElement('option');
                            option.value = '';
                            option.textContent = 'Нет доступных тем';
                            topicSelect.appendChild(option);
                        }
                        
                        // Разблокируем поле
                        topicSelect.disabled = false;
                    })
                    .catch(error => {
                        console.error('Ошибка загрузки тем:', error);
                        topicSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
                    });
            } else {
                // Если категория не выбрана, очищаем и блокируем список тем
                topicSelect.innerHTML = '<option value="">Сначала выберите категорию</option>';
                topicSelect.disabled = true;
            }
        });
    }
    
    // Обработка формы фильтрации консультаций
    const filterForm = document.getElementById('consultationFilterForm');
    if (filterForm) {
        const categoryFilterSelect = document.getElementById('category_filter');
        const topicFilterSelect = document.getElementById('topic_filter');
        
        if (categoryFilterSelect && topicFilterSelect) {
            categoryFilterSelect.addEventListener('change', function() {
                const categoryId = this.value;
                
                if (categoryId) {
                    // Очищаем список тем
                    topicFilterSelect.innerHTML = '<option value="">Загрузка...</option>';
                    
                    // Загружаем темы для выбранной категории
                    fetch(`/get_topics/${categoryId}`)
                        .then(response => response.json())
                        .then(data => {
                            topicFilterSelect.innerHTML = '<option value="">Все темы</option>';
                            
                            // Добавляем варианты выбора
                            data.forEach(topic => {
                                const option = document.createElement('option');
                                option.value = topic.id;
                                option.textContent = topic.name;
                                topicFilterSelect.appendChild(option);
                            });
                            
                            // Разблокируем поле
                            topicFilterSelect.disabled = false;
                        })
                        .catch(error => {
                            console.error('Ошибка загрузки тем:', error);
                            topicFilterSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
                        });
                } else {
                    // Если категория не выбрана, очищаем и блокируем список тем
                    topicFilterSelect.innerHTML = '<option value="">Все темы</option>';
                    topicFilterSelect.disabled = true;
                }
            });
        }
    }
});