// Global variables
let currentChores = [];
let choreUpdateQueue = [];
let isProcessingQueue = false;
let selectedStaff = null;
let completedChores = new Set();
let completedSections = new Set();
let totalChores = 0;
let completedCount = 0;
let checklistSelect;
let staffSelect;
let choreContainer;
let successSection;
let submitChecklistBtn;
let signaturePad;
let clearSignatureBtn;
let resetChecklistBtn;

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
    if (!Array.isArray(currentChores) || currentChores.length === 0) return;
    
    const total = currentChores.length;
    const completed = currentChores.filter(chore => chore.completed).length;
    const progress = (completed / total) * 100;
    
    // Update progress display
    const progressDiv = document.getElementById('progressDisplay');
    if (progressDiv) {
        progressDiv.innerHTML = `
            <div class="progress-display">
                <div class="progress-emoji">🎯</div>
                <div class="flex-grow-1">
                    <div class="progress">
                        <div class="progress-bar bg-success" 
                             role="progressbar" 
                             style="width: ${progress}%" 
                             aria-valuenow="${progress}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                        </div>
                    </div>
                    <small class="text-muted">${completed} of ${total} tasks completed (${Math.round(progress)}%)</small>
                </div>
            </div>
        `;
    }
    
    // Check if all tasks are completed
    if (completed === total) {
        successSection.classList.remove('d-none');
        showConfetti();
    } else {
        successSection.classList.add('d-none');
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', async function() {
    try {
        console.log('Starting application initialization...');
        
        // Get DOM elements
        console.log('Getting DOM elements...');
        checklistSelect = document.getElementById('checklistSelect');
        staffSelect = document.getElementById('staffSelect');
        choreContainer = document.getElementById('choreContainer');
        successSection = document.getElementById('successSection');
        submitChecklistBtn = document.getElementById('submitChecklistBtn');
        clearSignatureBtn = document.getElementById('clearSignatureBtn');
        resetChecklistBtn = document.getElementById('resetChecklist');
        
        // Initialize signature pad
        const canvas = document.getElementById('signaturePad');
        if (canvas) {
            signaturePad = new SignaturePad(canvas, {
                minWidth: 2,
                maxWidth: 4,
                penColor: "rgb(0, 0, 0)"
            });
            resizeSignaturePad();
            window.addEventListener('resize', resizeSignaturePad);
        }
        
        // Verify all required elements exist
        if (!checklistSelect) throw new Error('Checklist select element not found');
        if (!staffSelect) throw new Error('Staff select element not found');
        if (!choreContainer) throw new Error('Chores container element not found');
        if (!successSection) throw new Error('Success section element not found');
        if (!submitChecklistBtn) throw new Error('Submit checklist button not found');
        
        console.log('Populating checklist dropdown...');
        await populateChecklistDropdown();
        console.log('Checklist dropdown populated');

        // Add event listeners
        console.log('Adding event listeners...');
        checklistSelect.addEventListener('change', () => {
            if (checklistSelect.value) {
                loadChecklist(checklistSelect.value);
            }
            resetChecklistBtn.style.display = checklistSelect.value && staffSelect.value ? 'inline-flex' : 'none';
        });
        
        staffSelect.addEventListener('change', () => {
            updateUI();
            resetChecklistBtn.style.display = checklistSelect.value && staffSelect.value ? 'inline-flex' : 'none';
        });
        
        if (clearSignatureBtn) {
            clearSignatureBtn.addEventListener('click', () => signaturePad.clear());
        }
        
        if (resetChecklistBtn) {
            resetChecklistBtn.addEventListener('click', async () => {
                const checklistName = checklistSelect.value;
                if (!checklistName) return;
                
                if (!confirm(`Are you sure you want to reset the ${checklistName} checklist? This will remove all completed tasks and signatures.`)) {
                    return;
                }
                
                try {
                    const response = await fetch(window.location.origin + `/api/reset_checklist/${checklistName}`, {
                        method: 'POST'
                    });
                    
                    if (!response.ok) throw new Error('Failed to reset checklist');
                    
                    // Reload the page to show fresh checklist
                    location.reload();
                } catch (error) {
                    console.error('Error resetting checklist:', error);
                    alert('Failed to reset checklist. Please try again.');
                }
            });
        }
        
        console.log('Event listeners added');

        // Initial UI update
        console.log('Performing initial UI update...');
        updateUI();
        console.log('Initial UI update complete');

        // Load initial checklist if one is selected
        if (checklistSelect.value) {
            loadChecklist(checklistSelect.value);
        }

        console.log('Application initialization complete');
    } catch (error) {
        console.error('Error during application initialization:', error);
        // Show error to user
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = `Failed to initialize application: ${error.message}. Please refresh the page to try again.`;
        document.querySelector('.container').prepend(errorDiv);
    }
});

