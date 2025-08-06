// --- STATE MANAGEMENT ---
let emails = []; // Will hold emails fetched from the server
let activeEmailId = null;
let activeCategory = 'all';

// --- ICONS ---
const icons = {
    all: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2"></path><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path></svg>`,
    primary: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L8.6 3.3a2 2 0 0 0-1.7-1H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h16z"></path></svg>`,
    spam: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
    default: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>`
};

// --- INITIALIZATION ---
window.onload = async function() {
    await fetchEmails();
    renderFolders();
    renderEmailList();
};

// --- DATA FETCHING ---
async function fetchEmails() {
    try {
        const response = await fetch('/get_emails');
        emails = await response.json();
    } catch (error) {
        console.error('Error fetching emails:', error);
    }
}

// --- DRAG & DROP HANDLERS ---
function handleDragStart(e) {
    e.dataTransfer.setData('text/plain', e.target.dataset.id);
}
function handleDragOver(e) {
    e.preventDefault();
}
function handleDrop(e) {
    e.preventDefault();
    const emailId = parseInt(e.dataTransfer.getData('text/plain'));
    const targetFolder = e.currentTarget.dataset.category;
    const email = emails.find(em => em.id === emailId);
    if (email && targetFolder !== 'all') {
        learnAndUpdate(email.id, email.body, targetFolder);
    }
}

// --- RENDERING FUNCTIONS ---
async function renderFolders() {
    try {
        const response = await fetch('/get_categories');
        const data = await response.json();
        const folderList = document.getElementById('folder-list');
        folderList.innerHTML = '';

        const allFolder = document.createElement('li');
        allFolder.innerHTML = `${icons.all} All`;
        allFolder.dataset.category = 'all';
        allFolder.onclick = () => selectFolder('all');
        allFolder.ondragover = handleDragOver;
        allFolder.ondrop = handleDrop;
        folderList.appendChild(allFolder);

        data.categories.forEach(category => {
            const li = document.createElement('li');
            const icon = icons[category] || icons.default;
            li.innerHTML = `${icon} ${category.charAt(0).toUpperCase() + category.slice(1)}`;
            li.dataset.category = category;
            li.onclick = () => selectFolder(category);
            li.ondragover = handleDragOver;
            li.ondrop = handleDrop;
            folderList.appendChild(li);
        });
        document.querySelector(`.folder-list li[data-category='${activeCategory}']`).classList.add('active');
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
    const filteredEmails = activeCategory === 'all'
        ? emails
        : emails.filter(email => email.category === activeCategory);

    filteredEmails.forEach(email => {
        const item = document.createElement('div');
        item.className = 'email-item';
        item.dataset.id = email.id;
        item.draggable = true;
        item.ondragstart = handleDragStart;
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

    // --- THIS IS THE FIX ---
    // The "AI Analysis" box now clearly states the AI's original guess.
    // The tag at the top right always shows the TRUE, saved category.
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
            <div class="correction-controls">
                <p>Is this wrong? Correct it:</p>
                <button onclick="learnAndUpdate(${email.id}, '${email.body.replace(/'/g, "\\'")}', 'primary')">Move to Primary</button>
                <button onclick="learnAndUpdate(${email.id}, '${email.body.replace(/'/g, "\\'")}', 'spam')">Move to Spam</button>
                <br><br>
                <input type="text" id="custom-category-input" placeholder="Or a new category...">
                <button onclick="learnCustomAndUpdate(${email.id}, '${email.body.replace(/'/g, "\\'")}')">Learn Custom</button>
            </div>
        </div>
    `;
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

function learnCustomAndUpdate(emailId, emailText) {
    const customLabel = document.getElementById('custom-category-input').value;
    if (customLabel.trim()) {
        learnAndUpdate(emailId, emailText, customLabel.trim().toLowerCase());
    }
}

async function learnAndUpdate(emailId, emailText, correctLabel) {
    try {
        const response = await fetch('/learn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                email_id: emailId,
                email_text: emailText, 
                correct_label: correctLabel 
            })
        });
        const data = await response.json();
        alert(data.message);
        
        // Fetch fresh data from the server to ensure UI is in sync
        await fetchEmails();
        await renderFolders();
        renderEmailList();
        
        // Re-display the email to show the updated category tag
        displayEmail(emailId);

    } catch (error) { console.error('Error:', error); }
}