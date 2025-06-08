document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    const checklistSelect = document.getElementById('checklistSelect');
    const staffSelect = document.getElementById('staffSelect');
    const choresList = document.getElementById('choresList');
    const choresContainer = document.getElementById('choresContainer');
    const signatureSection = document.getElementById('signatureSection');
    const signaturePad = new SignaturePad(document.getElementById('signaturePad'), {
        minWidth: 2,
        maxWidth: 4,
        penColor: "rgb(0, 0, 0)"
    });
    const clearSignatureBtn = document.getElementById('clearSignature');
    const submitChecklistBtn = document.getElementById('submitChecklist');
    const resetChecklistBtn = document.getElementById('resetChecklist');

    let currentChores = [];
    let choreUpdateQueue = [];
    let isProcessingQueue = false;

    // Add at the top of the file after existing variables
    const encouragements = [
        { threshold: 0, emoji: "🌱", message: "Let's get started!" },
        { threshold: 0.25, emoji: "🌿", message: "Great progress!" },
        { threshold: 0.50, emoji: "🌳", message: "Halfway there!" },
        { threshold: 0.75, emoji: "🌺", message: "Almost done!" },
        { threshold: 1, emoji: "🎉", message: "Amazing work!" }
    ];

    const funFacts = [
        "Did you know? The oldest pub in England is Ye Olde Man & Scythe in Bolton, dating back to 1251! 🍺",
        "The term 'pub' comes from 'public house' - they were originally private houses that served alcohol! 🏠",
        "The first pubs were Roman taverns, built along Roman roads in Britain! 🛣️",
        "The tradition of clinking glasses comes from medieval times when people would splash drinks into each other's cups to prove they weren't poisoned! 🥂",
        "The world's longest pub crawl would take 27 years to visit every pub in the UK! 🚶‍♂️",
        "The oldest known recipe for beer is over 4,000 years old! 🍻",
        "In medieval England, pub visitors used to drink from leather tankards! 🥤",
        "The first beer was made by accident when grain got wet, fermented, and created a primitive beer! 🌾",
        "Some medieval pubs had beds upstairs, making them the first hotels! 🛏️",
        "The tradition of 'last orders' began during WW1 to help factory workers stay productive! ⏰"
    ];

    let lastFunFactIndex = -1;
    let achievementsShown = new Set();

    function getRandomFunFact() {
        let index;
        do {
            index = Math.floor(Math.random() * funFacts.length);
        } while (index === lastFunFactIndex);
        lastFunFactIndex = index;
        return funFacts[index];
    }

    function showAchievement(message, emoji) {
        if (achievementsShown.has(message)) return;
        achievementsShown.add(message);
        
        const achievement = document.createElement('div');
        achievement.className = 'achievement';
        achievement.innerHTML = `
            <div class="achievement-content">
                <div class="achievement-emoji">${emoji}</div>
                <div class="achievement-message">${message}</div>
            </div>
        `;
        document.body.appendChild(achievement);
        
        // Animate in
        setTimeout(() => achievement.classList.add('show'), 100);
        
        // Remove after animation
        setTimeout(() => {
            achievement.classList.remove('show');
            setTimeout(() => achievement.remove(), 500);
        }, 3000);
    }

    function updateProgressIndicator() {
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
        
        // Show achievements for milestones
        if (progress === 0.25) showAchievement("Quarter Way Hero! 🌟", "Keep up the great work!");
        if (progress === 0.50) showAchievement("Halfway Champion! 🏆", "You're crushing it!");
        if (progress === 0.75) showAchievement("Almost There! ⭐", "The finish line is in sight!");
        if (progress === 1) showAchievement("Checklist Master! 👑", "You've completed everything!");
        
        // Show random fun fact every 3 completed tasks
        if (completedChores > 0 && completedChores % 3 === 0) {
            showAchievement("Did You Know? 💡", getRandomFunFact());
        }
    }

    // Event Listeners
    checklistSelect.addEventListener('change', loadChecklist);
    staffSelect.addEventListener('change', updateUI);
    clearSignatureBtn.addEventListener('click', () => signaturePad.clear());
    submitChecklistBtn.addEventListener('click', submitChecklist);
    resetChecklistBtn.addEventListener('click', async () => {
        const checklistName = checklistSelect.value;
        if (!checklistName) return;
        
        if (!confirm(`Are you sure you want to reset the ${checklistName} checklist? This will remove all completed tasks and signatures.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/reset_checklist/${checklistName}`, {
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

    // Show/hide reset button based on checklist selection
    checklistSelect.addEventListener('change', () => {
        resetChecklistBtn.style.display = checklistSelect.value ? 'block' : 'none';
    });

    // Handle orientation change for signature pad
    window.addEventListener('resize', resizeSignaturePad);

    function resizeSignaturePad() {
        const canvas = document.getElementById('signaturePad');
        const ratio = Math.max(window.devicePixelRatio || 1, 1);
        canvas.width = canvas.offsetWidth * ratio;
        canvas.height = canvas.offsetHeight * ratio;
        canvas.getContext("2d").scale(ratio, ratio);
        signaturePad.clear(); // Clear and reset the signature pad
    }

    function updateUI() {
        const checklistSelected = checklistSelect.value !== '';
        const staffSelected = staffSelect.value !== '';
        
        if (checklistSelected && staffSelected) {
            loadChecklist();
        } else {
            choresList.classList.add('d-none');
            signatureSection.classList.add('d-none');
        }
    }

    async function loadChecklist() {
        if (!checklistSelect.value || !staffSelect.value) return;

        try {
            const response = await fetch(`/api/checklists/${checklistSelect.value}/chores`);
            const data = await response.json();
            currentChores = data;
            
            renderChores();
            choresList.classList.remove('d-none');
            updateSignatureSection();
            resizeSignaturePad();
        } catch (error) {
            console.error('Error loading checklist:', error);
            alert('Failed to load checklist. Please try again.');
        }
    }

    function renderChores() {
        choresContainer.innerHTML = '';
        
        // Add progress display
        const progressDiv = document.createElement('div');
        progressDiv.id = 'progressDisplay';
        progressDiv.className = 'progress-display';
        choresContainer.appendChild(progressDiv);
        
        // Group chores by section
        const sections = {};
        currentChores.forEach(chore => {
            const sectionMatch = chore.description.match(/^([^:]+):/);
            const sectionName = sectionMatch ? sectionMatch[1] : 'General Tasks';
            if (!sections[sectionName]) sections[sectionName] = [];
            sections[sectionName].push(chore);
        });
        
        // Render each section
        Object.entries(sections).forEach(([sectionName, sectionChores]) => {
            renderSection(sectionName, sectionChores);
        });
        
        updateProgressIndicator();
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

    function renderSection(sectionName, sectionChores) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'section';

        // Create section header with checkbox
        const headerDiv = document.createElement('div');
        headerDiv.className = 'section-header d-flex align-items-center';
        
        const allCompleted = sectionChores.every(chore => chore.completed);
        const someCompleted = sectionChores.some(chore => chore.completed);
        
        headerDiv.innerHTML = `
            <div class="form-check">
                <input class="form-check-input section-checkbox" type="checkbox" 
                       id="section-${sectionName.replace(/\s+/g, '-')}"
                       ${allCompleted ? 'checked' : ''}>
            </div>
            <h3 class="mb-0 ms-2">${sectionName}</h3>
        `;

        // Add indeterminate state if some but not all chores are completed
        if (someCompleted && !allCompleted) {
            headerDiv.querySelector('.section-checkbox').indeterminate = true;
        }

        sectionDiv.appendChild(headerDiv);

        // Create container for section's chores
        const choresDiv = document.createElement('div');
        choresDiv.className = 'section-chores ps-4';

        // Add each chore to the section
        sectionChores.forEach(chore => {
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
                    <div class="completion-info">
                        <small class="text-success">
                            ✓ Done by ${chore.completed_by} at ${timeString}
                        </small>
                    </div>
                `;
            }

            choreDiv.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input chore-checkbox" type="checkbox" 
                           id="chore-${chore.id}" data-section="${sectionName}"
                           ${chore.completed ? 'checked' : ''}>
                </div>
                <div class="flex-grow-1">
                    <label class="form-check-label" for="chore-${chore.id}">
                        ${chore.description}
                    </label>
                    ${completionInfo}
                    <div class="chore-comment">
                        <input type="text" class="form-control form-control-sm" 
                               placeholder="Add comment (optional)" 
                               value="${chore.comment || ''}"
                               data-chore-id="${chore.id}">
                    </div>
                </div>
            `;

            // Add event listeners
            const checkbox = choreDiv.querySelector('.chore-checkbox');
            checkbox.addEventListener('change', () => {
                handleChoreCompletion(chore.id, checkbox);
                updateSectionCheckbox(sectionName);
            });

            const commentInput = choreDiv.querySelector('input[type="text"]');
            commentInput.addEventListener('click', (e) => e.stopPropagation());
            commentInput.addEventListener('change', () => handleChoreComment(chore.id, commentInput.value));

            choresDiv.appendChild(choreDiv);
        });

        // Add section checkbox event listener
        const sectionCheckbox = headerDiv.querySelector('.section-checkbox');
        sectionCheckbox.addEventListener('change', async () => {
            const choreCheckboxes = choresDiv.querySelectorAll('.chore-checkbox');
            await handleSectionCheckboxChange(sectionCheckbox, choreCheckboxes);
        });

        sectionDiv.appendChild(choresDiv);
        choresContainer.appendChild(sectionDiv);
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
                <div class="completion-info">
                    <small class="text-success">
                        ✓ Done by ${chore.completed_by} at ${timeString}
                        ${chore.comment ? `<br>Comment: ${chore.comment}` : ''}
                    </small>
                </div>
            `;
        }

        choreDiv.innerHTML = `
            <div class="form-check">
                <input class="form-check-input chore-checkbox" type="checkbox" 
                       id="chore-${chore.id}"
                       ${chore.completed ? 'checked' : ''}>
            </div>
            <div class="flex-grow-1">
                <label class="form-check-label" for="chore-${chore.id}">
                    ${chore.description}
                </label>
                ${completionInfo}
                ${!chore.completed ? `
                <div class="chore-comment">
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
            
            setTimeout(() => checkmark.remove(), 1000);
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
        signatureSection.classList.toggle('d-none', !allChoresCompleted);
        
        if (allChoresCompleted) {
            signaturePad.clear();
            resizeSignaturePad();
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
}); 