/**
 * TaskBoard - Obsługa frontendu JavaScript
 * Zgodność z wytycznymi:
 * - brak innerHTML dla danych użytkownika (tylko textContent)
 * - addEventListener() do obsługi wszystkich zdarzeń
 * - pełna obsługa fetch() z weryfikacją response.ok
 * - obsługa tokena CSRF w nagłówku X-CSRFToken
 * - modularny podział na funkcje
 */

// Stan aplikacji
let tasks = [];
let currentFilter = 'all'; // 'all' | 'active' | 'completed'

// Elementy DOM
const taskForm = document.getElementById('task-form');
const taskInput = document.getElementById('task-input');
const validationError = document.getElementById('validation-error');
const messageContainer = document.getElementById('message-container');
const tasksList = document.getElementById('tasks-list');
const emptyState = document.getElementById('empty-state');
const totalCountEl = document.getElementById('total-count');
const completedCountEl = document.getElementById('completed-count');
const filterButtons = document.querySelectorAll('.btn-filter');

/**
 * Pobiera token CSRF z ukrytego pola formularza lub ciasteczek
 */
function getCsrfToken() {
    const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (tokenInput && tokenInput.value) {
        return tokenInput.value;
    }
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const parts = cookie.trim().split('=');
        if (parts[0] === 'csrftoken') {
            return decodeURIComponent(parts[1]);
        }
    }
    return '';
}

/**
 * Wyświetla globalny komunikat błędu lub sukcesu
 */
let messageTimeout = null;
function showMessage(message, isError = true) {
    if (!messageContainer) return;
    
    messageContainer.textContent = message;
    messageContainer.className = isError 
        ? 'message-container error' 
        : 'message-container success';
    messageContainer.classList.remove('hidden');

    if (messageTimeout) {
        clearTimeout(messageTimeout);
    }
    messageTimeout = setTimeout(() => {
        messageContainer.classList.add('hidden');
    }, 4000);
}

/**
 * Pokazuje lub czyści błąd walidacji pod formularzem
 */
function setValidationError(message) {
    if (!validationError) return;
    if (message) {
        validationError.textContent = message;
        validationError.classList.remove('hidden');
    } else {
        validationError.textContent = '';
        validationError.classList.add('hidden');
    }
}

/**
 * Pobiera listę zadań z backendu Django
 */
async function loadTasks() {
    try {
        const response = await fetch('/api/tasks/');
        if (!response.ok) {
            throw new Error('Nie udało się pobrać zadań');
        }
        const data = await response.json();
        tasks = data;
        renderTasks();
    } catch (error) {
        showMessage(error.message, true);
    }
}

/**
 * Dodaje nowe zadanie przez API (POST)
 */
async function addTask(title) {
    try {
        const response = await fetch('/api/tasks/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ title: title })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Wystąpił błąd podczas dodawania zadania');
        }

        tasks.unshift(data);
        renderTasks();
        taskInput.value = '';
        setValidationError('');
        showMessage('Zadanie dodane pomyślnie!', false);
    } catch (error) {
        showMessage(error.message, true);
    }
}

/**
 * Zmienia status zadania (ukończone / aktywne) przez API (PATCH)
 */
async function toggleTaskStatus(taskId, completed) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ completed: completed })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Nie udało się zmienić statusu zadania');
        }

        const taskIndex = tasks.findIndex(t => t.id === taskId);
        if (taskIndex !== -1) {
            tasks[taskIndex].completed = data.completed;
            renderTasks();
        }
    } catch (error) {
        showMessage(error.message, true);
    }
}

/**
 * Usuwa zadanie przez API (DELETE)
 */
async function deleteTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Nie udało się usunąć zadania');
        }

        tasks = tasks.filter(t => t.id !== taskId);
        renderTasks();
        showMessage('Zadanie zostało usunięte', false);
    } catch (error) {
        showMessage(error.message, true);
    }
}

