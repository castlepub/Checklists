// Global variables
let signaturePad;
let currentChores = [];
let choreUpdateQueue = [];
let isProcessingQueue = false;
let selectedStaff = null;
let completedChores = new Set();
let completedSections = new Set();
let totalChores = 0;
let completedCount = 0;

// Add achievements container to the body
const achievementsContainer = document.createElement('div');
achievementsContainer.id = 'achievementsContainer';
document.body.appendChild(achievementsContainer);

const encouragements = [
    { threshold: 0, emoji: "🌱", message: "Let's get started!" },
    { threshold: 0.25, emoji: "🌿", message: "Great progress!" },
    { threshold: 0.50, emoji: "🌳", message: "Halfway there!" },
    { threshold: 0.75, emoji: "🌺", message: "Almost done!" },
    { threshold: 1, emoji: "🎉", message: "Amazing work!" }
];

const funFacts = [
    "Did you know? The oldest pub in England is Ye Olde Man & Scythe in Bolton, dating back to 1251!",
    "The world's strongest beer is 'Snake Venom' at 67.5% alcohol by volume!",
    "The first beer was brewed in Mesopotamia around 4000 BC!",
    "The most expensive beer ever sold was a bottle of 'Allsopp's Arctic Ale' for $503,300!",
    "The longest bar in the world is in New Orleans, measuring 130.6 meters!",
    "The first Oktoberfest was actually a wedding celebration for Crown Prince Ludwig in 1810!",
    "The term 'pub' comes from 'public house'!",
    "The world's largest beer festival is Oktoberfest in Munich!",
    "The first beer cans were introduced in 1935!",
    "The world's most popular beer style is lager!"
];

let lastFunFactIndex = -1;
let achievementsShown = new Set();
let lastProgressThreshold = 0;

function getRandomFunFact() {
    let index;
    do {
        index = Math.floor(Math.random() * funFacts.length);
    } while (index === lastFunFactIndex);
    lastFunFactIndex = index;
    return funFacts[index];
}

function showAchievement(title, message, type = 'milestone') {
    const achievementId = `${title}-${message}`;
    if (achievementsShown.has(achievementId)) return;
    achievementsShown.add(achievementId);
    
    const achievement = document.createElement('div');
    achievement.className = `achievement ${type}`;
    achievement.innerHTML = `
        <div class="achievement-content">
            <div class="achievement-emoji">${type === 'fun-fact' ? '💡' : '🏆'}</div>
            <div class="achievement-message">
                <strong>${title}</strong><br>
                ${message}
            </div>
        </div>
    `;
    
    achievementsContainer.appendChild(achievement);
    
    // Animate in
    requestAnimationFrame(() => {
        achievement.classList.add('show');
    });
    
    // Add click to dismiss
    achievement.addEventListener('click', () => {
        achievement.classList.remove('show');
        setTimeout(() => {
            achievement.remove();
            achievementsShown.delete(achievementId);
        }, 500);
    });
    
    // Auto-dismiss after 10 seconds for fun facts, 15 seconds for milestones
    const timeout = type === 'fun-fact' ? 10000 : 15000;
    setTimeout(() => {
        if (achievement.isConnected) {
            achievement.classList.remove('show');
            setTimeout(() => {
                if (achievement.isConnected) {
                    achievement.remove();
                    achievementsShown.delete(achievementId);
                }
            }, 500);
        }
    }, timeout);
}

