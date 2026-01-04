// app/static/js/admin/dashboard.js

// Dashboard-specific JavaScript functions

// Initialize dashboard
function initDashboard() {
    console.log('Dashboard initialized');
    
    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(event.target) && 
                    !sidebarToggle.contains(event.target)) {
                    sidebar.classList.remove('active');
                }
            }
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
    
    // Update time initially and set interval
    updateTime();
    setInterval(updateTime, 60000);
    
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
    
    // Auto-show welcome toast
    setTimeout(() => {
        showToast('Dashboard loaded successfully!', 'success');
    }, 1000);
}

// Wait for DOM to load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

// Make function available globally
window.initDashboard = initDashboard;