/**
 * Aktualizuje liczniki podsumowania
 */
function updateCounters() {
    const total = tasks.length;
    const completed = tasks.filter(t => t.completed).length;

    if (totalCountEl) totalCountEl.textContent = total;
    if (completedCountEl) completedCountEl.textContent = completed;
}

/**
 * Renderuje elementy listy w DOM na podstawie stanu tasks i currentFilter
 */
function renderTasks() {
    if (!tasksList) return;

    // Czyszczenie listy
    tasksList.replaceChildren();

    // Filtrowanie tablicy zadań
    let filteredTasks = tasks;
    if (currentFilter === 'active') {
        filteredTasks = tasks.filter(t => !t.completed);
    } else if (currentFilter === 'completed') {
        filteredTasks = tasks.filter(t => t.completed);
    }

    // Obsługa pustej listy
    if (filteredTasks.length === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }

    // Budowanie elementów DOM dla każdego zadania
    filteredTasks.forEach(task => {
        const li = document.createElement('li');
        li.className = task.completed ? 'task-item completed' : 'task-item';
        li.dataset.id = task.id;

        // Kontener lewej strony (checkbox + treść)
        const contentDiv = document.createElement('div');
        contentDiv.className = 'task-content';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'task-checkbox';
        checkbox.checked = task.completed;
        checkbox.title = 'Zmień status zadania';
        checkbox.addEventListener('change', () => {
            toggleTaskStatus(task.id, checkbox.checked);
        });

        const titleSpan = document.createElement('span');
        titleSpan.className = 'task-title';
        // BEZPIECZEŃSTWO: użycie textContent zapobiega atakom XSS
        titleSpan.textContent = task.title;

        contentDiv.appendChild(checkbox);
        contentDiv.appendChild(titleSpan);

        // Kontener przycisków akcji
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'task-actions';

        const statusBtn = document.createElement('button');
        statusBtn.type = 'button';
        statusBtn.className = 'btn btn-status';
        statusBtn.textContent = task.completed ? 'Przywróć' : 'Ukończ';
        statusBtn.addEventListener('click', () => {
            toggleTaskStatus(task.id, !task.completed);
        });

        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'btn btn-delete';
        deleteBtn.textContent = 'Usuń';
        deleteBtn.addEventListener('click', () => {
            deleteTask(task.id);
        });

        actionsDiv.appendChild(statusBtn);
        actionsDiv.appendChild(deleteBtn);

        li.appendChild(contentDiv);
        li.appendChild(actionsDiv);
        tasksList.appendChild(li);
    });

    updateCounters();
}

/**
 * Ustawia aktywny filtr i odświeża widok
 */
function setFilter(filterType) {
    currentFilter = filterType;

    filterButtons.forEach(btn => {
        if (btn.dataset.filter === filterType) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    renderTasks();
}

/**
 * Obsługa wysłania formularza dodawania zadania
 */
function handleFormSubmit(event) {
    event.preventDefault();

    const title = taskInput.value.trim();

    // Walidacja po stronie klienta (slajd 7: "Nie można dodać pustego zadania")
    if (!title) {
        setValidationError('Treść zadania nie może być pusta!');
        taskInput.focus();
        return;
    }

    setValidationError('');
    addTask(title);
}

// Inicjalizacja nasłuchiwaczy zdarzeń po załadowaniu drzewa DOM
document.addEventListener('DOMContentLoaded', () => {
    // Obsługa formularza
    if (taskForm) {
        taskForm.addEventListener('submit', handleFormSubmit);
    }

    // Czyszczenie błędu walidacji przy wpisywaniu tekstu
    if (taskInput) {
        taskInput.addEventListener('input', () => {
            if (taskInput.value.trim().length > 0) {
                setValidationError('');
            }
        });
    }

    // Obsługa przycisków filtrów
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            setFilter(btn.dataset.filter);
        });
    });

    // Pobranie danych początkowych z API
    loadTasks();
});
