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

    let currentChores = [];
    let choreUpdateQueue = [];
    let isProcessingQueue = false;

    // Event Listeners
    checklistSelect.addEventListener('change', loadChecklist);
    staffSelect.addEventListener('change', updateUI);
    clearSignatureBtn.addEventListener('click', () => signaturePad.clear());
    submitChecklistBtn.addEventListener('click', submitChecklist);

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
        let currentSection = '';
        let completedCount = 0;
        let sectionChores = [];
        
        currentChores.forEach(chore => {
            // Check for section headers (denoted by # in the description)
            if (chore.description.startsWith('# ')) {
                // If we were collecting chores for a previous section, render it
                if (currentSection && sectionChores.length > 0) {
                    renderSection(currentSection, sectionChores);
                    sectionChores = [];
                }
                
                currentSection = chore.description.substring(2);
                return;
            }

            // Check for sub-headers (denoted by - at the start)
            if (chore.description.startsWith('- ')) {
                const subHeader = document.createElement('div');
                subHeader.className = 'sub-header ps-3 py-2';
                subHeader.textContent = chore.description.substring(2);
                choresContainer.appendChild(subHeader);
                return;
            }

            if (chore.completed) {
                completedCount++;
            }

            // Add chore to current section
            if (currentSection) {
                sectionChores.push(chore);
            } else {
                // If no section, render chore directly
                renderChore(chore);
            }
        });

        // Render the last section if any
        if (currentSection && sectionChores.length > 0) {
            renderSection(currentSection, sectionChores);
        }

        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = (completedCount / currentChores.length) * 100;
        progressBar.querySelector('.progress-bar').style.width = `${progressPercentage}%`;
        progressBar.classList.remove('d-none');

        updateSignatureSection();
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
        checkbox.addEventListener('change', () => handleChoreCompletion(chore.id, checkbox));

        const commentInput = choreDiv.querySelector('input[type="text"]');
        commentInput.addEventListener('click', (e) => e.stopPropagation());
        commentInput.addEventListener('change', () => handleChoreComment(chore.id, commentInput.value));

        choresContainer.appendChild(choreDiv);
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