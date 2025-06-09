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
let lastUpdateTime = 0;
const UPDATE_THROTTLE = 300; // Minimum time between updates in ms

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

function updateProgress() {
    const totalTasks = document.querySelectorAll('.chore-item').length;
    const completedTasks = document.querySelectorAll('.chore-item input[type="checkbox"]:checked').length;
    const percentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

    document.querySelector('.progress-bar-inner').style.width = `${percentage}%`;
    document.getElementById('progressText').textContent = `${completedTasks} of ${totalTasks} tasks completed`;
    document.getElementById('progressPercentage').textContent = `${percentage}%`;

    // Show success section if all tasks are completed
    if (completedTasks === totalTasks && totalTasks > 0) {
        successSection.classList.remove('d-none');
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
        resetChecklistBtn = document.getElementById('resetChecklist');
        
        // Verify all required elements exist
        if (!checklistSelect) throw new Error('Checklist select element not found');
        if (!staffSelect) throw new Error('Staff select element not found');
        if (!choreContainer) throw new Error('Chores container element not found');
        if (!successSection) throw new Error('Success section element not found');
        
        console.log('Populating staff dropdown...');
        await populateStaffDropdown();
        console.log('Staff dropdown populated');
        
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
    
    // Only reload checklist if it's not already loaded
    if (checklistSelected && staffSelected && choreContainer.children.length === 0) {
        loadChecklist(checklistSelect.value);
    } else if (!checklistSelected || !staffSelected) {
        choreContainer.classList.add('d-none');
        successSection.classList.add('d-none');
    } else {
        choreContainer.classList.remove('d-none');
    }
}

async function loadChecklist(checklistId) {
    if (!checklistId) return;
    
    try {
        console.log('Loading checklist:', checklistId);
        console.log('Fetching from:', window.location.origin + `/api/checklists/${checklistId}/chores`);
        
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
        if (Array.isArray(data)) {
            data.forEach(chore => {
                if (!sections[chore.section]) sections[chore.section] = [];
                sections[chore.section].push(chore);
            });
            
            console.log('Grouped sections:', sections);
            
            // Create a container for sections
            const sectionsContainer = document.createElement('div');
            sectionsContainer.className = 'sections-container';
            
            // Render each section
            Object.entries(sections).forEach(([sectionName, sectionChores]) => {
                console.log('Rendering section:', sectionName, 'with chores:', sectionChores);
                const sectionElement = renderSection(sectionName, sectionChores);
                sectionsContainer.appendChild(sectionElement);
            });
            
            // Add sections container to main container
            choreContainer.appendChild(sectionsContainer);
            
            // Show the container
            choreContainer.classList.remove('d-none');
            
            // Update progress
            updateProgress();
        } else {
            console.error('Received data is not an array:', data);
        }
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
    
    updateProgress();
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Create throttled version of updateProgressIndicator
const throttledUpdateProgress = throttle(updateProgress, 100);

async function handleChoreCompletion(choreId, checkbox, sectionName) {
    const isChecked = checkbox.checked;
    const staffName = staffSelect.value;
    
    if (!staffName) {
        alert('Please select your name first!');
        checkbox.checked = !isChecked;
        return;
    }
    
    try {
        const response = await fetch('/api/chore_completion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                chore_id: choreId,
                staff_name: staffName,
                completed: isChecked
            })
        });
        
        if (!response.ok) throw new Error('Failed to update chore status');
        
        // Update the chore's completed status in our local state
        const chore = currentChores.find(c => c.id === choreId);
        if (chore) {
            chore.completed = isChecked;
            chore.completed_by = isChecked ? staffName : null;
        }
        
        // Update progress
        updateProgress();
        
        // Update section checkbox
        updateSectionCheckbox(sectionName);
        
    } catch (error) {
        console.error('Error updating chore completion:', error);
        checkbox.checked = !isChecked;
        alert('Failed to update task status. Please try again.');
    }
}

