
// --- Helper Functions ---

function disableButton(button, text = "Processing...") {
    if (button) {
        button.disabled = true;
        button.classList.add('opacity-50', 'cursor-not-allowed');
        if (!button.dataset.originalText) { button.dataset.originalText = button.innerHTML; }
        const spinner = `<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"> <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle> <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path> </svg>`;
        button.innerHTML = spinner + (text || '');
    }
}

function enableButton(button) {
    if (button) {
        button.disabled = false;
        button.classList.remove('opacity-50', 'cursor-not-allowed');
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    }
}

function showFeedback(element, message, isError = true) {
    if (!element) return;
    element.textContent = message;
    element.classList.remove('hidden');
    element.classList.toggle('form-error', isError);
    element.classList.toggle('form-success', !isError);
    setTimeout(() => { element.textContent = ''; element.classList.add('hidden'); }, 4000);
}

function renderReminder(reminder) {
    const reminderDiv = document.createElement('div');
    reminderDiv.dataset.id = reminder.id;
    reminderDiv.className = 'reminder-item p-4 bg-gray-light border border-gray-200 rounded-lg flex justify-between items-center hover:bg-gray-200 transition-colors duration-150 opacity-0 translate-y-2';
    let formattedDate = 'Invalid Date';
    try {
        const dateObj = new Date(reminder.reminder_datetime);
        if (!isNaN(dateObj)) { formattedDate = dateObj.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }); }
    } catch (e) { console.error("Error parsing date:", reminder.reminder_datetime, e); }
    reminderDiv.innerHTML = `
        <div>
            <p class="font-medium text-gray-darker break-words">${reminder.text}</p>
            <p class="text-sm text-gray-lighter">${formattedDate}</p>
        </div>
        <button class="delete-reminder-btn table-button delete-button" aria-label="Delete reminder">
            Delete
        </button>
    `;
    requestAnimationFrame(() => { reminderDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease'; reminderDiv.classList.remove('opacity-0', 'translate-y-2'); });
    return reminderDiv;
}

function checkReminderListEmpty(count = null) {
    const reminderList = document.getElementById('reminderList');
    const noRemindersText = document.getElementById('noRemindersText');
    const upcomingRemindersCountEl = document.getElementById('upcomingRemindersCount');

    if (!reminderList) return;

    const reminderItemsCount = count !== null ? count : reminderList.querySelectorAll('.reminder-item').length;
    if (noRemindersText) { noRemindersText.classList.toggle('hidden', reminderItemsCount > 0); if (reminderItemsCount === 0) { noRemindersText.textContent = "No reminders scheduled yet."; } }
    if (upcomingRemindersCountEl) { upcomingRemindersCountEl.textContent = reminderItemsCount; }
}

function checkNotificationListEmpty() {
    const notificationList = document.getElementById('notificationList');
    const noNotificationsText = document.getElementById('noNotificationsText');
    if (!notificationList) return;
    const notificationItems = notificationList.querySelectorAll('.notification-item');
    if (noNotificationsText) { noNotificationsText.classList.toggle('hidden', notificationItems.length > 0); }
}
