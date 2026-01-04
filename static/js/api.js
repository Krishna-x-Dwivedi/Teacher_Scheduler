
// --- API Functions ---

// Reminders
async function fetchReminders() {
    const reminderList = document.getElementById('reminderList');
    const noRemindersText = document.getElementById('noRemindersText');
    if (!reminderList) return;

    reminderList.innerHTML = '';
    if (noRemindersText) { noRemindersText.textContent = "Loading reminders..."; noRemindersText.classList.remove('hidden'); }

    try {
        const response = await fetch(`${backendUrl}/reminders`);
        if (!response.ok) throw new Error(`Status: ${response.status}`);
        const reminders = await response.json();

        if (reminders.length === 0) { checkReminderListEmpty(0); }
        else {
            if (noRemindersText) noRemindersText.classList.add('hidden');
            reminders.forEach(reminder => { reminderList.appendChild(renderReminder(reminder)); });
            checkReminderListEmpty(reminders.length);
        }
    } catch (error) {
        console.error(error);
        if (noRemindersText) { noRemindersText.textContent = "Error loading reminders."; noRemindersText.classList.remove('hidden'); }
        checkReminderListEmpty(0);
    }
}

async function addReminder(event) {
    event.preventDefault();
    const reminderText = document.getElementById('reminderText').value.trim();
    const reminderDate = document.getElementById('reminderDate').value;
    const errorEl = document.getElementById('addReminderError');
    const successEl = document.getElementById('addReminderSuccess');
    const btn = document.getElementById('addReminderButton');

    showFeedback(errorEl, '', false); showFeedback(successEl, '', false);
    if (!reminderText || !reminderDate) { showFeedback(errorEl, 'Please fill in both fields.'); return; }

    disableButton(btn, "Adding...");
    try {
        const response = await fetch(`${backendUrl}/reminders`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: reminderText, reminder_datetime: reminderDate }), });
        const newReminder = await response.json();
        if (response.ok) {
            const reminderElement = renderReminder(newReminder);
            document.getElementById('reminderList').prepend(reminderElement);
            checkReminderListEmpty();
            document.getElementById('addReminderForm').reset();
            showFeedback(successEl, 'Reminder added successfully!', false);
        } else { showFeedback(errorEl, newReminder.error || 'Failed.'); }
    } catch (error) { console.error(error); showFeedback(errorEl, 'Error adding reminder.'); }
    finally { enableButton(btn); }
}

async function deleteReminder(event) {
    const deleteButton = event.target.closest('.delete-reminder-btn');
    if (deleteButton) {
        const reminderItem = deleteButton.closest('.reminder-item');
        const reminderId = reminderItem.dataset.id;
        if (confirm('Delete reminder?')) {
            disableButton(deleteButton, "Deleting...");
            try {
                const response = await fetch(`${backendUrl}/reminders/${reminderId}`, { method: 'DELETE' });
                if (response.ok) {
                    reminderItem.remove();
                    checkReminderListEmpty();
                } else { alert("Failed to delete."); }
            } catch (e) { alert("Network error."); }
        }
    }
}

// Faculties
async function fetchFaculties(populateDropdowns = false) {
    const tbody = document.getElementById('facultyTableBody');
    const mapSelect = document.getElementById('mapFacultySelect');
    const viewSelect = document.getElementById('viewFacultySelect');
    const countEl = document.getElementById('facultyCount');

    if (tbody) tbody.innerHTML = '<tr><td colspan="3" class="text-center text-gray-500 py-4">Loading...</td></tr>';

    try {
        const response = await fetch(`${backendUrl}/faculties`);
        const faculties = await response.json();

        if (tbody) tbody.innerHTML = '';
        if (populateDropdowns) {
            mapSelect.innerHTML = '<option value="">Select Faculty</option>';
            viewSelect.innerHTML = '<option value="">Select Faculty</option>';
        }

        if (faculties.length === 0 && tbody) { tbody.innerHTML = '<tr><td colspan="3" class="text-center text-gray-500 py-4">No faculties found.</td></tr>'; }
        else {
            faculties.forEach(f => {
                if (tbody) {
                    const row = tbody.insertRow();
                    row.innerHTML = `<td>${f.faculty_id}</td><td>${f.name}</td><td>${f.faculty_code || 'N/A'}</td>`;
                }
                if (populateDropdowns) {
                    const text = f.name + (f.faculty_code ? ` (${f.faculty_code})` : '');
                    mapSelect.add(new Option(text, f.faculty_id));
                    viewSelect.add(new Option(text, f.faculty_id));
                }
            });
        }
        if (countEl) countEl.textContent = faculties.length;
    } catch (e) { console.error(e); if (tbody) tbody.innerHTML = '<tr><td colspan="3" class="text-center text-red-500">Error.</td></tr>'; }
}

