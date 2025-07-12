// StackIt Main JavaScript

// Initialize notification system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeNotifications();
    initializeTooltips();
    initializeAutoRefresh();
});

// Notification System
function initializeNotifications() {
    if (!window.currentUser || !window.currentUser.isAuthenticated) {
        return;
    }
    
    updateNotificationCount();
    loadNotifications();
    
    // Update notification count every 30 seconds
    setInterval(updateNotificationCount, 30000);
    
    // Load notifications when dropdown is opened
    const notificationDropdown = document.getElementById('notificationDropdown');
    if (notificationDropdown) {
        notificationDropdown.addEventListener('click', function() {
            loadNotifications();
        });
    }
}

// Update notification count badge
function updateNotificationCount() {
    fetch('/notifications/count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notificationCount');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count > 99 ? '99+' : data.count;
                    badge.style.display = 'inline';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error fetching notification count:', error));
}

// Load notifications dropdown content
function loadNotifications() {
    fetch('/notifications')
        .then(response => response.json())
        .then(data => {
            const notificationList = document.getElementById('notificationList');
            if (!notificationList) return;
            
            // Clear existing content
            notificationList.innerHTML = '<li><h6 class="dropdown-header">Notifications</h6></li>';
            
            if (data.length === 0) {
                notificationList.innerHTML += '<li><p class="dropdown-item-text text-muted">No notifications</p></li>';
                return;
            }
            
            data.forEach(notification => {
                const item = document.createElement('li');
                item.innerHTML = `
                    <a class="dropdown-item" href="${notification.link || '#'}">
                        <div class="notification-item">
                            <p class="mb-1 small">${escapeHtml(notification.message)}</p>
                            <small class="text-muted">${notification.created_at}</small>
                        </div>
                    </a>
                `;
                notificationList.appendChild(item);
            });
            
            // Add "View All" link if there are notifications
            if (data.length > 0) {
                notificationList.innerHTML += '<li><hr class="dropdown-divider"></li>';
                notificationList.innerHTML += '<li><a class="dropdown-item text-center" href="#"><small>View All Notifications</small></a></li>';
            }
        })
        .catch(error => {
            console.error('Error loading notifications:', error);
            const notificationList = document.getElementById('notificationList');
            if (notificationList) {
                notificationList.innerHTML = '<li><p class="dropdown-item-text text-danger">Error loading notifications</p></li>';
            }
        });
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Auto-refresh functionality for real-time updates
function initializeAutoRefresh() {
    // Only enable auto-refresh on question detail pages
    if (window.location.pathname.includes('/question/')) {
        // Refresh answer scores and new answers every 10 seconds
        setInterval(refreshQuestionData, 10000);
    }
}

// Refresh question data (votes, new answers)
function refreshQuestionData() {
    // This would typically make an AJAX call to get updated question data
    // For now, we'll just update vote counts if they've changed
    updateVoteScores();
}

// Update vote scores without page reload
function updateVoteScores() {
    const voteScores = document.querySelectorAll('.vote-score');
    voteScores.forEach(scoreElement => {
        const answerId = scoreElement.closest('.answer-card')?.dataset.answerId;
        if (answerId) {
            // In a real implementation, you'd fetch the current score from the server
            // fetch(`/api/answer/${answerId}/score`)
            //     .then(response => response.json())
            //     .then(data => {
            //         scoreElement.textContent = data.score;
            //     });
        }
    });
}

// Utility function to escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Vote functionality with visual feedback
function handleVote(button, answerId, voteType) {
    const scoreElement = button.closest('.vote-section').querySelector('.vote-score');
    const originalScore = parseInt(scoreElement.textContent);
    
    // Add loading state
    button.classList.add('loading');
    
    // Make vote request
    fetch(`/vote/${answerId}/${voteType}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (response.ok) {
            // Update UI optimistically
            // In a real implementation, you'd get the new score from the response
            const newScore = voteType === 'up' ? originalScore + 1 : originalScore - 1;
            scoreElement.textContent = newScore;
            
            // Add visual feedback
            scoreElement.classList.add('fade-in');
            setTimeout(() => scoreElement.classList.remove('fade-in'), 300);
        } else {
            throw new Error('Vote failed');
        }
    })
    .catch(error => {
        console.error('Error voting:', error);
        // Show error message
        showToast('Error', 'Failed to submit vote. Please try again.', 'danger');
    })
    .finally(() => {
        button.classList.remove('loading');
    });
}

// Toast notification system
function showToast(title, message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-white bg-${type} border-0`;
    toastElement.setAttribute('role', 'alert');
    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${escapeHtml(title)}</strong><br>
                ${escapeHtml(message)}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    
    toast.show();
    
    // Remove element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Get or create toast container
function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    return container;
}

// Form validation enhancements
function enhanceFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            form.classList.add('was-validated');
        });
    });
}

// Real-time character count for textareas
function initializeCharacterCounters() {
    const textareas = document.querySelectorAll('textarea[data-max-length]');
    textareas.forEach(textarea => {
        const maxLength = parseInt(textarea.dataset.maxLength);
        const counter = document.createElement('small');
        counter.className = 'text-muted';
        textarea.parentNode.appendChild(counter);
        
        function updateCounter() {
            const remaining = maxLength - textarea.value.length;
            counter.textContent = `${remaining} characters remaining`;
            counter.className = remaining < 50 ? 'text-danger' : 'text-muted';
        }
        
        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });
}

// Search functionality enhancements
function enhanceSearch() {
    const searchInputs = document.querySelectorAll('input[type="search"]');
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            // Add loading indicator
            input.classList.add('loading');
            
            searchTimeout = setTimeout(() => {
                // Remove loading indicator
                input.classList.remove('loading');
                
                // In a real implementation, you'd perform live search here
                // performLiveSearch(input.value);
            }, 300);
        });
    });
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + / to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals/dropdowns
        if (e.key === 'Escape') {
            const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
            openDropdowns.forEach(dropdown => {
                bootstrap.Dropdown.getInstance(dropdown.previousElementSibling)?.hide();
            });
        }
    });
}

// Initialize all enhancements
document.addEventListener('DOMContentLoaded', function() {
    enhanceFormValidation();
    initializeCharacterCounters();
    enhanceSearch();
    initializeKeyboardShortcuts();
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    // In production, you might want to send this to an error tracking service
});

// Service worker registration for offline functionality (future enhancement)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // navigator.serviceWorker.register('/sw.js');
    });
}

// Export functions for use in templates
window.StackIt = {
    showToast,
    handleVote,
    updateNotificationCount,
    loadNotifications
};
