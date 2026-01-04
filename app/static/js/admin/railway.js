// static/js/admin/railway.js
// Sidebar toggle for mobile
document.getElementById('sidebarToggle').addEventListener('click', function() {
    document.getElementById('sidebar').classList.toggle('active');
});

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    
    if (window.innerWidth <= 768) {
        if (!sidebar.contains(event.target) && !toggleBtn.contains(event.target)) {
            sidebar.classList.remove('active');
        }
    }
});

// Toast notification function
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `
        <div class="toast-message">${message}</div>
        <button class="toast-close">&times;</button>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
    
    // Close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    });
}

// Update time function
function updateTime() {
    const now = new Date();
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        timeElement.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    }
}

// Initialize animations and functions
document.addEventListener('DOMContentLoaded', function() {
    // Update time initially and set interval
    updateTime();
    setInterval(updateTime, 60000);
    
    // Add hover effects to cards
    const cards = document.querySelectorAll('.stat-card, .quick-action-btn, .status-card, .stat-item');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Animate stat numbers with counting effect
    const statNumbers = document.querySelectorAll('.stat-number, .stat-number-horizontal:not(#currentTime)');
    statNumbers.forEach(stat => {
        const originalText = stat.textContent.trim();
        const numValue = parseInt(originalText.replace(/[^0-9]/g, ''));
        
        if (!isNaN(numValue) && numValue > 0) {
            stat.textContent = '0';
            
            let counter = 0;
            const target = numValue;
            const increment = target / 50;
            
            const updateCounter = () => {
                if (counter < target) {
                    counter += increment;
                    stat.textContent = Math.floor(counter).toLocaleString();
                    setTimeout(updateCounter, 20);
                } else {
                    stat.textContent = target.toLocaleString();
                }
            };
            
            setTimeout(updateCounter, 300);
        }
    });
    
    // Auto-show welcome toast (optional)
    setTimeout(() => {
        showToast('Dashboard loaded successfully!', 'success');
    }, 1000);
});