function updateUI() {
    const checklistSelected = checklistSelect.value !== '';
    const staffSelected = staffSelect.value !== '';
    
    // Remove any existing alert
    const existingAlert = document.querySelector('.alert-info');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    if (!staffSelected && !checklistSelected) {
        // Show message to select staff member only if neither staff nor checklist is selected
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-info mt-3';
        alertDiv.textContent = 'Please select your name from the staff list to view and complete checklists.';
        checklistSelect.parentNode.insertBefore(alertDiv, checklistSelect.nextSibling);
    }
    
    if (checklistSelected && staffSelected) {
        loadChecklist();
    } else {
        choreContainer.classList.add('d-none');
        successSection.classList.add('d-none');
    }
}

async function loadChecklist(checklistId) {
    if (!checklistId) return;
    
    try {
        console.log('Loading checklist:', checklistId);
        const response = await fetch(window.location.origin + `/api/checklists/${checklistId}/chores`);
        if (!response.ok) {
            console.error('Failed to load checklist:', response.status, response.statusText);
            throw new Error('Failed to load checklist');
        }
        
        const data = await response.json();
        console.log('Received checklist data:', data);
        currentChores = data;
        
        // Clear existing chores
        choreContainer.innerHTML = '';
        
        // Add progress display
        const progressDiv = document.createElement('div');
        progressDiv.id = 'progressDisplay';
        progressDiv.className = 'progress-display';
        choreContainer.appendChild(progressDiv);
        
        // Group chores by section
        const sections = {};
        data.forEach(chore => {
            if (!sections[chore.section]) sections[chore.section] = [];
            sections[chore.section].push(chore);
        });
        
        console.log('Grouped sections:', sections);
        
        // Render each section
        Object.entries(sections).forEach(([sectionName, sectionChores]) => {
            renderSection(sectionName, sectionChores);
        });
        
        // Show the container
        choreContainer.classList.remove('d-none');
        
        // Update progress
        updateProgressIndicator();
    } catch (error) {
        console.error('Error loading checklist:', error);
        alert('Failed to load checklist. Please try again.');
    }
}

function renderChores(chores) {
    choreContainer.innerHTML = '';
    
    // Add progress display
    const progressDiv = document.createElement('div');
    progressDiv.id = 'progressDisplay';
    choreContainer.appendChild(progressDiv);
    
    // Group chores by section
    const sections = {};
    if (Array.isArray(chores)) {
        chores.forEach(chore => {
            if (!sections[chore.section]) {
                sections[chore.section] = [];
            }
            sections[chore.section].push(chore);
        });
    } else {
        console.error('chores is not an array:', chores);
        return;
    }
    
    // Render each section
    Object.entries(sections).forEach(([sectionName, sectionChores]) => {
        const sectionElement = renderSection(sectionName, sectionChores);
        choreContainer.appendChild(sectionElement);
    });
    
    updateProgressIndicator();
}

