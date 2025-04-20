/**
 * Модуль для работы с диаграммами в системе ЮрКонсалт
 * Использует Chart.js для отображения статистики
 */

/**
 * Инициализирует круговую диаграмму с распределением по категориям права
 * @param {string} chartId - ID элемента canvas для диаграммы
 * @param {Object} data - Данные для диаграммы
 */
function initCategoryChart(chartId, data) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: [
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: 'Распределение по категориям права'
                }
            }
        }
    });
}

/**
 * Инициализирует линейную диаграмму с динамикой консультаций
 * @param {string} chartId - ID элемента canvas для диаграммы
 * @param {Object} data - Данные для диаграммы
 */
function initConsultationChart(chartId, data) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Консультации',
                data: data.data,
                fill: false,
                borderColor: 'rgb(54, 162, 235)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Динамика консультаций по месяцам'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Количество консультаций'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Месяц'
                    }
                }
            }
        }
    });
}

/**
 * Инициализирует столбчатую диаграмму с активностью юристов
 * @param {string} chartId - ID элемента canvas для диаграммы
 * @param {Object} data - Данные для диаграммы
 */
function initLawyerActivityChart(chartId, data) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Часы',
                data: data.data,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Активность юристов (часы)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Часов'
                    }
                }
            }
        }
    });
}

/**
 * Инициализирует радарную диаграмму с распределением компетенций юристов
 * @param {string} chartId - ID элемента canvas для диаграммы 
 * @param {Object} data - Данные для диаграммы
 */
function initCompetenceChart(chartId, data) {
    const ctx = document.getElementById(chartId).getContext('2d');
    
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: data.labels,
            datasets: data.datasets
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Компетенции юристов по категориям права'
                }
            },
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 10
                }
            }
        }
    });
}