// Update the processChoreUpdateQueue function
async function processChoreUpdateQueue() {
    if (isProcessingQueue || choreUpdateQueue.length === 0) return;
    
    isProcessingQueue = true;
    const batchSize = 5; // Process 5 updates at a time
    
    while (choreUpdateQueue.length > 0) {
        const batch = choreUpdateQueue.splice(0, batchSize);
        const promises = batch.map(({ choreId, checkbox, comment }) => 
            fetch(window.location.origin + `/api/chores/${choreId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    staff_name: staffSelect.value,
                    completed: checkbox.checked,
                    comment: comment
                })
            })
        );

        try {
            await Promise.all(promises);
        } catch (error) {
            console.error('Error processing chore updates:', error);
            // Continue processing the queue despite errors
        }

        // Add a small delay between batches
        if (choreUpdateQueue.length > 0) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
    
    isProcessingQueue = false;
    throttledUpdateProgress();
}

// Optimized render functions
function renderSection(sectionName, sectionChores) {
    const sectionDiv = document.createElement('div');
    sectionDiv.className = 'section mb-4';
    sectionDiv.dataset.sectionName = sectionName;
    sectionDiv.dataset.sectionId = sectionChores[0]?.section_id;

    const sectionHeader = document.createElement('div');
    sectionHeader.className = 'card-header bg-light d-flex align-items-center gap-2';
    sectionHeader.innerHTML = `
        <input type="checkbox" class="form-check-input" ${sectionChores.every(chore => chore.completed) ? 'checked' : ''}>
        <h5 class="mb-0 flex-grow-1">${sectionName}</h5>
    `;

    const choresContainer = document.createElement('div');
    choresContainer.className = 'card-body';

    // Sort chores by order
    sectionChores.sort((a, b) => a.order - b.order);

    // Create chores HTML in a single operation
    const choresHTML = sectionChores.map(chore => `
        <div class="chore-item mb-2 ${chore.completed ? 'completed' : ''}">
            <div class="d-flex align-items-start gap-2">
                <input type="checkbox" class="form-check-input mt-1" id="chore-${chore.id}"
                       ${chore.completed ? 'checked' : ''} data-chore-id="${chore.id}">
                <label class="form-check-label flex-grow-1" for="chore-${chore.id}">
                    ${chore.description}
                </label>
            </div>
            ${chore.completed && chore.completed_by ? `
                <div class="completion-info text-muted ms-4">
                    <small>Completed by ${chore.completed_by}</small>
                    ${chore.comment ? `<br><small>Comment: ${chore.comment}</small>` : ''}
                </div>
            ` : !chore.completed ? `
                <div class="chore-comment ms-4 mt-1">
                    <input type="text" class="form-control form-control-sm" 
                           placeholder="Add a comment..." value="${chore.comment || ''}">
                </div>
            ` : ''}
        </div>
    `).join('');

    choresContainer.innerHTML = choresHTML;

    // Add event listeners
    const checkboxes = choresContainer.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => 
            handleChoreCompletion(parseInt(checkbox.dataset.choreId), checkbox, sectionName)
        );
    });

    sectionDiv.appendChild(sectionHeader);
    sectionDiv.appendChild(choresContainer);

    // Add section checkbox event listener
    const sectionCheckbox = sectionHeader.querySelector('input[type="checkbox"]');
    sectionCheckbox.addEventListener('change', () => 
        handleSectionCheckboxChange(sectionCheckbox, checkboxes)
    );

    return sectionDiv;
}

async function handleSectionCheckboxChange(sectionCheckbox, choreCheckboxes) {
    const isChecked = sectionCheckbox.checked;
    const sectionName = sectionCheckbox.closest('.section').dataset.sectionName;
    const staffName = staffSelect.value;
    
    if (!staffName) {
        alert('Please select a staff member first.');
        sectionCheckbox.checked = !isChecked;
        return;
    }

    try {
        // Prepare batch of chores to update
        const choresToUpdate = Array.from(choreCheckboxes)
            .filter(checkbox => checkbox.checked !== isChecked)
            .map(checkbox => {
                const choreDiv = checkbox.closest('.chore-item');
                const commentInput = choreDiv ? choreDiv.querySelector('input[type="text"]') : null;
                const comment = commentInput ? commentInput.value.trim() : '';
                return {
                    choreId: parseInt(checkbox.dataset.choreId),
                    checkbox: checkbox,
                    comment: comment
                };
            });

        if (choresToUpdate.length === 0) return;

        // Collect all comments
        const comments = choresToUpdate
            .filter(item => item.comment)
            .map(item => item.comment);
        const combinedComment = comments.join(' | ');

        // Optimistically update UI
        choresToUpdate.forEach(({ checkbox, comment }) => {
            checkbox.checked = isChecked;
            const choreDiv = checkbox.closest('.chore-item');
            if (choreDiv) {
                if (isChecked) {
                    choreDiv.classList.add('completed');
                    // Add completion info
                    const completionInfo = document.createElement('div');
                    completionInfo.className = 'completion-info text-muted ms-4';
                    completionInfo.innerHTML = `
                        <small>Completed by ${staffName}</small>
                        ${comment ? `<br><small>Comment: ${comment}</small>` : ''}
                    `;
                    choreDiv.appendChild(completionInfo);
                } else {
                    choreDiv.classList.remove('completed');
                    // Remove completion info
                    const completionInfo = choreDiv.querySelector('.completion-info');
                    if (completionInfo) completionInfo.remove();
                }
            }
        });

        // Send single request for the section
        const sectionId = parseInt(sectionCheckbox.closest('.section').dataset.sectionId);
        const response = await fetch(window.location.origin + `/api/sections/${sectionId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                staff_name: staffName,
                completed: isChecked,
                comment: combinedComment || undefined
            })
        });

        if (!response.ok) {
            throw new Error('Failed to update section');
        }

        // Update progress
        updateProgress();

        // Add completion animation for successful update
        if (isChecked) {
            choresToUpdate.forEach(({ checkbox }) => {
                const checkmark = document.createElement('div');
                checkmark.className = 'floating-checkmark';
                checkmark.textContent = '✓';
                checkbox.parentElement.appendChild(checkmark);
                setTimeout(() => checkmark.remove(), 1000);
            });
        }

    } catch (error) {
        console.error('Error updating section:', error);
        // Revert all changes on error
        sectionCheckbox.checked = !isChecked;
        choreCheckboxes.forEach(checkbox => {
            checkbox.checked = !isChecked;
            const choreDiv = checkbox.closest('.chore-item');
            if (choreDiv) {
                if (!isChecked) {
                    choreDiv.classList.add('completed');
                } else {
                    choreDiv.classList.remove('completed');
                }
            }
        });
        alert('Failed to update section. Please try again.');
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
    try {
        const checklistId = checklistSelect.value;
        const staffName = staffSelect.value;
        
        if (!checklistId || !staffName) {
            alert('Please select both a checklist and your name before submitting.');
            return;
        }

        const response = await fetch('/api/submit_checklist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                checklist_id: checklistId,
                staff_name: staffName
            })
        });

        if (!response.ok) {
            throw new Error('Failed to submit checklist');
        }

        // Show success message
        alert('Checklist submitted successfully!');
        
        // Reload the page to show fresh checklist
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

