// static/js/mentions.js

class MentionAutocomplete {
    constructor(quill) {
        this.quill = quill;
        this.container = quill.container.parentNode.querySelector('.mention-dropdown-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'mention-dropdown-container';
            quill.container.parentNode.appendChild(this.container);
        }
        this.dropdown = null;
        this.users = [];
        this.mentionStartIndex = -1;
        
        this.init();
    }

    async init() {
        await this.loadUsers();
        
        this.quill.on('text-change', (delta, oldDelta, source) => {
            if (source === 'user') {
                this.handleInput();
            }
        });

        // Register keyboard bindings
        this.quill.keyboard.addBinding({ key: 'ArrowDown' }, this.navigateDropdown.bind(this, 'down'));
        this.quill.keyboard.addBinding({ key: 'ArrowUp' }, this.navigateDropdown.bind(this, 'up'));
        this.quill.keyboard.addBinding({ key: 'Enter' }, (range, context) => {
            if (this.dropdown) {
                this.selectActiveUser();
                return false; // Prevent Quill from handling Enter
            }
            return true; // Allow Quill to handle Enter normally
        });
        this.quill.keyboard.addBinding({ key: 'Escape' }, this.hideDropdown.bind(this));
    }

    async loadUsers() {
        try {
            const response = await fetch('/api/users');
            if (!response.ok) throw new Error('Failed to load users');
            this.users = await response.json();
        } catch (error) {
            console.error('Could not load users for mentions:', error);
        }
    }

    handleInput() {
        const selection = this.quill.getSelection();
        if (!selection) {
            this.hideDropdown();
            return;
        }
        
        // FIX: Use Quill v2 compatible method to get text before cursor
        const textBeforeCursor = this.quill.getText(0, selection.index);
        const atIndex = textBeforeCursor.lastIndexOf('@');

        if (atIndex === -1) {
            this.hideDropdown();
            return;
        }
        
        const query = textBeforeCursor.substring(atIndex + 1);
        if (/\s/.test(query)) {
            this.hideDropdown();
            return;
        }

        this.mentionStartIndex = atIndex;
        const filteredUsers = this.users.filter(user => user.username.toLowerCase().startsWith(query.toLowerCase()));
        
        if (filteredUsers.length > 0) {
            this.showDropdown(filteredUsers);
        } else {
            this.hideDropdown();
        }
    }

    showDropdown(users) {
        this.hideDropdown(true);
        
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'mention-dropdown list-group shadow-sm';
        
        users.slice(0, 5).forEach((user, index) => {
            const item = document.createElement('a');
            item.href = "#";
            item.className = 'mention-item list-group-item list-group-item-action p-2';
            if (index === 0) item.classList.add('active');
            item.dataset.username = user.username;
            item.innerHTML = `<span class="fw-bold">${user.username}</span> <small class="text-muted ms-1">(${user.role})</small>`;
            item.addEventListener('mousedown', (e) => { // Use mousedown to fire before blur
                e.preventDefault();
                this.selectUser(user.username);
            });
            this.dropdown.appendChild(item);
        });

        this.container.appendChild(this.dropdown);
        this.positionDropdown();
    }
    
    positionDropdown() {
        const bounds = this.quill.getBounds(this.mentionStartIndex);
        this.dropdown.style.position = 'absolute';
        this.dropdown.style.left = `${bounds.left}px`;
        this.dropdown.style.top = `${bounds.bottom + 5}px`;
        this.dropdown.style.zIndex = '1050'; // Ensure it's above other elements
    }

    hideDropdown() {
        if (this.dropdown) {
            this.dropdown.remove();
            this.dropdown = null;
        }
        return true; // Let other handlers run
    }

    navigateDropdown(direction) {
        if (!this.dropdown) return true;
        const active = this.dropdown.querySelector('.active');
        let next;
        if (direction === 'down') {
            next = active.nextElementSibling || this.dropdown.firstChild;
        } else {
            next = active.previousElementSibling || this.dropdown.lastChild;
        }
        if (active) active.classList.remove('active');
        if (next) next.classList.add('active');
        return false; // Prevent default arrow behavior
    }

    selectActiveUser() {
        if (!this.dropdown) return;
        const active = this.dropdown.querySelector('.active');
        if (active) {
            this.selectUser(active.dataset.username);
        }
    }

    selectUser(username) {
        const selection = this.quill.getSelection();
        const queryLength = selection.index - this.mentionStartIndex;
        
        this.quill.deleteText(this.mentionStartIndex, queryLength);
        this.quill.insertText(this.mentionStartIndex, username + ' ');
        this.quill.setSelection(this.mentionStartIndex + username.length + 1);
        this.hideDropdown();
    }
}