function renderSection(sectionName, sectionChores) {
    console.log('Rendering section:', sectionName, 'with chores:', sectionChores);
    
    const sectionDiv = document.createElement('div');
    sectionDiv.className = 'section mb-4';
    sectionDiv.dataset.sectionName = sectionName;
    
    // Section header
    const sectionHeader = document.createElement('div');
    sectionHeader.className = 'card-header bg-light d-flex align-items-center gap-2';
    
    const sectionCheckbox = document.createElement('input');
    sectionCheckbox.type = 'checkbox';
    sectionCheckbox.className = 'form-check-input';
    sectionCheckbox.checked = sectionChores.every(chore => chore.completed);
    
    const sectionTitle = document.createElement('h5');
    sectionTitle.className = 'mb-0 flex-grow-1';
    sectionTitle.textContent = sectionName;
    
    sectionHeader.appendChild(sectionCheckbox);
    sectionHeader.appendChild(sectionTitle);
    sectionDiv.appendChild(sectionHeader);
    
    // Chores container
    const choresContainer = document.createElement('div');
    choresContainer.className = 'card-body';
    
    // Sort chores by order
    sectionChores.sort((a, b) => a.order - b.order);
    
    // Add each chore
    sectionChores.forEach(chore => {
        const choreDiv = document.createElement('div');
        choreDiv.className = 'chore-item mb-2';
        if (chore.completed) {
            choreDiv.classList.add('completed');
        }
        
        // Checkbox and label container
        const checkboxContainer = document.createElement('div');
        checkboxContainer.className = 'd-flex align-items-start gap-2';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input mt-1';
        checkbox.id = `chore-${chore.id}`;
        checkbox.checked = chore.completed;
        checkbox.dataset.choreId = chore.id;
        
        const label = document.createElement('label');
        label.className = 'form-check-label flex-grow-1';
        label.htmlFor = `chore-${chore.id}`;
        label.textContent = chore.description;
        
        checkboxContainer.appendChild(checkbox);
        checkboxContainer.appendChild(label);
        choreDiv.appendChild(checkboxContainer);
        
        // Add completion info if completed
        if (chore.completed && chore.completed_by) {
            const completionInfo = document.createElement('div');
            completionInfo.className = 'completion-info text-muted ms-4';
            completionInfo.innerHTML = `
                <small>Completed by ${chore.completed_by}</small>
                ${chore.comment ? `<br><small>Comment: ${chore.comment}</small>` : ''}
            `;
            choreDiv.appendChild(completionInfo);
        }
        // Add comment input if not completed
        else if (!chore.completed) {
            const commentDiv = document.createElement('div');
            commentDiv.className = 'chore-comment ms-4 mt-1';
            
            const commentInput = document.createElement('input');
            commentInput.type = 'text';
            commentInput.className = 'form-control form-control-sm';
            commentInput.placeholder = 'Add a comment...';
            commentInput.value = chore.comment || '';
            
            commentDiv.appendChild(commentInput);
            choreDiv.appendChild(commentDiv);
        }
        
        choresContainer.appendChild(choreDiv);
        
        // Add checkbox event listener
        checkbox.addEventListener('change', () => handleChoreCompletion(chore.id, checkbox, sectionName));
    });
    
    sectionDiv.appendChild(choresContainer);
    
    // Add section checkbox event listener
    const choreCheckboxes = choresContainer.querySelectorAll('input[type="checkbox"]');
    sectionCheckbox.addEventListener('change', () => handleSectionCheckboxChange(sectionCheckbox, choreCheckboxes));
    
    // Add to the main container
    choreContainer.appendChild(sectionDiv);
}