function updateProgressIndicator() {
    // This function is now deprecated and should not be used
    return;
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
        
        updateProgress();
    } catch (error) {
        console.error('Error completing section:', error);
        alert('Failed to complete section. Please try again.');
    }
}

// Populate checklist dropdown
async function populateChecklistDropdown() {
    try {
        console.log('Starting to populate dropdowns...');
        
        // Populate staff select first
        const staffNames = [
            "Nora", "Josh", "Vaile", "Melissa", "Paddy",
            "Pero", "Guy", "Dean", "Bethany", "Henry"
        ];
        
        console.log('Staff names to add:', staffNames);
        
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

        console.log('Staff dropdown populated');
        console.log('Fetching checklists from:', window.location.origin + '/api/checklists');

        // Then populate checklists
        const response = await fetch(window.location.origin + '/api/checklists');
        const checklists = await response.json();
        
        console.log('Received checklists:', checklists);
        
        // Clear existing options except the first one
        while (checklistSelect.options.length > 1) {
            checklistSelect.remove(1);
        }
        
        // Add new options
        checklists.forEach(checklist => {
            console.log('Adding checklist:', checklist);
            const option = document.createElement('option');
            option.value = checklist.name;
            option.textContent = checklist.description || checklist.name;
            checklistSelect.appendChild(option);
        });
        
        console.log('Checklist dropdown populated');
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

// Fun buttons functionality
async function fetchNews() {
    try {
        const response = await fetch('https://api.thenewsapi.com/v1/news/top?api_token=ZWNTWt7A4YuhmINhCCcTfKIYaHrk37LAiI2dhuq3&locale=us&limit=1');
        const data = await response.json();
        if (data.data && data.data[0]) {
            return `📰 ${data.data[0].title}`;
        }
        return "Could not fetch news at this time.";
    } catch (error) {
        return "Could not fetch news at this time.";
    }
}

async function fetchFunFact() {
    try {
        const response = await fetch('https://uselessfacts.jsph.pl/api/v2/facts/random');
        const data = await response.json();
        return `💡 ${data.text}`;
    } catch (error) {
        return "Could not fetch fun fact at this time.";
    }
}

async function fetchQuote() {
    try {
        const response = await fetch('https://api.quotable.io/quotes/random?maxLength=100');
        const data = await response.json();
        if (data && data[0]) {
            return `💭 "${data[0].content}" - ${data[0].author}`;
        }
        return "Could not fetch quote at this time.";
    } catch (error) {
        return "Could not fetch quote at this time.";
    }
}

function showFunContent(content) {
    const funContent = document.getElementById('funContent');
    funContent.textContent = content;
    funContent.classList.remove('show');
    void funContent.offsetWidth; // Trigger reflow
    funContent.classList.add('show');
}

// Event listeners for fun buttons
document.getElementById('newsButton').addEventListener('click', async () => {
    const news = await fetchNews();
    showFunContent(news);
});

document.getElementById('funFactButton').addEventListener('click', async () => {
    const funFact = await fetchFunFact();
    showFunContent(funFact);
});

document.getElementById('quoteButton').addEventListener('click', async () => {
    const quote = await fetchQuote();
    showFunContent(quote);
});

// Add progress update to existing functions
function displayChores(chores) {
    // ... existing code ...
    
    // Add this at the end of the function
    updateProgress();
}

// Add to the checkbox change event listener
function handleCheckboxChange(event) {
    // ... existing code ...
    
    // Add this at the end of the function
    updateProgress();
}

// Add the missing populateStaffDropdown function
async function populateStaffDropdown() {
    try {
        const response = await fetch('/api/staff');
        if (!response.ok) throw new Error('Failed to fetch staff list');
        const staff = await response.json();
        
        staffSelect.innerHTML = '<option value="">Choose your name...</option>';
        staff.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            staffSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error populating staff dropdown:', error);
        throw new Error('Failed to load staff list');
    }
} 