// --- STATE MANAGEMENT ---
let emails = [];
let activeEmailId = null;
let activeCategory = 'all';
let selectedEmailIds = new Set();

// --- ICONS ---
const icons = {
    all: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2"></path><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path></svg>`,
    primary: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L8.6 3.3a2 2 0 0 0-1.7-1H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h16z"></path></svg>`,
    spam: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
    default: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>`,
    delete: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="delete-icon"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`
};

// --- INITIALIZATION & EVENT LISTENERS ---
document.addEventListener('DOMContentLoaded', function() {
    initializePage();

    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', handleSearch);

    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    selectAllCheckbox.addEventListener('change', handleSelectAll);

    const bulkMoveBtn = document.getElementById('bulk-move-btn');
    bulkMoveBtn.addEventListener('click', handleBulkMove);

    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.addEventListener('click', handleRefreshClick);

    const profileSection = document.getElementById('profile-section');
    const dropdown = document.getElementById('profile-dropdown');
    if (profileSection && dropdown) {
        profileSection.addEventListener('click', (event) => {
            event.stopPropagation();
            dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
        });
        window.addEventListener('click', () => {
            if (dropdown.style.display === 'block') dropdown.style.display = 'none';
        });
    }
});

async function initializePage() {
    await fetchEmails();
    await renderFolders();
    renderEmailList();
}

// --- DATA FETCHING ---
async function fetchEmails() {
    try {
        const response = await fetch(`/get_emails?t=${new Date().getTime()}`);
        emails = await response.json();
    } catch (error) { console.error('Error fetching emails:', error); }
}

// --- EVENT HANDLERS ---
function handleDragStart(e) { e.dataTransfer.setData('text/plain', e.target.dataset.id); }
function handleDragOver(e) { e.preventDefault(); }
function handleDrop(e) {
    e.preventDefault();
    const emailId = parseInt(e.dataTransfer.getData('text/plain'));
    const targetFolder = e.currentTarget.dataset.category;
    const email = emails.find(em => em.id === emailId);
    if (email && targetFolder && targetFolder !== 'all') {
        learnAndUpdate(email.id, targetFolder);
    }
}

let searchDebounceTimer;
function handleSearch(event) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(async () => {
        const query = event.target.value.trim();
        if (query.length > 1) {
            try {
                const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
                const searchResults = await response.json();
                renderEmailList(searchResults);
            } catch (error) { console.error('Search error:', error); }
        } else if (query.length === 0) {
            renderEmailList();
        }
    }, 300);
}

function handleEmailSelect(emailId, checkbox) {
    if (checkbox.checked) {
        selectedEmailIds.add(emailId);
    } else {
        selectedEmailIds.delete(emailId);
    }
    updateBulkActionsToolbar();
}

function handleSelectAll(event) {
    const isChecked = event.target.checked;
    const emailCheckboxes = document.querySelectorAll('.email-item-checkbox');
    selectedEmailIds.clear();
    const filteredEmails = getFilteredEmails();
    if (isChecked) {
        filteredEmails.forEach(email => selectedEmailIds.add(email.id));
    }
    emailCheckboxes.forEach(cb => cb.checked = isChecked);
    updateBulkActionsToolbar();
}

async function handleBulkMove() {
    const categoriesResponse = await fetch('/get_categories');
    const data = await categoriesResponse.json();
    const categories = data.categories.join(', ');
    const targetCategory = prompt(`Move ${selectedEmailIds.size} emails to which folder?\n\nAvailable: ${categories}`);
    
    if (targetCategory && data.categories.includes(targetCategory.toLowerCase())) {
        try {
            await fetch('/bulk_update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email_ids: Array.from(selectedEmailIds), category: targetCategory.toLowerCase() })
            });
            selectedEmailIds.clear();
            await initializePage();
            document.getElementById('email-view-pane').innerHTML = '<p>Select an email to view its content.</p>';
        } catch (error) { console.error('Bulk move error:', error); }
    } else if (targetCategory) {
        alert('Invalid category name.');
    }
}

async function handleRefreshClick() {
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.classList.add('loading');
    try {
        await fetch('/refresh_emails', { method: 'POST' });
        await initializePage();
    } catch (error) {
        console.error('Refresh error:', error);
        alert('An error occurred while refreshing.');
    } finally {
        refreshBtn.classList.remove('loading');
    }
}

// --- HELPER to get currently visible emails ---
function getFilteredEmails() {
    if (activeCategory === 'all') return emails;
    if (activeCategory === 'primary') return emails.filter(e => e.category !== 'spam');
    return emails.filter(e => e.category === activeCategory);
}