async function handleSectionCheckboxChange(sectionCheckbox, choreCheckboxes) {
    const isChecked = sectionCheckbox.checked;
    const sectionName = sectionCheckbox.closest('.section').dataset.sectionName;
    
    try {
        // Process each checkbox sequentially to avoid race conditions
        for (const checkbox of choreCheckboxes) {
            if (checkbox.checked !== isChecked) {
                checkbox.checked = isChecked;
                await handleChoreCompletion(parseInt(checkbox.id.replace('chore-', '')), checkbox);
            }
        }
    } catch (error) {
        // If any checkbox update fails, revert the section checkbox
        sectionCheckbox.checked = !isChecked;
        sectionCheckbox.indeterminate = true;
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

async function handleChoreCompletion(choreId, checkbox, sectionName) {
    try {
        const response = await fetch(window.location.origin + `/api/chores/${choreId}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                staff_name: staffSelect.value,
                completed: checkbox.checked
            })
        });

        if (!response.ok) throw new Error('Failed to update chore status');
        
        // Update the chore in currentChores
        const chore = currentChores.find(c => c.id === choreId);
        if (chore) {
            chore.completed = checkbox.checked;
            chore.completed_by = staffSelect.value;
            chore.completed_at = new Date().toISOString();
            
            // Check if all chores in the section are completed
            const sectionChores = currentChores.filter(c => c.section === sectionName);
            const allSectionChoresCompleted = sectionChores.every(c => c.completed);
            
            // Update section checkbox
            const sectionCheckboxes = document.querySelectorAll('.section-header input[type="checkbox"]');
            sectionCheckboxes.forEach(cb => {
                if (cb.closest('.section').querySelector('.section-header label').textContent === sectionName) {
                    cb.checked = allSectionChoresCompleted;
                }
            });
            
            // Check if all chores are completed
            const allChoresCompleted = currentChores.every(c => c.completed);
            if (allChoresCompleted) {
                successSection.classList.remove('d-none');
                showConfetti();
            } else {
                successSection.classList.add('d-none');
            }
            
            // Update progress
            updateProgressIndicator();
        }
        
        // Add completion animation
        if (checkbox.checked) {
            const checkmark = document.createElement('div');
            checkmark.className = 'floating-checkmark';
            checkmark.textContent = '✓';
            checkbox.parentElement.appendChild(checkmark);
            
            setTimeout(() => checkmark.remove(), 1000);
        }
    } catch (error) {
        console.error('Error updating chore:', error);
        checkbox.checked = !checkbox.checked; // Revert the checkbox
        alert('Failed to update chore. Please try again.');
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
    const allChoresCompleted = currentChores.every(chore => chore.completed);
    if (allChoresCompleted) {
        successSection.classList.remove('d-none');
        // Show confetti animation
        showConfetti();
    } else {
        successSection.classList.add('d-none');
    }
}

function showConfetti() {
    // Add confetti effect (you can add a confetti library later if desired)
    const confetti = document.createElement('div');
    confetti.className = 'confetti-container';
    document.body.appendChild(confetti);
    
    // Remove confetti after animation
    setTimeout(() => {
        if (confetti.parentNode) {
            confetti.parentNode.removeChild(confetti);
        }
    }, 3000);
}

async function submitChecklist() {
    const staffName = staffSelect.value;
    const checklistId = checklistSelect.value;

    // Check if all chores are completed
    const allCompleted = currentChores.every(chore => chore.completed);
    if (!allCompleted) {
        alert('Please complete all tasks before submitting the checklist.');
        return;
    }

    try {
        const response = await fetch('/api/submit_checklist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                checklist_id: checklistId,
                staff_name: staffName
            })
        });

        if (!response.ok) throw new Error('Failed to submit checklist');
        
        // Get unique contributors
        const contributors = [...new Set(currentChores
            .filter(chore => chore.completed_by)
            .map(chore => chore.completed_by)
        )];
        
        // Format contributors list
        let contributorsText = '';
        if (contributors.length === 1) {
            contributorsText = contributors[0];
        } else if (contributors.length === 2) {
            contributorsText = `${contributors[0]} and ${contributors[1]}`;
        } else if (contributors.length > 2) {
            const lastContributor = contributors.pop();
            contributorsText = `${contributors.join(', ')}, and ${lastContributor}`;
        }
        
        // Show success message with confetti
        showConfetti();
        
        // Create a success message that will stay visible
        const successMessage = document.createElement('div');
        successMessage.className = 'alert alert-success text-center mt-4';
        successMessage.innerHTML = `
            <h4 class="alert-heading">🎉 Amazing job! 🎉</h4>
            <p class="mb-0">The ${checklistSelect.options[checklistSelect.selectedIndex].text} has been completed by ${contributorsText}!</p>
        `;
        
        // Replace the success section content and remove submit button
        successSection.innerHTML = '';
        successSection.appendChild(successMessage);
        
        // Disable all checkboxes
        document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.disabled = true;
        });
        
        // Disable the checklist select and staff select
        checklistSelect.disabled = true;
        staffSelect.disabled = true;
        
        // Reload the page after 5 seconds
        setTimeout(() => {
            location.reload();
        }, 5000);
        
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
        // Populate staff select first
        const staffNames = [
            "Nora", "Josh", "Vaile", "Melissa", "Paddy",
            "Pero", "Guy", "Dean", "Bethany", "Henry"
        ];
        
        // Clear existing options except the first one
        while (staffSelect.options.length > 1) {
            staffSelect.remove(1);
        }
        
        // Add new options
        staffNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            staffSelect.appendChild(option);
        });

        // Then populate checklists
        const response = await fetch(window.location.origin + '/api/checklists');
        const checklists = await response.json();
        
        // Clear existing options except the first one
        while (checklistSelect.options.length > 1) {
            checklistSelect.remove(1);
        }
        
        // Add new options
        checklists.forEach(checklist => {
            const option = document.createElement('option');
            option.value = checklist.name;
            option.textContent = checklist.description || checklist.name;
            checklistSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading checklists:', error);
        alert('Failed to load checklists. Please refresh the page.');
    }
}

// Resize signature pad when window resizes
function resizeSignaturePad() {
    if (!signaturePad) return;
    
    const canvas = signaturePad.canvas;
    const ratio = Math.max(window.devicePixelRatio || 1, 1);
    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;
    
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    canvas.getContext("2d").scale(ratio, ratio);
    signaturePad.clear(); // otherwise isEmpty() might return incorrect value
}

// Add window resize listener
window.addEventListener('resize', resizeSignaturePad);

// Add this CSS to your style.css file
const style = document.createElement('style');
style.textContent = `
    .confetti-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
    }
`;
document.head.appendChild(style); 