async function addFaculty(event) {
    event.preventDefault();
    const name = document.getElementById('facultyName').value.trim();
    const code = document.getElementById('facultyCode').value.trim() || null;
    const errorEl = document.getElementById('addFacultyError');
    const successEl = document.getElementById('addFacultySuccess');
    const btn = document.getElementById('addFacultyButton');

    if (!name) { showFeedback(errorEl, 'Name required.'); return; }

    disableButton(btn, "Adding...");
    try {
        const response = await fetch(`${backendUrl}/faculties`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, faculty_code: code }) });
        const res = await response.json();
        if (response.ok) {
            showFeedback(successEl, 'Added!', false);
            document.getElementById('addFacultyForm').reset();
            fetchFaculties(true);
        } else { showFeedback(errorEl, res.error || 'Failed.'); }
    } catch (e) { showFeedback(errorEl, 'Error.'); }
    finally { enableButton(btn); }
}

// Subjects
async function fetchSubjects(populateDropdown = false) {
    const tbody = document.getElementById('subjectTableBody');
    const mapSelect = document.getElementById('mapSubjectSelect');
    const countEl = document.getElementById('subjectCount');

    if (tbody) tbody.innerHTML = '<tr><td colspan="4" class="text-center text-gray-500 py-4">Loading...</td></tr>';

    try {
        const response = await fetch(`${backendUrl}/subjects`);
        const subjects = await response.json();

        if (tbody) tbody.innerHTML = '';
        if (populateDropdown) mapSelect.innerHTML = '<option value="">Select Subject</option>';

        if (subjects.length === 0 && tbody) { tbody.innerHTML = '<tr><td colspan="4" class="text-center text-gray-500">No subjects.</td></tr>'; }
        else {
            subjects.forEach(s => {
                if (tbody) {
                    const row = tbody.insertRow();
                    row.innerHTML = `<td>${s.subject_id}</td><td>${s.code}</td><td>${s.name}</td><td>${s.is_lab ? 'Yes' : 'No'}</td>`;
                }
                if (populateDropdown) {
                    mapSelect.add(new Option(`${s.name} (${s.code})`, s.subject_id));
                }
            });
        }
        if (countEl) countEl.textContent = subjects.length;
    } catch (e) { if (tbody) tbody.innerHTML = '<tr><td colspan="4" class="text-center text-red-500">Error.</td></tr>'; }
}

async function addSubject(event) {
    event.preventDefault();
    const code = document.getElementById('subjectCode').value.trim();
    const name = document.getElementById('subjectName').value.trim();
    const isLab = document.getElementById('subjectIsLab').checked;
    const errorEl = document.getElementById('addSubjectError');
    const successEl = document.getElementById('addSubjectSuccess');
    const btn = document.getElementById('addSubjectButton');

    if (!code || !name) { showFeedback(errorEl, 'Code & Name required.'); return; }

    disableButton(btn, "Adding...");
    try {
        const response = await fetch(`${backendUrl}/subjects`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, name, is_lab: isLab }) });
        const res = await response.json();
        if (response.ok) { showFeedback(successEl, 'Added!', false); document.getElementById('addSubjectForm').reset(); fetchSubjects(true); }
        else { showFeedback(errorEl, res.error || 'Failed.'); }
    } catch (e) { showFeedback(errorEl, 'Error.'); }
    finally { enableButton(btn); }
}

// Mappings
async function addFacultySubjectMapping(event) {
    event.preventDefault();
    const facId = document.getElementById('mapFacultySelect').value;
    const subId = document.getElementById('mapSubjectSelect').value;
    const errorEl = document.getElementById('addMappingError');
    const successEl = document.getElementById('addMappingSuccess');
    const btn = document.getElementById('addMappingButton');

    if (!facId || !subId) { showFeedback(errorEl, 'Select both.'); return; }

    disableButton(btn, "Assigning...");
    try {
        const response = await fetch(`${backendUrl}/faculty-subjects`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ faculty_id: facId, subject_id: subId }) });
        if (response.ok) {
            showFeedback(successEl, 'Assigned!', false);
            document.getElementById('mapSubjectSelect').value = "";
            const viewSelect = document.getElementById('viewFacultySelect');
            if (viewSelect.value === facId) displaySubjectsForFaculty(facId);
        } else { showFeedback(errorEl, 'Failed.'); }
    } catch (e) { showFeedback(errorEl, 'Error.'); }
    finally { enableButton(btn); }
}

