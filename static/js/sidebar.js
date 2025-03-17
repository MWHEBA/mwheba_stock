/**
 * MWHEBA Stock - Sidebar Menu Controller
 * Advanced implementation for handling sidebar menus with smooth transitions
 * 
 * @author MWHEBA Team
 * @version 1.1.0
 */

class SidebarController {
    constructor() {
        // DOM Elements
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
        this.submenuToggles = document.querySelectorAll('.sidebar-menu .dropdown-toggle');
        this.submenus = document.querySelectorAll('.sidebar-menu .sub-menu');
        
        // State
        this.isSmallScreen = window.matchMedia('(max-width: 768px)').matches;
        
        // Initialize
        this.setupEventListeners();
    }
    
    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Main sidebar toggle button
        if (this.sidebarToggleBtn && this.sidebar) {
            this.sidebarToggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleSidebar();
            });
        }
        
        // Submenu toggle buttons
        this.submenuToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleSubmenu(toggle);
            });
        });
        
        // Close sidebar when clicking outside on mobile
        if (this.isSmallScreen) {
            document.addEventListener('click', (e) => {
                if (this.sidebar && !this.sidebar.contains(e.target) && 
                    this.sidebarToggleBtn && !this.sidebarToggleBtn.contains(e.target) &&
                    this.sidebar.classList.contains('active')) {
                    this.sidebar.classList.remove('active');
                }
            });
        }
        
        // Handle resize events
        window.addEventListener('resize', () => {
            this.isSmallScreen = window.matchMedia('(max-width: 768px)').matches;
        });
    }
    
    /**
     * Toggle the sidebar visibility
     */
    toggleSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.toggle('active');
        }
    }
    
    /**
     * Toggle a submenu open/closed
     * @param {HTMLElement} toggleButton - The toggle button clicked
     */
    toggleSubmenu(toggleButton) {
        // Get target submenu
        const targetId = toggleButton.getAttribute('href');
        if (!targetId) return;
        
        const targetSubmenu = document.querySelector(targetId);
        if (!targetSubmenu) return;
        
        const isCurrentlyOpen = targetSubmenu.classList.contains('show');
        
        // Close all open submenus
        this.closeAllSubmenus();
        
        // If clicked menu was closed, open it
        if (!isCurrentlyOpen) {
            this.openSubmenu(targetSubmenu, toggleButton);
        }
    }
    
    /**
     * Close all open submenus
     */
    closeAllSubmenus() {
        // Remove 'show' class from all submenus
        this.submenus.forEach(submenu => {
            submenu.classList.remove('show');
        });
        
        // Remove active state from all toggles
        this.submenuToggles.forEach(toggle => {
            toggle.classList.remove('active-toggle');
        });
    }
    
    /**
     * Open a specific submenu
     * @param {HTMLElement} submenu - The submenu element to open
     * @param {HTMLElement} toggleButton - The related toggle button
     */
    openSubmenu(submenu, toggleButton) {
        // Show the submenu
        submenu.classList.add('show');
        
        // Set active state on toggle button
        toggleButton.classList.add('active-toggle');
    }
}

/**
 * Initialize sidebar when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    const sidebarController = new SidebarController();
    
    // Make it globally accessible for debugging or external access
    window.sidebarController = sidebarController;
    
    // Log initialization
    console.log('MWHEBA Stock: Sidebar Controller Initialized');
});