function updateProgressIndicator() {
    const progressBar = document.getElementById('progressBar');
    if (!progressBar) return;
    
    const totalChores = currentChores.length;
    if (totalChores === 0) return;
    
    const completedChores = currentChores.filter(chore => chore.completed).length;
    const progress = completedChores / totalChores;
    
    // Find the appropriate encouragement
    const encouragement = encouragements
        .slice()
        .reverse()
        .find(e => progress >= e.threshold);
    
    // Update the progress display
    const progressDisplay = document.getElementById('progressDisplay');
    if (!progressDisplay) return;
    
    // Update content
    progressDisplay.innerHTML = `
        <div class="progress-emoji">${encouragement.emoji}</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${progress * 100}%"></div>
        </div>
        <div class="progress-text">
            ${encouragement.message}<br>
            <small>${completedChores} of ${totalChores} tasks done</small>
        </div>
    `;
    
    // Add bounce animation to emoji when threshold changes
    if (encouragement.threshold > lastProgressThreshold) {
        const emoji = progressDisplay.querySelector('.progress-emoji');
        emoji.classList.add('bounce');
        setTimeout(() => emoji.classList.remove('bounce'), 1000);
    }
    lastProgressThreshold = encouragement.threshold;
    
    // Show achievements for milestones
    if (progress >= 0.25 && progress < 0.5) {
        showAchievement("Quarter Way Hero! 🌟", "Keep up the great work!");
    }
    if (progress >= 0.5 && progress < 0.75) {
        showAchievement("Halfway Champion! 🏆", "You're crushing it!");
    }
    if (progress >= 0.75 && progress < 1) {
        showAchievement("Almost There! ⭐", "The finish line is in sight!");
    }
    if (progress === 1) {
        showAchievement("Checklist Master! 👑", "You've completed everything!");
    }
    
    // Show random fun fact every 5 completed tasks
    if (completedChores > 0 && completedChores % 5 === 0) {
        showAchievement("Did You Know?", getRandomFunFact(), 'fun-fact');
    }
}

// Initialize the application
async function initializeApp() {
    try {
        console.log('Initializing application...');
        
        // Get DOM elements
        const checklistSelect = document.getElementById('checklistSelect');
        const staffSelect = document.getElementById('staffSelect');
        const choresContainer = document.getElementById('choresContainer');
        const signatureSection = document.getElementById('signatureSection');
        const clearSignatureBtn = document.getElementById('clearSignatureBtn');
        const submitChecklistBtn = document.getElementById('submitChecklistBtn');
        const resetChecklistBtn = document.getElementById('resetChecklistBtn');
        
        // Verify all required elements exist
        if (!checklistSelect) throw new Error('Checklist select element not found');
        if (!staffSelect) throw new Error('Staff select element not found');
        if (!choresContainer) throw new Error('Chores container element not found');
        if (!signatureSection) throw new Error('Signature section element not found');
        if (!clearSignatureBtn) throw new Error('Clear signature button not found');
        if (!submitChecklistBtn) throw new Error('Submit checklist button not found');
        if (!resetChecklistBtn) throw new Error('Reset checklist button not found');
        
        // Initialize signature pad
        const canvas = document.getElementById('signaturePad');
        if (!canvas) throw new Error('Signature pad canvas not found');
        signaturePad = new SignaturePad(canvas);
        
        await populateChecklistDropdown();
        console.log('Checklist dropdown populated');

        // Add event listeners
        checklistSelect.addEventListener('change', loadChecklist);
        staffSelect.addEventListener('change', updateUI);
        clearSignatureBtn.addEventListener('click', () => signaturePad.clear());
        submitChecklistBtn.addEventListener('click', submitChecklist);
        resetChecklistBtn.addEventListener('click', resetChecklist);
        console.log('Event listeners added');

        // Initial UI update
        updateUI();

    } catch (error) {
        console.error('Error during application initialization:', error);
        // Show error to user
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = `Failed to initialize application: ${error.message}. Please refresh the page to try again.`;
        document.querySelector('.container').prepend(errorDiv);
    }
}

// Start the application when the module loads
initializeApp();

function updateUI() {
    const checklistSelected = checklistSelect.value !== '';
    const staffSelected = staffSelect.value !== '';
    
    if (checklistSelected && staffSelected) {
        loadChecklist();
    } else {
        choresContainer.classList.add('d-none');
        signatureSection.classList.add('d-none');
    }
}

