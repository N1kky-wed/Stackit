// User mention functionality with autocomplete
class MentionAutocomplete {
    constructor(textareaSelector) {
        this.textarea = document.querySelector(textareaSelector);
        this.dropdown = null;
        this.users = [];
        this.currentMentionStart = -1;
        this.currentMentionEnd = -1;
        
        if (this.textarea) {
            this.init();
            this.loadUsers();
        }
    }
    
    init() {
        this.textarea.addEventListener('input', (e) => this.handleInput(e));
        this.textarea.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.textarea.addEventListener('blur', (e) => this.handleBlur(e));
    }
    
    async loadUsers() {
        try {
            const response = await fetch('/api/users');
            this.users = await response.json();
        } catch (error) {
            console.log('Could not load users for mentions');
        }
    }
    
    handleInput(e) {
        const cursorPos = this.textarea.selectionStart;
        const text = this.textarea.value;
        
        // Find @ symbol before cursor
        const beforeCursor = text.substring(0, cursorPos);
        const atIndex = beforeCursor.lastIndexOf('@');
        
        if (atIndex === -1) {
            this.hideDropdown();
            return;
        }
        
        // Check if @ is at start or preceded by whitespace
        const charBeforeAt = atIndex > 0 ? beforeCursor[atIndex - 1] : ' ';
        if (charBeforeAt !== ' ' && charBeforeAt !== '\n' && atIndex !== 0) {
            this.hideDropdown();
            return;
        }
        
        // Get the text after @
        const afterAt = beforeCursor.substring(atIndex + 1);
        
        // Check if there's whitespace in the mention (which would break it)
        if (afterAt.includes(' ') || afterAt.includes('\n')) {
            this.hideDropdown();
            return;
        }
        
        this.currentMentionStart = atIndex;
        this.currentMentionEnd = cursorPos;
        
        // Filter users based on input
        const filteredUsers = this.users.filter(user => 
            user.username.toLowerCase().includes(afterAt.toLowerCase())
        );
        
        if (filteredUsers.length > 0 && afterAt.length > 0) {
            this.showDropdown(filteredUsers, afterAt);
        } else if (afterAt.length === 0) {
            this.showDropdown(this.users.slice(0, 5), afterAt);
        } else {
            this.hideDropdown();
        }
    }
    
    handleKeydown(e) {
        if (!this.dropdown) return;
        
        const items = this.dropdown.querySelectorAll('.mention-item');
        const activeItem = this.dropdown.querySelector('.mention-item.active');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextItem = activeItem ? activeItem.nextElementSibling : items[0];
            if (nextItem) {
                if (activeItem) activeItem.classList.remove('active');
                nextItem.classList.add('active');
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevItem = activeItem ? activeItem.previousElementSibling : items[items.length - 1];
            if (prevItem) {
                if (activeItem) activeItem.classList.remove('active');
                prevItem.classList.add('active');
            }
        } else if (e.key === 'Enter' || e.key === 'Tab') {
            e.preventDefault();
            if (activeItem) {
                this.selectUser(activeItem.dataset.username);
            }
        } else if (e.key === 'Escape') {
            this.hideDropdown();
        }
    }
    
    handleBlur(e) {
        // Delay hiding to allow clicking on dropdown
        setTimeout(() => {
            if (!this.dropdown || !this.dropdown.matches(':hover')) {
                this.hideDropdown();
            }
        }, 200);
    }
    
    showDropdown(users, query) {
        this.hideDropdown();
        
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'mention-dropdown';
        this.dropdown.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            min-width: 200px;
        `;
        
        users.forEach((user, index) => {
            const item = document.createElement('div');
            item.className = 'mention-item';
            if (index === 0) item.classList.add('active');
            item.dataset.username = user.username;
            item.style.cssText = `
                padding: 8px 12px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
                display: flex;
                align-items: center;
            `;
            
            const roleColor = user.role === 'admin' ? '#dc3545' : user.role === 'ai' ? '#0d6efd' : '#6c757d';
            
            item.innerHTML = `
                <div>
                    <div style="font-weight: 500;">${user.username}</div>
                    <div style="font-size: 12px; color: ${roleColor};">${user.role}</div>
                </div>
            `;
            
            item.addEventListener('mouseenter', () => {
                this.dropdown.querySelector('.mention-item.active')?.classList.remove('active');
                item.classList.add('active');
            });
            
            item.addEventListener('click', () => {
                this.selectUser(user.username);
            });
            
            this.dropdown.appendChild(item);
        });
        
        // Position dropdown
        const rect = this.textarea.getBoundingClientRect();
        const textareaStyle = window.getComputedStyle(this.textarea);
        
        this.dropdown.style.left = rect.left + 'px';
        this.dropdown.style.top = (rect.bottom + 5) + 'px';
        
        document.body.appendChild(this.dropdown);
        
        // Style active item
        const style = document.createElement('style');
        style.textContent = `
            .mention-item.active {
                background-color: #e9ecef !important;
            }
            .mention-item:hover {
                background-color: #f8f9fa;
            }
        `;
        document.head.appendChild(style);
    }
    
    hideDropdown() {
        if (this.dropdown) {
            this.dropdown.remove();
            this.dropdown = null;
        }
    }
    
    selectUser(username) {
        const text = this.textarea.value;
        const beforeMention = text.substring(0, this.currentMentionStart);
        const afterMention = text.substring(this.currentMentionEnd);
        
        const newText = beforeMention + '@' + username + ' ' + afterMention;
        this.textarea.value = newText;
        
        const newCursorPos = this.currentMentionStart + username.length + 2;
        this.textarea.setSelectionRange(newCursorPos, newCursorPos);
        
        this.hideDropdown();
        this.textarea.focus();
        
        // Trigger input event for any listeners
        this.textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }
}

// Initialize mention autocomplete when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize for question description
    if (document.querySelector('#description')) {
        new MentionAutocomplete('#description');
    }
    
    // Initialize for answer content
    if (document.querySelector('#content')) {
        new MentionAutocomplete('#content');
    }
});