async function renderFolders() {
    try {
        const response = await fetch(`/get_categories?t=${new Date().getTime()}`);
        const data = await response.json();
        const folderList = document.getElementById('folder-list');
        folderList.innerHTML = '';

        // --- THIS IS THE UPDATED LOGIC ---
        // Calculate total counts for the "All" folder
        const all_total = emails.length;
        const all_unread = emails.filter(e => !e.is_read).length;

        const allFolder = document.createElement('li');
        allFolder.innerHTML = `
            <div class="folder-name">${icons.all} All</div>
            <span class="folder-count">${all_unread} / ${all_total}</span>
        `;
        allFolder.dataset.category = 'all';
        allFolder.onclick = () => selectFolder('all');
        allFolder.addEventListener('dragover', handleDragOver);
        allFolder.addEventListener('drop', handleDrop);
        folderList.appendChild(allFolder);

        data.categories.forEach(category => {
            const li = document.createElement('li');
            const icon = icons[category.name] || icons.default;
            let deleteButtonHTML = '';
            if (category.name !== 'primary' && category.name !== 'spam') {
                deleteButtonHTML = `<span class="delete-btn" onclick="event.stopPropagation(); deleteCategory('${category.name}');">${icons.delete}</span>`;
            }
            
            li.innerHTML = `
                <div class="folder-name">${icon} ${category.name.charAt(0).toUpperCase() + category.name.slice(1)}</div>
                <span class="folder-count">${category.unread_count} / ${category.total_count}</span>
                ${deleteButtonHTML}
            `;
            li.dataset.category = category.name;
            li.onclick = () => selectFolder(category.name);
            li.addEventListener('dragover', handleDragOver);
            li.addEventListener('drop', handleDrop);
            folderList.appendChild(li);
        });
        const activeFolder = document.querySelector(`.folder-list li[data-category='${activeCategory}']`);
        if (activeFolder) activeFolder.classList.add('active');
    } catch (error) { console.error('Error fetching categories:', error); }
}

async function displayEmail(emailId) {
    activeEmailId = emailId;
    const email = emails.find(e => e.id === emailId);
    if (!email) return;

    // --- THIS IS THE UPDATED LOGIC ---
    // Mark the email as read in our local data and refresh the folder counts
    if (!email.is_read) {
        email.is_read = true;
        renderFolders();
    }

    document.querySelectorAll('.email-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`.email-item[data-id='${emailId}']`).classList.add('active');

    const emailViewPane = document.getElementById('email-view-pane');
    
    // Fetch the pre-rendered HTML from the server (this also marks it as read on the backend)
    try {
        const response = await fetch(`/email_content/${email.id}`);
        const htmlContent = await response.text();
        const prediction = await classifyEmail(email.body);

        emailViewPane.innerHTML = `
            <div class="email-header">
                <h2>${email.subject}</h2>
                <span class="email-category-tag">${email.category.toUpperCase()}</span>
            </div>
            <p><strong>From:</strong> ${email.from}</p>
            <div class="email-body-iframe">${htmlContent}</div> 
            <div class="ai-actions">
                <h3>AI Analysis</h3>
                <div id="ai-prediction" class="ai-prediction ${prediction}">AI's First Guess: ${prediction.toUpperCase()}</div>
                <div class="correction-controls" data-email-id="${email.id}">
                    <p>Is this wrong? Correct it:</p>
                    <button data-label="primary">Move to Primary</button>
                    <button data-label="spam">Move to Spam</button>
                    <br><br>
                    <input type="text" id="custom-category-input" placeholder="Or a new category...">
                    <button id="learn-custom-btn">Learn Custom</button>
                </div>
            </div>
        `;

        const controls = emailViewPane.querySelector('.correction-controls');
        controls.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                const emailId = parseInt(controls.dataset.emailId);
                let label;
                if (e.target.id === 'learn-custom-btn') {
                    label = document.getElementById('custom-category-input').value.trim().toLowerCase();
                } else {
                    label = e.target.dataset.label;
                }
                if (label) {
                    learnAndUpdate(emailId, label);
                }
            }
        });
    } catch (error) {
        console.error('Error fetching email content:', error);
    }
}

function selectFolder(category) {
    activeCategory = category;
    document.getElementById('search-input').value = '';
    selectedEmailIds.clear();
    initializePage();
}

function renderEmailList(emailsToRender = null) {
    const emailListContent = document.getElementById('email-list-content');
    emailListContent.innerHTML = '';
    
    const filteredEmails = emailsToRender !== null ? emailsToRender : getFilteredEmails();

    if (filteredEmails.length === 0) {
        emailListContent.innerHTML = '<p style="padding: 20px; color: #627D98;">No emails found.</p>';
        return;
    }

    filteredEmails.forEach(email => {
        const item = document.createElement('div');
        item.className = 'email-item';
        item.dataset.id = email.id;
        
        item.innerHTML = `
            <input type="checkbox" class="email-item-checkbox" onchange="handleEmailSelect(${email.id}, this)">
            <div class="email-item-details">
                <div class="from">${email.from}</div>
                <div class="subject">${email.subject}</div>
            </div>
        `;
        item.querySelector('.email-item-details').onclick = () => displayEmail(email.id);
        item.draggable = true;
        item.addEventListener('dragstart', handleDragStart);
        emailListContent.appendChild(item);
    });
    updateBulkActionsToolbar();
}



// --- API & UPDATE FUNCTIONS ---
async function classifyEmail(emailText) {
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email_text: emailText })
        });
        const data = await response.json();
        return data.prediction;
    } catch (error) { console.error('Error:', error); return 'Error'; }
}

async function learnAndUpdate(emailId, correctLabel) {
    const email = emails.find(e => e.id === emailId);
    if (!email) return;

    try {
        await fetch('/learn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                email_id: emailId,
                email_text: email.body, 
                correct_label: correctLabel 
            })
        });
        
        await initializePage();
        
        if (activeEmailId === emailId) {
            displayEmail(activeEmailId);
        }

    } catch (error) { console.error('Error:', error); }
}

async function deleteCategory(category) {
    if (!confirm(`Are you sure you want to delete the "${category}" folder? Emails in this folder will be moved to Primary.`)) {
        return;
    }
    try {
        const response = await fetch('/delete_category', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category: category })
        });
        const data = await response.json();
        if (response.ok) {
            activeCategory = 'all';
            await initializePage();
            document.getElementById('email-view-pane').innerHTML = '<p>Select an email to view its content.</p>';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Error deleting category:', error);
    }
}