async function loadChecklist() {
    if (!checklistSelect.value || !staffSelect.value) return;

    try {
        const response = await fetch(window.location.origin + `/api/checklists/${checklistSelect.value}/chores`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to load checklist');
        }
        
        if (!Array.isArray(data)) {
            console.error('Invalid response format:', data);
            throw new Error('Invalid response format from server');
        }
        
        currentChores = data;
        renderChores();
        choresContainer.classList.remove('d-none');
        updateSignatureSection();
        resizeSignaturePad();
        
        // Update task counter
        const totalChores = currentChores.length;
        const completedChores = currentChores.filter(chore => chore.completed).length;
        updateProgressIndicator();
    } catch (error) {
        console.error('Error loading checklist:', error);
        alert('Failed to load checklist. Please try again.');
        choresContainer.classList.add('d-none');
        signatureSection.classList.add('d-none');
    }
}

function renderChores() {
    choresContainer.innerHTML = '';
    
    // Add progress display
    const progressDiv = document.createElement('div');
    progressDiv.id = 'progressDisplay';
    choresContainer.appendChild(progressDiv);
    
    // Group chores by section
    const sections = {};
    if (Array.isArray(currentChores)) {
        currentChores.forEach(chore => {
            if (!sections[chore.section]) {
                sections[chore.section] = [];
            }
            sections[chore.section].push(chore);
        });
    } else {
        console.error('currentChores is not an array:', currentChores);
        return;
    }
    
    // Render each section
    Object.entries(sections).forEach(([sectionName, sectionChores]) => {
        renderSection(sectionName, sectionChores);
    });
    
    updateProgressIndicator();
}

function renderSection(sectionName, sectionChores) {
    const sectionDiv = document.createElement('div');
    sectionDiv.className = 'section mb-3';
    
    // Section header with checkbox
    const sectionHeader = document.createElement('div');
    sectionHeader.className = 'section-header d-flex align-items-center p-2 bg-light';
    
    const sectionCheckbox = document.createElement('input');
    sectionCheckbox.type = 'checkbox';
    sectionCheckbox.className = 'form-check-input me-2';
    sectionCheckbox.checked = sectionChores.every(chore => chore.completed);
    sectionCheckbox.addEventListener('change', () => completeSection(sectionName));
    
    const sectionTitle = document.createElement('label');
    sectionTitle.className = 'form-check-label h5 mb-0 flex-grow-1';
    sectionTitle.textContent = sectionName;
    sectionTitle.style.cursor = 'pointer';
    sectionTitle.addEventListener('click', () => {
        sectionCheckbox.checked = !sectionCheckbox.checked;
        completeSection(sectionName);
    });
    
    sectionHeader.appendChild(sectionCheckbox);
    sectionHeader.appendChild(sectionTitle);
    sectionDiv.appendChild(sectionHeader);
    
    // Chores list
    const choresList = document.createElement('div');
    choresList.className = 'chores-list p-2';
    
    sectionChores.forEach(chore => {
        const choreDiv = document.createElement('div');
        choreDiv.className = 'chore-item d-flex align-items-center mb-2';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input me-2';
        checkbox.checked = chore.completed;
        checkbox.dataset.choreId = chore.id;
        checkbox.addEventListener('change', () => handleChoreCompletion(chore.id, checkbox));
        
        const label = document.createElement('label');
        label.className = 'form-check-label flex-grow-1';
        label.textContent = chore.description;
        label.style.cursor = 'pointer';
        label.addEventListener('click', () => {
            checkbox.checked = !checkbox.checked;
            handleChoreCompletion(chore.id, checkbox);
        });
        
        choreDiv.appendChild(checkbox);
        choreDiv.appendChild(label);
        choresList.appendChild(choreDiv);
    });
    
    sectionDiv.appendChild(choresList);
    choresContainer.appendChild(sectionDiv);
}

