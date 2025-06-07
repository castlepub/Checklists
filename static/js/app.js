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
        
        currentChores.forEach(chore => {
            // Check for section headers (denoted by # in the description)
            if (chore.description.startsWith('# ')) {
                currentSection = chore.description.substring(2);
                const sectionHeader = document.createElement('h3');
                sectionHeader.className = 'section-header';
                sectionHeader.textContent = currentSection;
                choresContainer.appendChild(sectionHeader);
                return;
            }

            if (chore.completed) {
                completedCount++;
            }

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
                    <input class="form-check-input" type="checkbox" id="chore-${chore.id}" 
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

            // Add touch-friendly event listeners
            const checkbox = choreDiv.querySelector('input[type="checkbox"]');
            const label = choreDiv.querySelector('.form-check-label');

            // Make the entire chore item clickable
            choreDiv.addEventListener('click', (e) => {
                // Don't toggle if clicking the comment input
                if (e.target.type !== 'text') {
                    checkbox.checked = !checkbox.checked;
                    handleChoreCompletion(chore.id, checkbox);
                }
            });

            // Prevent double-triggering when clicking checkbox directly
            checkbox.addEventListener('click', (e) => {
                e.stopPropagation();
            });

            // Handle comment input
            const commentInput = choreDiv.querySelector('input[type="text"]');
            commentInput.addEventListener('click', (e) => e.stopPropagation());
            commentInput.addEventListener('change', () => handleChoreComment(chore.id, commentInput.value));

            choresContainer.appendChild(choreDiv);
        });

        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = (completedCount / currentChores.length) * 100;
        progressBar.querySelector('.progress-bar').style.width = `${progressPercentage}%`;
        progressBar.classList.remove('d-none');

        updateSignatureSection();
    }

    async function handleChoreCompletion(choreId, checkbox) {
        const staffName = staffSelect.value;
        
        try {
            const response = await fetch('/api/chore_completion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    chore_id: choreId,
                    staff_name: staffName,
                    completed: checkbox.checked
                })
            });

            if (!response.ok) throw new Error('Failed to update chore status');
            
            const chore = currentChores.find(c => c.id === choreId);
            chore.completed = checkbox.checked;
            updateSignatureSection();
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
        signatureSection.classList.toggle('d-none', !allChoresCompleted);
        
        if (allChoresCompleted) {
            signaturePad.clear();
        }
    }

    async function submitChecklist() {
        if (signaturePad.isEmpty()) {
            alert('Please sign before submitting.');
            return;
        }

        const staffName = staffSelect.value;
        const checklistId = checklistSelect.value;
        
        try {
            const response = await fetch('/api/submit_checklist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    checklist_id: checklistId,
                    staff_name: staffName,
                    signature_data: signaturePad.toDataURL()
                })
            });

            if (!response.ok) throw new Error('Failed to submit checklist');
            
            alert('Checklist submitted successfully!');
            checklistSelect.value = '';
            staffSelect.value = '';
            currentChores = [];
            updateUI();
        } catch (error) {
            console.error('Error submitting checklist:', error);
            alert('Failed to submit checklist. Please try again.');
        }
    }
}); 