async function displaySubjectsForFaculty(facId) {
    const list = document.getElementById('assignedSubjectsList');
    const placeholder = document.getElementById('assignmentsPlaceholder');

    list.innerHTML = ''; list.classList.add('hidden');
    placeholder.textContent = 'Loading...'; placeholder.classList.remove('hidden');

    if (!facId) { placeholder.textContent = 'Select faculty.'; return; }

    try {
        const response = await fetch(`${backendUrl}/faculty-subjects/${facId}`);
        const subjects = await response.json();

        if (subjects.length === 0) { placeholder.textContent = 'No assignments.'; }
        else {
            placeholder.classList.add('hidden');
            subjects.forEach(s => {
                const li = document.createElement('li');
                li.className = 'flex justify-between items-center text-sm py-1';
                li.innerHTML = `<span>${s.name} (${s.code})</span> <button class="delete-mapping-btn table-button delete-button" data-faculty-id="${facId}" data-subject-id="${s.subject_id}">Delete</button>`;
                list.appendChild(li);
            });
            list.classList.remove('hidden');
        }
    } catch (e) { placeholder.textContent = 'Error.'; }
}

async function deleteFacultySubjectMapping(event) {
    const btn = event.target.closest('.delete-mapping-btn');
    if (!btn) return;
    if (!confirm('Remove assignment?')) return;

    const facId = btn.dataset.facultyId;
    const subId = btn.dataset.subjectId;
    disableButton(btn, "Deleting...");

    try {
        const response = await fetch(`${backendUrl}/faculty-subjects/${facId}/${subId}`, { method: 'DELETE' });
        if (response.ok) { btn.closest('li').remove(); }
        else { alert("Failed."); enableButton(btn); }
    } catch (e) { alert("Error."); enableButton(btn); }
}

// Branches/Sections/Classes (Simplified for brevity, similar pattern)
async function fetchBranches() {
    const tbody = document.getElementById('branchTableBody');
    const select = document.getElementById('classBranchSelect');
    if (tbody) tbody.innerHTML = '<tr><td>Loading...</td></tr>';
    try {
        const res = await fetch(`${backendUrl}/branches`);
        const data = await res.json();
        if (tbody) tbody.innerHTML = '';
        if (select) select.innerHTML = '<option value="">Select Branch</option>';
        data.forEach(b => {
            if (tbody) tbody.insertRow().innerHTML = `<td>${b.branch_id}</td><td>${b.name}</td><td>${b.code || ''}</td>`;
            if (select) select.add(new Option(b.name, b.branch_id));
        });
    } catch (e) { }
}
async function addBranch(e) {
    e.preventDefault();
    const name = document.getElementById('branchName').value;
    const code = document.getElementById('branchCode').value;
    await fetch(`${backendUrl}/branches`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, code }) });
    document.getElementById('addBranchForm').reset(); fetchBranches();
}

async function fetchSections() {
    const tbody = document.getElementById('sectionTableBody');
    const select = document.getElementById('classSectionSelect');
    if (tbody) tbody.innerHTML = '<tr><td>Loading...</td></tr>';
    try {
        const res = await fetch(`${backendUrl}/sections`);
        const data = await res.json();
        if (tbody) tbody.innerHTML = '';
        if (select) select.innerHTML = '<option value="">Select Section</option>';
        data.forEach(s => {
            if (tbody) tbody.insertRow().innerHTML = `<td>${s.section_id}</td><td>${s.name}</td>`;
            if (select) select.add(new Option(s.name, s.section_id));
        });
    } catch (e) { }
}
async function addSection(e) {
    e.preventDefault();
    const name = document.getElementById('sectionName').value;
    await fetch(`${backendUrl}/sections`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
    document.getElementById('addSectionForm').reset(); fetchSections();
}

async function fetchClasses() {
    const tbody = document.getElementById('classTableBody');
    if (tbody) tbody.innerHTML = '<tr><td>Loading...</td></tr>';
    try {
        const res = await fetch(`${backendUrl}/classes`);
        const data = await res.json();
        if (tbody) tbody.innerHTML = '';
        data.forEach(c => {
            if (tbody) tbody.insertRow().innerHTML = `<td>${c.class_id}</td><td>${c.class_name || ''}</td><td>${c.branch_name}</td><td>${c.section_name}</td><td>${c.year}</td>`;
        });
    } catch (e) { }
}
async function addClass(e) {
    e.preventDefault();
    const branch_id = document.getElementById('classBranchSelect').value;
    const section_id = document.getElementById('classSectionSelect').value;
    const year = document.getElementById('classYear').value;
    const class_name = document.getElementById('className').value;
    await fetch(`${backendUrl}/classes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ branch_id, section_id, year, class_name }) });
    document.getElementById('addClassForm').reset(); fetchClasses();
}

async function handleGenerateTimetable() {
    if (!confirm("Generate new timetable (overwriting old one)?")) return;
    const link = document.getElementById('generateTimetableLink');
    if (link) link.textContent = "Generating...";
    try {
        const res = await fetch(`${backendUrl}/generate-timetable`, { method: 'POST' });
        const data = await res.json();
        alert(data.message);
    } catch (e) { alert("Error generating."); }
    if (link) link.textContent = "Generate Timetable";
}