async function handleSectionCheckboxChange(sectionCheckbox, choreCheckboxes) {
    const isChecked = sectionCheckbox.checked;
    
    // Process each checkbox sequentially to avoid race conditions
    for (const checkbox of choreCheckboxes) {
        if (checkbox.checked !== isChecked) {
            checkbox.checked = isChecked;
            try {
                await handleChoreCompletion(checkbox.id.replace('chore-', ''), checkbox);
            } catch (error) {
                // If any checkbox update fails, revert the section checkbox
                sectionCheckbox.checked = !isChecked;
                sectionCheckbox.indeterminate = true;
                return;
            }
        }
    }
}

function renderChore(chore) {
    const choreDiv = document.createElement('div');
    choreDiv.className = `chore-item ${chore.completed ? 'completed' : ''}`;
    
    // Format completion time if exists
    let completionInfo = '';
    if (chore.completed && chore.completed_by && chore.completed_at) {
        const completedDate = new Date(chore.completed_at);
        const timeString = completedDate.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        });
        completionInfo = `
            <small class="text-success ms-2">
                ✓ Done by ${chore.completed_by} at ${timeString}
            </small>
        `;
    }

    // Add comment display if exists
    let commentDisplay = '';
    if (chore.comment) {
        commentDisplay = `
            <small class="text-muted ms-2">
                <i class="fas fa-comment"></i> ${chore.comment}
            </small>
        `;
    }

    choreDiv.innerHTML = `
        <div class="form-check">
            <input class="form-check-input chore-checkbox" type="checkbox" 
                   id="chore-${chore.id}"
                   ${chore.completed ? 'checked' : ''}>
        </div>
        <div class="flex-grow-1">
            <div class="d-flex align-items-center">
                <label class="form-check-label" for="chore-${chore.id}">
                    ${chore.description}
                </label>
                ${completionInfo}
                ${commentDisplay}
            </div>
            ${!chore.completed ? `
            <div class="chore-comment mt-1">
                <input type="text" class="form-control form-control-sm" 
                       placeholder="Add comment (optional)" 
                       value="${chore.comment || ''}"
                       data-chore-id="${chore.id}">
            </div>
            ` : ''}
        </div>
    `;

    // Add event listeners
    const checkbox = choreDiv.querySelector('.chore-checkbox');
    checkbox.addEventListener('change', () => handleChoreCompletion(chore.id, checkbox));

    // Add comment event listener only if the chore is not completed
    if (!chore.completed) {
        const commentInput = choreDiv.querySelector('.chore-comment input');
        if (commentInput) {
            commentInput.addEventListener('change', async (e) => {
                const comment = e.target.value.trim();
                try {
                    const response = await fetch('/api/chore_completion', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            chore_id: chore.id,
                            staff_name: staffSelect.value,
                            completed: checkbox.checked,
                            comment: comment
                        })
                    });

                    if (!response.ok) throw new Error('Failed to update comment');
                    
                    // Update the chore in currentChores
                    const chore = currentChores.find(c => c.id === chore.id);
                    if (chore) chore.comment = comment;
                } catch (error) {
                    console.error('Error updating comment:', error);
                    alert('Failed to update comment. Please try again.');
                }
            });
        }
    }

    return choreDiv;
}

function updateSectionCheckbox(sectionName) {
    const sectionCheckbox = document.querySelector(`#section-${sectionName.replace(/\s+/g, '-')}`);
    if (!sectionCheckbox) return;

    const choreCheckboxes = Array.from(document.querySelectorAll(`.chore-checkbox[data-section="${sectionName}"]`));
    const allChecked = choreCheckboxes.every(cb => cb.checked);
    const someChecked = choreCheckboxes.some(cb => cb.checked);

    sectionCheckbox.checked = allChecked;
    sectionCheckbox.indeterminate = someChecked && !allChecked;
}

