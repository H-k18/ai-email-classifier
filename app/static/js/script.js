// --- STATE MANAGEMENT ---
let emails = [];
let activeEmailId = null;
let activeCategory = 'all';

// --- ICONS ---
const icons = {
    all: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2"></path><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path></svg>`,
    primary: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L8.6 3.3a2 2 0 0 0-1.7-1H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h16z"></path></svg>`,
    spam: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
    default: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>`,
    delete: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="delete-icon"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`
};

// --- INITIALIZATION ---
window.onload = async function() {
    await fetchAndRenderAll();
};

async function fetchAndRenderAll() {
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

// --- DRAG & DROP HANDLERS ---
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

// --- RENDERING FUNCTIONS ---
async function renderFolders() {
    try {
        const response = await fetch(`/get_categories?t=${new Date().getTime()}`);
        const data = await response.json();
        const folderList = document.getElementById('folder-list');
        folderList.innerHTML = '';

        const allFolder = document.createElement('li');
        allFolder.innerHTML = `<div>${icons.all} All</div>`;
        allFolder.dataset.category = 'all';
        allFolder.onclick = () => selectFolder('all');
        folderList.appendChild(allFolder);

        data.categories.forEach(category => {
            const li = document.createElement('li');
            const icon = icons[category] || icons.default;
            let deleteButtonHTML = '';
            
            if (category !== 'primary' && category !== 'spam') {
                deleteButtonHTML = `<span class="delete-btn" onclick="event.stopPropagation(); deleteCategory('${category}');">${icons.delete}</span>`;
            }
            
            li.innerHTML = `<div>${icon} ${category.charAt(0).toUpperCase() + category.slice(1)}</div> ${deleteButtonHTML}`;
            li.dataset.category = category;
            li.onclick = () => selectFolder(category);
            li.addEventListener('dragover', handleDragOver);
            li.addEventListener('drop', handleDrop);
            folderList.appendChild(li);
        });
        const activeFolder = document.querySelector(`.folder-list li[data-category='${activeCategory}']`);
        if (activeFolder) activeFolder.classList.add('active');
    } catch (error) { console.error('Error fetching categories:', error); }
}

function selectFolder(category) {
    activeCategory = category;
    renderFolders();
    renderEmailList();
}

function renderEmailList() {
    const emailListPane = document.getElementById('email-list-pane');
    emailListPane.innerHTML = '';
    const filteredEmails = activeCategory === 'all' ? emails : emails.filter(email => email.category === activeCategory);

    filteredEmails.forEach(email => {
        const item = document.createElement('div');
        item.className = 'email-item';
        item.dataset.id = email.id;
        item.draggable = true;
        item.addEventListener('dragstart', handleDragStart);
        item.innerHTML = `<div class="from">${email.from}</div><div class="subject">${email.subject}</div>`;
        item.onclick = () => displayEmail(email.id);
        emailListPane.appendChild(item);
    });
}

async function displayEmail(emailId) {
    activeEmailId = emailId;
    const email = emails.find(e => e.id === emailId);
    if (!email) return;

    document.querySelectorAll('.email-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`.email-item[data-id='${emailId}']`).classList.add('active');

    const emailViewPane = document.getElementById('email-view-pane');
    const prediction = await classifyEmail(email.body);

    emailViewPane.innerHTML = `
        <div class="email-header">
            <h2>${email.subject}</h2>
            <span class="email-category-tag">${email.category.toUpperCase()}</span>
        </div>
        <p><strong>From:</strong> ${email.from}</p>
        <div class="email-body">${email.body}</div>
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
        
        await fetchAndRenderAll();
        
        if (activeEmailId === emailId) {
            displayEmail(activeEmailId);
        }

    } catch (error) { console.error('Error:', error); }
}

// --- THIS IS THE MISSING FUNCTION ---
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
            await fetchAndRenderAll();
            document.getElementById('email-view-pane').innerHTML = '<p>Select an email to view its content.</p>';
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Error deleting category:', error);
    }
}