/**
 * Main JavaScript for MWHEBA Stock
 */

// Wait for DOM to be loaded
document.addEventListener("DOMContentLoaded", function() {
    // Check if bootstrap is defined before using it
    if (typeof bootstrap !== 'undefined') {
        // Initialize Bootstrap dropdowns
        var dropdownElementList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'))
        var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
            return new bootstrap.Dropdown(dropdownToggleEl)
        });

        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Ensure all header dropdowns work properly
        document.querySelectorAll('.header-right .dropdown-toggle').forEach(function(dropdown) {
            dropdown.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        });
        
        // Auto-hide alerts after 5 seconds
        setTimeout(function() {
            const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
            alerts.forEach(function(alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 5000);
        
        // Handle live search inputs
        const searchInputs = document.querySelectorAll('.live-search');
        searchInputs.forEach(input => {
            input.addEventListener('input', function() {
                let searchTerm = this.value.toLowerCase();
                let targetId = this.getAttribute('data-search-target');
                let targetRows = document.querySelectorAll(`#${targetId} tbody tr`);
                
                targetRows.forEach(row => {
                    const textContent = row.textContent.toLowerCase();
                    if (textContent.includes(searchTerm)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        });

        // Format number inputs with currency symbol
        document.querySelectorAll('.currency-input').forEach(input => {
            input.addEventListener('blur', function() {
                let value = parseFloat(this.value);
                if (!isNaN(value)) {
                    this.value = value.toFixed(2);
                }
            });
        });
        
        // Special handling for quick actions dropdown
        const quickActionsDropdown = document.getElementById('quickActionsDropdown');
        if (quickActionsDropdown) {
            quickActionsDropdown.addEventListener('click', function(e) {
                const dropdown = bootstrap.Dropdown.getInstance(quickActionsDropdown);
                if (!dropdown) {
                    new bootstrap.Dropdown(quickActionsDropdown).toggle();
                }
            });
        }
    }
});

/**
 * Helper function to format currency
 * @param {number} amount - The amount to format
 * @returns {string} Formatted amount with EGP symbol
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('ar-EG', { 
        style: 'currency', 
        currency: 'EGP',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Helper function to format date in Arabic locale
 * @param {Date} date - The date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    return new Intl.DateTimeFormat('ar-EG', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    }).format(new Date(date));
}

/**
 * Toggle a modal dialog
 * @param {string} modalId - The ID of the modal to toggle
 */
function toggleModal(modalId) {
    const modalElement = document.getElementById(modalId);
    const modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);
    modalInstance.toggle();
}

/**
 * Load content into a modal via AJAX
 * @param {string} url - The URL to fetch content from
 * @param {string} modalId - The ID of the modal to load content into
 */
function loadModalContent(url, modalId) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            const modalBody = document.querySelector(`#${modalId} .modal-body`);
            modalBody.innerHTML = html;
            toggleModal(modalId);
        })
        .catch(error => {
            console.error('Error loading modal content:', error);
        });
}