async function processChoreUpdateQueue() {
    if (isProcessingQueue || choreUpdateQueue.length === 0) return;
    
    isProcessingQueue = true;
    
    while (choreUpdateQueue.length > 0) {
        const { choreId, checkbox } = choreUpdateQueue.shift();
        try {
            const response = await fetch('/api/chore_completion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    chore_id: choreId,
                    staff_name: staffSelect.value,
                    completed: checkbox.checked
                })
            });

            if (!response.ok) throw new Error('Failed to update chore status');
            
            const chore = currentChores.find(c => c.id === choreId);
            chore.completed = checkbox.checked;
            updateSignatureSection();
            
            // Add a small delay between requests
            await new Promise(resolve => setTimeout(resolve, 300));
        } catch (error) {
            console.error('Error updating chore:', error);
            checkbox.checked = !checkbox.checked; // Revert the checkbox
            alert('Failed to update chore. Please try again.');
        }
    }
    
    isProcessingQueue = false;
}

async function handleChoreCompletion(choreId, checkbox) {
    // Add to queue instead of sending request immediately
    choreUpdateQueue.push({ choreId, checkbox });
    processChoreUpdateQueue();
    
    // Update progress immediately for better user feedback
    updateProgressIndicator();
    
    // Add completion animation
    if (checkbox.checked) {
        const checkmark = document.createElement('div');
        checkmark.className = 'floating-checkmark';
        checkmark.textContent = '✓';
        checkbox.parentElement.appendChild(checkmark);
        
        setTimeout(() => {
            if (checkmark.isConnected) {
                checkmark.remove();
            }
        }, 1000);
    }
}

async function handleChoreComment(choreId, comment) {
    try {
        const response = await fetch('/api/chore_comment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chore_id: choreId,
                comment: comment
            })
        });

        if (!response.ok) throw new Error('Failed to save comment');
        
        const chore = currentChores.find(c => c.id === choreId);
        chore.comment = comment;
    } catch (error) {
        console.error('Error saving comment:', error);
        alert('Failed to save comment. Please try again.');
    }
}

function updateSignatureSection() {
    if (!Array.isArray(currentChores)) {
        console.error('currentChores is not an array:', currentChores);
        return;
    }
    
    const allCompleted = currentChores.every(chore => chore.completed);
    signatureSection.classList.toggle('d-none', !allCompleted);
    
    if (allCompleted) {
        signaturePad.clear();
    }
}

async function submitChecklist() {
    if (!signaturePad || signaturePad.isEmpty()) {
        alert('Please provide your signature before submitting.');
        return;
    }

    const staffName = staffSelect.value;
    const checklistId = checklistSelect.value;
    const signatureData = signaturePad.toDataURL();

    try {
        const response = await fetch('/api/submit_checklist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                checklist_id: checklistId,
                staff_name: staffName,
                signature_data: signatureData
            })
        });

        if (!response.ok) throw new Error('Failed to submit checklist');
        
        alert('Checklist submitted successfully!');
        location.reload();
    } catch (error) {
        console.error('Error submitting checklist:', error);
        alert('Failed to submit checklist. Please try again.');
    }
}

function selectStaff(staffName) {
    selectedStaff = staffName;
    document.querySelectorAll('.list-group-item').forEach(item => {
        item.classList.remove('active');
    });
    document.getElementById(`staff-${staffName}`).classList.add('active');
}

function updateProgress() {
    const progress = (completedCount / totalChores) * 100;
    document.querySelector('.progress-fill').style.width = `${progress}%`;
    document.querySelector('.progress-text').textContent = `${Math.round(progress)}%`;

    // Update emoji based on progress
    const currentEncouragement = encouragements.reduce((prev, curr) => {
        return (progress >= curr.threshold * 100) ? curr : prev;
    });

    const emojiElement = document.querySelector('.progress-emoji');
    if (emojiElement.textContent !== currentEncouragement.emoji) {
        emojiElement.textContent = currentEncouragement.emoji;
        emojiElement.classList.add('bounce');
        setTimeout(() => emojiElement.classList.remove('bounce'), 1000);
    }

    // Show milestone achievements
    if (progress % 25 === 0 && progress > 0 && !completedSections.has(progress)) {
        completedSections.add(progress);
        showAchievement(currentEncouragement.emoji, "Milestone Reached!", currentEncouragement.message, "milestone");
    }

    // Show fun facts every 5 completed tasks
    if (completedCount % 5 === 0 && completedCount > 0 && !completedChores.has(completedCount)) {
        completedChores.add(completedCount);
        const randomFact = funFacts[Math.floor(Math.random() * funFacts.length)];
        showAchievement("💡", "Fun Fact!", randomFact, "fun-fact");
    }
}

