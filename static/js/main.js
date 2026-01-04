
// --- Global Variables ---
const backendUrl = '/api';
const sections = document.querySelectorAll('.app-section');
const navLinks = document.querySelectorAll('.nav-link');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');

// --- Elements ---
const loginSection = document.getElementById('loginSection');
const signUpSection = document.getElementById('signUpSection');
const loggedInSection = document.getElementById('loggedInContent');
const reminderList = document.getElementById('reminderList');

// --- Main Logic ---

function hideAllSections() {
    sections.forEach(section => {
        section.style.display = 'none';
        section.classList.remove('active-section');
    });
}

function showSection(sectionId) {
    hideAllSections();
    const sectionToShow = document.getElementById(sectionId);
    if (sectionToShow) {
        const displayStyle = (sectionId === 'loginSection' || sectionId === 'signUpSection') ? 'flex' : 'block';
        sectionToShow.style.display = displayStyle;
        requestAnimationFrame(() => sectionToShow.classList.add('active-section'));

        switch (sectionId) {
            case 'manageFacultiesSection': fetchFaculties(); break;
            case 'manageSubjectsSection': fetchSubjects(); break;
            case 'manageMappingsSection': fetchFaculties(true); fetchSubjects(true); break;
            case 'manageBranchesSection': fetchBranches(); break;
            case 'manageSectionsSection': fetchSections(); break;
            case 'manageClassesSection': fetchClasses(); fetchBranches(true); fetchSections(true); break;
            case 'remindersSection': fetchReminders(); break;
            case 'homeSection': updateDashboardCounts(); break;
        }
    }
}

function updateNavLinks(activeSectionId) {
    navLinks.forEach(link => link.classList.toggle('active', link.dataset.section === activeSectionId));
}

// --- Auth Functions ---

async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const loginErrorEl = document.getElementById('loginError');
    const loginSubmitButton = document.getElementById('loginSubmitButton');

    loginErrorEl.textContent = '';
    disableButton(loginSubmitButton, "Signing In...");
    try {
        const response = await fetch(`${backendUrl}/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }), });
        const data = await response.json();
        if (response.ok) {
            loginSection.style.display = 'none'; loginSection.classList.remove('active-section');
            signUpSection.style.display = 'none'; signUpSection.classList.remove('active-section');
            loggedInSection.classList.remove('hidden');
            showSection('homeSection');
            updateNavLinks('home');
            fetchReminders();
            updateDashboardCounts();
            if (window.innerWidth >= 768) { sidebar.classList.remove('-translate-x-full'); sidebar.classList.add('md:relative', 'md:translate-x-0'); }
        } else { showFeedback(loginErrorEl, data.error || 'Login failed.'); }
    } catch (error) { console.error(error); showFeedback(loginErrorEl, 'An error occurred.'); }
    finally { enableButton(loginSubmitButton); }
}

async function handleSignUp(event) {
    event.preventDefault();
    const name = document.getElementById('signUpName').value;
    const email = document.getElementById('signUpEmail').value;
    const password = document.getElementById('signUpPassword').value;
    const confirmPassword = document.getElementById('signUpConfirmPassword').value;
    const signUpErrorEl = document.getElementById('signUpError');
    const signUpSubmitButton = document.getElementById('signUpSubmitButton');

    signUpErrorEl.textContent = '';
    if (password !== confirmPassword) { showFeedback(signUpErrorEl, 'Passwords do not match.'); return; }

    disableButton(signUpSubmitButton, "Signing Up...");
    try {
        const response = await fetch(`${backendUrl}/signup`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, email, password }), });
        const data = await response.json();
        if (response.ok) {
            alert('Sign up successful! Please log in.');
            showSection('loginSection');
            loggedInSection.classList.add('hidden');
            document.getElementById('signUpForm').reset();
        } else { showFeedback(signUpErrorEl, data.error || 'Sign up failed.'); }
    } catch (error) { console.error(error); showFeedback(signUpErrorEl, 'An error occurred.'); }
    finally { enableButton(signUpSubmitButton); }
}

function handleLogout() {
    loggedInSection.classList.add('hidden');
    hideAllSections();
    showSection('loginSection');
    updateNavLinks(null);
    document.getElementById('loginForm').reset();
    closeMobileSidebar();
}

// --- Sidebar ---
function openMobileSidebar() {
    sidebar.classList.remove('-translate-x-full');
    sidebarOverlay.classList.remove('hidden');
}
function closeMobileSidebar() {
    sidebar.classList.add('-translate-x-full');
    sidebarOverlay.classList.add('hidden');
}

// --- Initial Setup & Listeners ---

document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    navLinks.forEach(link => link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetSection = e.currentTarget.dataset.section;
        if (targetSection) {
            showSection(targetSection + 'Section');
            updateNavLinks(targetSection);
            if (window.innerWidth < 768) closeMobileSidebar();
        }
    }));

    // Auth
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('signUpForm').addEventListener('submit', handleSignUp);
    document.getElementById('showSignUp').addEventListener('click', (e) => { e.preventDefault(); showSection('signUpSection'); });
    document.getElementById('showLogin').addEventListener('click', (e) => { e.preventDefault(); showSection('loginSection'); });
    document.getElementById('logoutButton').addEventListener('click', (e) => { e.preventDefault(); handleLogout(); });

    // Forms
    document.getElementById('addReminderForm').addEventListener('submit', addReminder);
    document.getElementById('addFacultyForm').addEventListener('submit', addFaculty);
    document.getElementById('addSubjectForm').addEventListener('submit', addSubject);
    document.getElementById('addMappingForm').addEventListener('submit', addFacultySubjectMapping);
    document.getElementById('addBranchForm').addEventListener('submit', addBranch);
    document.getElementById('addSectionForm').addEventListener('submit', addSection);
    document.getElementById('addClassForm').addEventListener('submit', addClass);

    // Lists
    reminderList.addEventListener('click', deleteReminder);
    document.getElementById('assignedSubjectsList').addEventListener('click', deleteFacultySubjectMapping);
    document.getElementById('viewFacultySelect').addEventListener('change', (e) => displaySubjectsForFaculty(e.target.value));

    // Timetable
    document.getElementById('generateTimetableLink').addEventListener('click', (e) => {
        e.preventDefault();
        handleGenerateTimetable();
    });

    // Mobile Sidebar
    document.getElementById('openSidebarBtn').addEventListener('click', openMobileSidebar);
    document.getElementById('closeSidebarBtn').addEventListener('click', closeMobileSidebar);
    sidebarOverlay.addEventListener('click', closeMobileSidebar);

    // Init
    hideAllSections();
    loggedInSection.classList.add('hidden');
    showSection('loginSection');
    checkReminderListEmpty(0);
    checkNotificationListEmpty();
});

// --- Placeholder for Dashboard ---
async function updateDashboardCounts() { }
