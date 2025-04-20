/**
 * Основной JavaScript файл для системы "Решение есть. Консалтинг"
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
    
    // Обработка переключателей для показа/скрытия пароля
    const passwordToggleBtns = document.querySelectorAll('.password-toggle');
    
    passwordToggleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const passwordField = this.previousElementSibling;
            const icon = this.querySelector('i');
            
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                icon.setAttribute('data-feather', 'eye-off');
            } else {
                passwordField.type = 'password';
                icon.setAttribute('data-feather', 'eye');
            }
            
            feather.replace();
        });
    });
    
    // Обработка формы с выбором отрасли права и темы
    const branchSelect = document.getElementById('branch_id');
    const topicInput = document.getElementById('topic');
    const topicsList = document.getElementById('topics-list');
    
    if (branchSelect) {
        branchSelect.addEventListener('change', function() {
            // Можно добавить дополнительную логику при смене отрасли права
            if (topicInput) {
                topicInput.focus();
            }
        });
    }
    
    // Обработка ввода темы с автодополнением
    if (topicInput && topicsList) {
        // Загрузка тем для автодополнения
        let selectedBranchId = branchSelect ? branchSelect.value : '';
        
        topicInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            if (query.length > 1) {
                const currentBranchId = branchSelect ? branchSelect.value : '';
                
                // Отправляем запрос на сервер для получения совпадающих тем
                fetch(`/get_topics_autocomplete?branch_id=${currentBranchId}&query=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        // Очищаем список
                        topicsList.innerHTML = '';
                        
                        if (data.length > 0) {
                            // Показываем список
                            topicsList.classList.remove('d-none');
                            
                            // Добавляем варианты
                            data.forEach(topic => {
                                const item = document.createElement('a');
                                item.classList.add('list-group-item', 'list-group-item-action');
                                item.textContent = topic;
                                item.href = '#';
                                
                                item.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    topicInput.value = this.textContent;
                                    topicsList.classList.add('d-none');
                                });
                                
                                topicsList.appendChild(item);
                            });
                        } else {
                            topicsList.classList.add('d-none');
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка загрузки автодополнений:', error);
                    });
            } else {
                topicsList.classList.add('d-none');
            }
        });
        
        // Скрытие списка при клике вне его
        document.addEventListener('click', function(e) {
            if (!topicInput.contains(e.target) && !topicsList.contains(e.target)) {
                topicsList.classList.add('d-none');
            }
        });
    }
    
    // Реализация выбора отрасли права с карточками
    const branchCards = document.querySelectorAll('.branch-card-input');
    
    branchCards.forEach(input => {
        input.addEventListener('change', function() {
            document.querySelectorAll('.branch-card').forEach(card => {
                card.classList.remove('border-primary', 'shadow-primary');
            });
            
            if (this.checked) {
                const card = this.closest('.branch-card');
                card.classList.add('border-primary', 'shadow-primary');
                
                // Обновляем скрытое поле с ID отрасли права
                const branchIdInput = document.getElementById('branch_id');
                if (branchIdInput) {
                    branchIdInput.value = this.value;
                }
            }
        });
    });
    
    // Обработка формы фильтрации консультаций
    const filterForm = document.getElementById('consultationFilterForm');
    if (filterForm) {
        const branchFilterSelect = document.getElementById('branch_filter');
        const statusFilterSelect = document.getElementById('status_filter');
        
        [branchFilterSelect, statusFilterSelect].forEach(select => {
            if (select) {
                select.addEventListener('change', function() {
                    filterForm.submit();
                });
            }
        });
    }
    
    // Автоматическая прокрутка к последнему сообщению в чате консультации
    const messageThread = document.querySelector('.message-thread');
    if (messageThread) {
        messageThread.scrollTop = messageThread.scrollHeight;
    }
});