async function toggleChore(choreId, checkbox) {
    try {
        const response = await fetch(window.location.origin + `/api/chores/${choreId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                completed: checkbox.checked,
                staff_name: staffSelect.value
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update chore');
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error toggling chore:', error);
        checkbox.checked = !checkbox.checked; // Revert the checkbox
        throw error;
    }
}

async function completeSection(sectionName) {
    try {
        // Get the section ID from the current chores
        const sectionChores = currentChores.filter(chore => chore.section === sectionName);
        if (sectionChores.length === 0) {
            console.error('No chores found for section:', sectionName);
            return;
        }
        
        // Get the section ID from the first chore
        const sectionId = sectionChores[0].section_id;
        if (!sectionId) {
            console.error('No section ID found for section:', sectionName);
            return;
        }
        
        // Send request to complete the section
        const response = await fetch(window.location.origin + `/api/sections/${sectionId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                staff_name: staffSelect.value
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to complete section');
        }
        
        // Update all checkboxes in the section
        const checkboxes = document.querySelectorAll(`input[data-chore-id]`);
        checkboxes.forEach(checkbox => {
            const choreId = parseInt(checkbox.dataset.choreId);
            const chore = currentChores.find(c => c.id === choreId);
            if (chore && chore.section === sectionName) {
                checkbox.checked = true;
                const choreObj = currentChores.find(c => c.id === choreId);
                if (choreObj) {
                    choreObj.completed = true;
                }
            }
        });
        
        updateProgressIndicator();
    } catch (error) {
        console.error('Error completing section:', error);
        alert('Failed to complete section. Please try again.');
    }
}

// Populate checklist dropdown
async function populateChecklistDropdown() {
    try {
        console.log('Fetching checklists...');
        const response = await fetch(window.location.origin + '/api/checklists');
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received checklists:', data);
        
        if (!Array.isArray(data)) {
            throw new Error('Expected array of checklists but got: ' + typeof data);
        }
        
        checklistSelect.innerHTML = '<option value="">Choose a checklist...</option>';
        data.forEach(c => {
            if (!c.name) {
                console.warn('Checklist missing name:', c);
                return;
            }
            const option = document.createElement('option');
            option.value = c.name;
            option.textContent = c.description || c.name;
            checklistSelect.appendChild(option);
            console.log('Added checklist option:', c.name);
        });
    } catch (error) {
        console.error('Failed to load checklists:', error);
        // Show error to user
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = 'Failed to load checklists. Please refresh the page to try again.';
        checklistSelect.parentNode.insertBefore(errorDiv, checklistSelect);
    }
}

async function resetChecklist() {
    if (!confirm('Are you sure you want to reset this checklist? This will clear all completion statuses.')) {
        return;
    }

    try {
        const response = await fetch(window.location.origin + `/api/checklists/${currentChecklist}/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                staff_name: staffSelect.value
            })
        });

        if (!response.ok) {
            throw new Error('Failed to reset checklist');
        }

        // Clear all checkboxes
        document.querySelectorAll('.chore-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Remove completed class from all chore items
        document.querySelectorAll('.chore-item').forEach(item => {
            item.classList.remove('completed');
        });

        // Remove completed class from all section headers
        document.querySelectorAll('.section-header').forEach(header => {
            header.classList.remove('completed');
        });

        // Reset the progress indicator
        updateProgressIndicator(0, 0);

        // Reload the checklist to ensure everything is in sync
        await loadChecklist(currentChecklist);

        alert('Checklist has been reset successfully!');
    } catch (error) {
        console.error('Error resetting checklist:', error);
        alert('Failed to reset checklist. Please try again.');
    }
} 