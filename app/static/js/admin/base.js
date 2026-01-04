// app/static/js/admin/base.js
// app/static/js/admin/base.js - ADD THIS AT THE TOP
console.log('=== BASE.JS LOADED ===');
console.log('Timestamp:', new Date().toISOString());
console.log('showToast function exists:', typeof showToast === 'function');
console.log('formatCurrency function exists:', typeof formatCurrency === 'function');
// ===== BASE ADMIN JAVASCRIPT =====
// Common functions used across all admin pages

// Toast notification function
function showToast(message, type = 'success') {
    // Remove existing toasts to prevent stacking
    document.querySelectorAll('.toast-notification').forEach(toast => {
        toast.remove();
    });
    
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `
        <div class="toast-message">${message}</div>
        <button class="toast-close">&times;</button>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast with animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }, 5000);
    
    // Manual close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    });
}

// Handle flash messages on page load
function handleFlashMessages() {
    // This function will be populated by Flask template
    // {% with messages = get_flashed_messages(with_categories=true) %}
    // {% if messages %}
    // {% for category, message in messages %}
    // showToast('{{ message }}', '{{ category if category != "message" else "success" }}');
    // {% endfor %}
    // {% endif %}
    // {% endwith %}
}

// Common utility functions
function formatCurrency(amount) {
    if (typeof amount !== 'number') {
        amount = parseFloat(amount) || 0;
    }
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid Date';
    
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatTime(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid Time';
    
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Form validation helper
function validateForm(formId, options = {}) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const errors = [];
    
    // Validate required fields
    form.querySelectorAll('[required]').forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
            errors.push(`${field.name || field.id} is required`);
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    // Email validation
    form.querySelectorAll('input[type="email"]').forEach(field => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (field.value && !emailRegex.test(field.value)) {
            isValid = false;
            field.classList.add('is-invalid');
            errors.push('Invalid email format');
        }
    });
    
    // Show errors if any
    if (!isValid && options.showErrors !== false) {
        showToast(errors.join(', '), 'error');
    }
    
    return isValid;
}

// Toggle loading state for buttons
function setButtonLoading(button, isLoading, loadingText = 'Loading...') {
    if (!button) return;
    
    if (isLoading) {
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${loadingText}`;
        button.disabled = true;
    } else {
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
        button.disabled = false;
    }
}

// Confirm dialog helper
function confirmAction(message, callback) {
    if (confirm(message)) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

// Initialize tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize popovers
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Debounce function for performance
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

// Throttle function for performance
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(
        () => showToast('Copied to clipboard!', 'success'),
        (err) => showToast('Failed to copy: ' + err, 'error')
    );
}

// Initialize common functionality
function initAdminBase() {
    console.log('Admin base initialized');
    
    // Initialize Bootstrap components
    initTooltips();
    initPopovers();
    
    // Add some global event listeners
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[name="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    });
    
    // Handle form submissions with loading states
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                setButtonLoading(submitButton, true, 'Processing...');
            }
        });
    });
    
    // Add copy buttons for code/text
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.dataset.copy || 
                              this.previousElementSibling?.textContent || 
                              this.parentElement.querySelector('code')?.textContent;
            if (textToCopy) {
                copyToClipboard(textToCopy);
            }
        });
    });
}

// Wait for DOM to load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAdminBase);
} else {
    initAdminBase();
}

// Make functions available globally
window.showToast = showToast;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.validateForm = validateForm;
window.setButtonLoading = setButtonLoading;
window.confirmAction = confirmAction;
window.copyToClipboard = copyToClipboard;