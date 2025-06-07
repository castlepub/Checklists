document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    const checklistSelect = document.getElementById('checklistSelect');
    const staffSelect = document.getElementById('staffSelect');
    const choresList = document.getElementById('choresList');
    const choresContainer = document.getElementById('choresContainer');
    const signatureSection = document.getElementById('signatureSection');
    const signaturePad = new SignaturePad(document.getElementById('signaturePad'));
    const clearSignatureBtn = document.getElementById('clearSignature');
    const submitChecklistBtn = document.getElementById('submitChecklist');

    let currentChores = [];

    // Event Listeners
    checklistSelect.addEventListener('change', loadChecklist);
    staffSelect.addEventListener('change', updateUI);
    clearSignatureBtn.addEventListener('click', () => signaturePad.clear());
    submitChecklistBtn.addEventListener('click', submitChecklist);

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
        } catch (error) {
            console.error('Error loading checklist:', error);
            alert('Failed to load checklist. Please try again.');
        }
    }

    function renderChores() {
        choresContainer.innerHTML = '';
        
        currentChores.forEach(chore => {
            const choreDiv = document.createElement('div');
            choreDiv.className = 'chore-item';
            choreDiv.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="chore-${chore.id}" 
                           ${chore.completed ? 'checked' : ''}>
                </div>
                <div class="flex-grow-1">
                    <label class="form-check-label" for="chore-${chore.id}">
                        ${chore.description}
                    </label>
                    <div class="chore-comment">
                        <input type="text" class="form-control form-control-sm" 
                               placeholder="Add comment (optional)" 
                               value="${chore.comment || ''}"
                               data-chore-id="${chore.id}">
                    </div>
                </div>
            `;

            const checkbox = choreDiv.querySelector('input[type="checkbox"]');
            checkbox.addEventListener('change', () => handleChoreCompletion(chore.id, checkbox));

            const commentInput = choreDiv.querySelector('input[type="text"]');
            commentInput.addEventListener('change', () => handleChoreComment(chore.id, commentInput.value));

            choresContainer.appendChild(choreDiv);
        });

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