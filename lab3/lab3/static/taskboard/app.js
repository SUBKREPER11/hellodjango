let tasks = [];
let currentFilter = 'all';

const taskForm = document.getElementById('task-form');
const taskInput = document.getElementById('task-input');
const validationError = document.getElementById('validation-error');
const messageContainer = document.getElementById('message-container');
const tasksList = document.getElementById('tasks-list');
const emptyState = document.getElementById('empty-state');
const totalCountEl = document.getElementById('total-count');
const completedCountEl = document.getElementById('completed-count');
const filterButtons = document.querySelectorAll('.btn-filter');

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

function showMessage(msg, isError = true) {
    if (!messageContainer) return;
    messageContainer.textContent = msg;
    messageContainer.className = isError ? 'message error' : 'message';
    messageContainer.classList.remove('hidden');

    setTimeout(() => {
        messageContainer.classList.add('hidden');
    }, 3000);
}

function setValidationError(msg) {
    if (!validationError) return;
    if (msg) {
        validationError.textContent = msg;
        validationError.classList.remove('hidden');
    } else {
        validationError.textContent = '';
        validationError.classList.add('hidden');
    }
}

async function loadTasks() {
    try {
        const response = await fetch('/api/tasks/');
        if (!response.ok) {
            throw new Error('Nie udało się pobrać zadań');
        }
        tasks = await response.json();
        renderTasks();
    } catch (error) {
        showMessage(error.message, true);
    }
}

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
            throw new Error(data.error || 'Błąd zapisu zadania');
        }

        tasks.unshift(data);
        renderTasks();
        taskInput.value = '';
        setValidationError('');
    } catch (error) {
        showMessage(error.message, true);
    }
}

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
            throw new Error(data.error || 'Błąd aktualizacji zadania');
        }

        const task = tasks.find(t => t.id === taskId);
        if (task) {
            task.completed = data.completed;
            renderTasks();
        }
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function deleteTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Błąd usuwania zadania');
        }

        tasks = tasks.filter(t => t.id !== taskId);
        renderTasks();
    } catch (error) {
        showMessage(error.message, true);
    }
}

function updateCounters() {
    const total = tasks.length;
    const completed = tasks.filter(t => t.completed).length;

    if (totalCountEl) totalCountEl.textContent = total;
    if (completedCountEl) completedCountEl.textContent = completed;
}

function renderTasks() {
    if (!tasksList) return;
    tasksList.replaceChildren();

    let filtered = tasks;
    if (currentFilter === 'active') {
        filtered = tasks.filter(t => !t.completed);
    } else if (currentFilter === 'completed') {
        filtered = tasks.filter(t => t.completed);
    }

    if (filtered.length === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }

    filtered.forEach(task => {
        const li = document.createElement('li');
        if (task.completed) {
            li.classList.add('completed');
        }

        const content = document.createElement('div');
        content.className = 'task-content';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'task-checkbox';
        checkbox.checked = task.completed;
        checkbox.addEventListener('change', () => {
            toggleTaskStatus(task.id, checkbox.checked);
        });

        const titleSpan = document.createElement('span');
        titleSpan.className = 'task-title';
        titleSpan.textContent = task.title;

        content.appendChild(checkbox);
        content.appendChild(titleSpan);

        const actions = document.createElement('div');
        actions.className = 'task-actions';

        const statusBtn = document.createElement('button');
        statusBtn.type = 'button';
        statusBtn.className = 'btn-status';
        statusBtn.textContent = task.completed ? 'Przywróć' : 'Ukończ';
        statusBtn.addEventListener('click', () => {
            toggleTaskStatus(task.id, !task.completed);
        });

        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'btn-delete';
        deleteBtn.textContent = 'Usuń';
        deleteBtn.addEventListener('click', () => {
            deleteTask(task.id);
        });

        actions.appendChild(statusBtn);
        actions.appendChild(deleteBtn);

        li.appendChild(content);
        li.appendChild(actions);
        tasksList.appendChild(li);
    });

    updateCounters();
}

function setFilter(type) {
    currentFilter = type;
    filterButtons.forEach(btn => {
        if (btn.dataset.filter === type) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    renderTasks();
}

function handleFormSubmit(e) {
    e.preventDefault();
    const title = taskInput.value.trim();

    if (!title) {
        setValidationError('Treść zadania nie może być pusta!');
        taskInput.focus();
        return;
    }

    setValidationError('');
    addTask(title);
}

document.addEventListener('DOMContentLoaded', () => {
    if (taskForm) {
        taskForm.addEventListener('submit', handleFormSubmit);
    }

    if (taskInput) {
        taskInput.addEventListener('input', () => {
            if (taskInput.value.trim().length > 0) {
                setValidationError('');
            }
        });
    }

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            setFilter(btn.dataset.filter);
        });
    });

    loadTasks();
});
