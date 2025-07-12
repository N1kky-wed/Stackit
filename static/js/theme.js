// Dark theme functionality
function toggleTheme() {
    const body = document.body;
    const themeIcon = document.getElementById('themeIcon');
    const isDark = body.classList.contains('dark-theme');
    
    if (isDark) {
        body.classList.remove('dark-theme');
        themeIcon.className = 'fas fa-moon';
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-theme');
        themeIcon.className = 'fas fa-sun';
        localStorage.setItem('theme', 'dark');
    }
}

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    const themeIcon = document.getElementById('themeIcon');
    
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        if (themeIcon) themeIcon.className = 'fas fa-sun';
    }
});

// Custom confirmation dialog
function showCustomConfirm(title, message, onConfirm, onCancel = null) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header border-0">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="mb-0">${message}</p>
                </div>
                <div class="modal-footer border-0">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" id="confirmBtn">Delete</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bootstrapModal = new bootstrap.Modal(modal);
    
    modal.querySelector('#confirmBtn').addEventListener('click', function() {
        bootstrapModal.hide();
        if (onConfirm) onConfirm();
    });
    
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
        if (onCancel) onCancel();
    });
    
    bootstrapModal.show();
}

// Global delete confirmation function
function confirmDelete(questionId) {
    showCustomConfirm(
        'Delete Question',
        'Are you sure you want to delete this question? This action cannot be undone.',
        function() {
            window.location.href = `/delete_question/${questionId}`;
        }
    );
    return false;
}

function confirmAnswerDelete(answerId) {
    showCustomConfirm(
        'Delete Answer',
        'Are you sure you want to delete this answer? This action cannot be undone.',
        function() {
            window.location.href = `/admin/delete_answer/${answerId}`;
        }
    );
    return false;
}