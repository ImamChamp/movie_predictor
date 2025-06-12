document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('movie-form');
    const resultEmpty = document.getElementById('result-empty');
    const resultContent = document.getElementById('result-content');
    const loading = document.getElementById('loading');
    const genresError = document.getElementById('genres-error');
    const budgetRange = document.getElementById('budget-range');
    const budgetInput = document.getElementById('budget-input');
    const budgetCategory = document.getElementById('budget-category');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    document.getElementById('fullscreenToggle')?.addEventListener('click', toggleFullscreen);
    document.getElementById('closeChat')?.addEventListener('click', closeChat);

    messageInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // чтобы не вставлялся перенос строки
            sendMessage();
        }
    });

    console.log('messageInput exists:', !!messageInput);
    console.log('chatMessages exists:', !!chatMessages);

    if (!messageInput) {
        console.error('Element #messageInput not found in DOM');
    }
    if (!chatMessages) {
        console.error('Element #chatMessages not found in DOM');
    }
    document.querySelector('.chat-toggle').addEventListener('click', toggleChat);
    document.querySelector('.send-button').addEventListener('click', sendMessage);

    // Функция для определения категории бюджета
    function getBudgetCategory(budget) {
        if (budget < 10000000) return "Малобюджетный";
        if (budget < 70000000) return "Средний";
        return "Блокбастер";
    }

    // Функция для форматирования бюджета
    function formatBudget(budget) {
        return parseInt(budget).toLocaleString();
    }

    // Обновление при изменении ползунка
    budgetRange.addEventListener('input', function() {
        const budget = parseInt(this.value);
        budgetInput.value = budget;
        budgetCategory.textContent = `Бюджет: ${getBudgetCategory(budget)}`;
    });

    // Обновление при изменении ввода
    budgetInput.addEventListener('input', function() {
        let budget = parseInt(this.value) || 1000000;

        // Ограничение значений
        if (budget < 1000000) budget = 1000000;
        if (budget > 300000000) budget = 300000000;

        this.value = budget;
        budgetRange.value = budget;
        budgetCategory.textContent = `Бюджет: ${getBudgetCategory(budget)}`;
    });

    // Обработка потери фокуса полем ввода для форматирования
    budgetInput.addEventListener('blur', function() {
        this.value = parseInt(this.value) || 1000000;
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        // Проверяем, выбран ли хотя бы один жанр
        const selectedGenres = document.querySelectorAll('input[name="genres"]:checked');
        if (selectedGenres.length === 0) {
            genresError.style.display = 'block';
            return;
        } else {
            genresError.style.display = 'none';
        }

        resultEmpty.style.display = 'none';
        resultContent.style.display = 'none';
        loading.style.display = 'flex';

        // Собираем данные из формы
        const formData = new FormData(form);

        // Собираем выбранные жанры в массив
        const genres = [];
        selectedGenres.forEach(checkbox => {
            genres.push(checkbox.value);
        });
        const budget = parseInt(budgetInput.value);

        const movieData = {
            title: formData.get('title'),
            genres: genres, // Теперь передаем массив жанров
            original_language: formData.get('original_language'),
            budget: budget,
            country: formData.get('country')
        };

        // Отправка данных на сервер Flask
        fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(movieData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сервера');
            }
            return response.json();
        })
        .then(data => {
            loading.style.display = 'none';
            displayResults(data.movie, data.prediction, data.statistic);
            resultContent.style.display = 'block';
        })
        .catch(error => {
            console.error('Ошибка:', error);
            loading.style.display = 'none';

            // В случае ошибки показываем сообщение
            resultEmpty.style.display = 'block';
            resultEmpty.innerHTML = '<p>Произошла ошибка при получении предсказания. Пожалуйста, попробуйте еще раз.</p>';
        });
        localStorage.removeItem("movieFormData");
    });

    function saveFormDataToLocalStorage() {
        const selectedGenres = getSelectedGenres(); // предполагаем, что эта функция уже есть
        const budget = document.getElementById("budget-input").value; // Updated to match input ID
        const country = document.getElementById("country").value;
        const language = document.getElementById("original_language").value; // Updated to match select ID

        const formData = {
            genres: selectedGenres,
            budget,
            country,
            language,
        };

        localStorage.setItem("movieFormData", JSON.stringify(formData));
    }

    document.getElementById("open-charts")?.addEventListener("click", (e) => {
        saveFormDataToLocalStorage();
    });

    function displayResults(movieData, prediction, statistic) {
        document.getElementById('result-title').textContent = movieData.title;

        document.getElementById('percentage').textContent = statistic;

        const genreMapping = {
            'Action': 'Боевик',
            'Comedy': 'Комедия',
            'Drama': 'Драма',
            'Horror': 'Ужасы',
            'Science Fiction': 'Фантастика',
            'Thriller': 'Триллер',
            'Romance': 'Мелодрама',
            'Animation': 'Мультфильм',
            'Adventure': 'Приключения',
            'Fantasy': 'Фэнтези',
            'Family': 'Семейный',
            'Crime': 'Преступники',
            'Mystery': 'Мистика',
            'History': 'Исторический',
            'War': 'Военный',
            'Documentary': 'Документальный',
            'Music': 'Музыкальный',
            'Western': 'Вестерн',
            'TV Movie': 'ТВ-Фильм'
        };

        const countryMapping = {
            'AU': 'Австралия',
            'US': 'США',
            'MX': 'Мексика',
            'GB': 'Великобритания',
            'CL': 'Чили',
            'NO': 'Норвегия',
            'ES': 'Испания',
            'AR': 'Аргентина',
            'KR': 'Южная Корея',
            'HK': 'Гонконг',
            'UA': 'Украина',
            'IT': 'Италия',
            'RU': 'Россия',
            'CO': 'Колумбия',
            'DE': 'Германия',
            'JP': 'Япония',
            'FR': 'Франция',
            'FI': 'Финляндия',
            'IS': 'Исландия',
            'ID': 'Индонезия',
            'BR': 'Бразилия',
            'BE': 'Бельгия',
            'DK': 'Дания',
            'TR': 'Турция',
            'TH': 'Таиланд',
            'PL': 'Польша',
            'GT': 'Гватемала',
            'CN': 'Китай',
            'CZ': 'Чехия',
            'PH': 'Филиппины',
            'ZA': 'Южная Африка',
            'CA': 'Канада',
            'NL': 'Нидерланды',
            'TW': 'Тайвань',
            'PR': 'Пуэрто-Рико',
            'IN': 'Индия',
            'IE': 'Ирландия',
            'SG': 'Сингапур',
            'PE': 'Перу',
            'CH': 'Швейцария',
            'SE': 'Швеция',
            'IL': 'Израиль',
            'DO': 'Доминикана',
            'VN': 'Вьетнам',
            'GR': 'Греция',
            'SU': 'СССР',
            'HU': 'Венгрия',
            'BO': 'Боливия',
            'SK': 'Словакия',
            'UY': 'Уругвай',
            'BY': 'Беларусь',
            'AT': 'Австрия',
            'PY': 'Парагвай',
            'MY': 'Малайзия',
            'MU': 'Маврикий',
            'LV': 'Латвия',
            'XC': 'Европа (прочее)',
            'KH': 'Камбоджа',
            'IR': 'Иран'
        };

        // Отображаем жанры в виде списка или тегов
        const genresContainer = document.getElementById('result-genres');
        genresContainer.innerHTML = ''; // Очищаем предыдущие значения

        // Если genres - массив, обрабатываем его
        if (Array.isArray(movieData.genres)) {
            const genreElements = movieData.genres.map(genre => {
                const displayName = genreMapping[genre] || genre;
                return `<span class="genre-tag">${displayName}</span>`;
            });
            genresContainer.innerHTML = genreElements.join('');
        }
        // Если genres - строка (для обратной совместимости)
        else if (movieData.genre) {
            genresContainer.innerHTML = `<span class="genre-tag">${genreMapping[movieData.genre] || movieData.genre}</span>`;
        }

        document.getElementById('result-country').textContent = countryMapping[movieData.country] || movieData.country;

        const predictionValue = typeof prediction === 'number' ? prediction.toFixed(1) : prediction;
        document.getElementById('prediction-value').textContent = predictionValue;
        const ratingContainer = document.getElementById('rating-container')
        const ratingBar = document.getElementById('rating-bar');
        const ratingPercentage = (parseFloat(predictionValue) / 10) * 100;

        setTimeout(() => {
            ratingBar.style.width = `${ratingPercentage}%`;

            if (parseFloat(predictionValue) >= 70) {
                ratingBar.style.backgroundColor = '#4CAF50'; /* Зеленый для хороших оценок */
                ratingContainer.style.backgroundColor = '#4CAF50'; /* Зеленый для хороших оценок */
            } else if (parseFloat(predictionValue) >= 60 <= 69.9) {
                ratingBar.style.backgroundColor = '#FFC107'; /* Желтый для средних */
                ratingContainer.style.backgroundColor = '#FFC107'; /* Желтый для средних */
            } else if (parseFloat(predictionValue) <= 59) {
                ratingBar.style.backgroundColor = '#F44336'; /* Красный для низких */
                ratingContainer.style.backgroundColor = '#F44336';
            }
        }, 100);
    }

    // Chat widget functionality
    let chatOpen = false;

    function toggleChat() {
        console.log('toggleChat called, chatOpen:', chatOpen);
        const container = document.getElementById('chatContainer');
        const toggle = document.querySelector('.chat-toggle');

        chatOpen = !chatOpen;

        if (chatOpen) {
            container.classList.add('open');
            toggle.classList.add('active');
        } else {
            container.classList.remove('open');
            toggle.classList.remove('active');
        }
    }

    function closeChat() {
        const container = document.getElementById('chatContainer');
        const toggle = document.querySelector('.chat-toggle');
        chatOpen = false;
        container.classList.remove('open');
        toggle.classList.remove('active');
    }

    function handleKeyPress(event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    }

    function sendMessage() {
        console.log('sendMessage called');
        const input = document.getElementById('messageInput');
        if (!input) {
            console.error('Element #messageInput not found');
            return;
        }
        const message = input.value.trim();
        if (!message) {
            console.log('Message is empty');
            return;
        }

        // Добавляем сообщение пользователя
        addMessage(message, 'user');
        input.value = '';

        // Показываем индикатор набора
        showTyping();

        // Отправляем POST запрос на сервер
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сервера');
            }
            return response.json();
        })
        .then(data => {
            hideTyping();
            if (data.error) {
                console.error('Server error:', data.error);
                addMessage('Произошла ошибка на сервере. Попробуйте снова.', 'bot');
                return;
            }
            const botResponse = data.response;
            addMessage(botResponse, 'bot');
        })
        .catch(error => {
            console.error('Ошибка:', error);
            hideTyping();
            addMessage('Не удалось связаться с сервером. Проверьте подключение.', 'bot');
        });
    }

    function addMessage(text, sender) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.textContent = text;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function showTyping() {
        const messagesContainer = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function hideTyping() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Закрытие чата при клике вне его
    document.addEventListener('click', function(event) {
        const chatWidget = document.querySelector('.chat-widget');
        const chatContainer = document.getElementById('chatContainer');

        if (chatOpen && !chatWidget.contains(event.target)) {
            toggleChat();
        }
    });

    let isFullscreen = false;

    function toggleFullscreen() {
        const chatWidget = document.querySelector('.chat-widget');
        const fullscreenButton = document.getElementById('fullscreenToggle');
        const fullscreenIcon = fullscreenButton.querySelector('svg path');

        isFullscreen = !isFullscreen;

        if (isFullscreen) {
            chatWidget.classList.add('fullscreen');
            fullscreenIcon.setAttribute('d', 'M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 0 2-2h3M3 16h3a2 2 0 0 0 2 2v3');

            // Добавить обработчик для выхода по ESC
            document.addEventListener('keydown', handleEscapeKey);

            // Добавить обработчик для выхода по клику вне окна
            setTimeout(() => {
                document.addEventListener('click', handleOutsideClick);
            }, 100);
        } else {
            chatWidget.classList.remove('fullscreen');
            fullscreenIcon.setAttribute('d', 'M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3');

            // Удалить обработчики
            document.removeEventListener('keydown', handleEscapeKey);
            document.removeEventListener('click', handleOutsideClick);
        }
    }
});

$(document).ready(function() {
    $('#country').select2({
        templateResult: function (state) {
            if (!state.id) return state.text;
            const img = $(state.element).data('image');
            if (!img) return state.text;
            return $('<span><img src="' + img + '" class="img-flag" /> ' + state.text + '</span>');
        },
        templateSelection: function (state) {
            if (!state.id) return state.text;
            const img = $(state.element).data('image');
            if (!img) return state.text;
            return $('<span><img src="' + img + '" class="img-flag" /> ' + state.text + '</span>');
        }
    });
});

// Функция для получения выбранных жанров
function getSelectedGenres() {
    const selectedGenres = document.querySelectorAll('input[name="genres"]:checked');
    const genres = [];
    selectedGenres.forEach(checkbox => {
        genres.push(checkbox.value);
    });
    return genres;
}