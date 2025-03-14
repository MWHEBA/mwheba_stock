// Purchase Order Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener for the "Add Purchase Order" button
    const addPurchaseOrderButtons = document.querySelectorAll('[data-bs-target="#addPurchaseOrderModal"]');
    addPurchaseOrderButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Reset the form
            document.getElementById('addPurchaseOrderForm').reset();
            
            // Clear any hidden input for purchase order ID
            const orderIdInput = document.getElementById('editPurchaseOrderId');
            if (orderIdInput) {
                orderIdInput.value = '';
            }
            
            // Reset the modal title
            document.getElementById('addPurchaseOrderModalLabel').textContent = 'إضافة مشتريات جديدة';
            
            // Reset the save button text
            document.getElementById('savePurchaseOrderBtn').textContent = 'حفظ الطلب';
            
            // Clear the items table except for the first row
            const tbody = document.querySelector('#purchaseOrderItemsTable tbody');
            const rows = tbody.querySelectorAll('tr');
            
            // Keep only the first row
            if (rows.length > 1) {
                for (let i = rows.length - 1; i > 0; i--) {
                    rows[i].remove();
                }
            }
            
            // Reset the first row
            const firstRow = tbody.querySelector('tr');
            if (firstRow) {
                const productSelect = firstRow.querySelector('.product-select');
                const quantityInput = firstRow.querySelector('.item-quantity');
                const priceInput = firstRow.querySelector('.item-price');
                const totalInput = firstRow.querySelector('.item-total');
                
                if (productSelect) productSelect.selectedIndex = 0;
                if (quantityInput) quantityInput.value = 1;
                if (priceInput) priceInput.value = '0.00';
                if (totalInput) totalInput.value = '0.00';
                
                // Populate the product select
                populateProductSelect(productSelect);
            }
            
            // Reset totals
            document.getElementById('purchaseOrderSubtotal').value = '0.00';
            document.getElementById('purchaseOrderDiscount').value = '0.00';
            document.getElementById('purchaseOrderTotal').value = '0.00';
        });
    });
    // Fetch products from API and store them for later use
    let productsData = [];
    
    // Function to fetch products
    function fetchProducts() {
        fetch('/api/products/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                productsData = data.products;
                console.log('Products loaded:', productsData.length);
                
                // Populate all existing product selects
                populateAllProductSelects();
            } else {
                console.error('Error loading products:', data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching products:', error);
        });
    }
    
    // Function to populate a product select element
    function populateProductSelect(selectElement) {
        // Keep the first option (placeholder)
        const firstOption = selectElement.options[0];
        selectElement.innerHTML = '';
        selectElement.appendChild(firstOption);
        
        // Add product options
        productsData.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = product.name;
            option.setAttribute('data-price', product.price);
            option.setAttribute('data-stock', product.quantity);
            selectElement.appendChild(option);
        });
    }
    
    // Function to populate all product selects
    function populateAllProductSelects() {
        const productSelects = document.querySelectorAll('.product-select');
        productSelects.forEach(select => {
            populateProductSelect(select);
        });
    }
    
    // Fetch products on page load
    fetchProducts();
    
    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Function to show alert/notification
    function showAlert(message, type = 'success') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '9999';
        alertDiv.style.minWidth = '300px';
        
        // Add message and close button
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add to document
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 3000);
    }

    // Set default date to today for the date input
    const today = new Date().toISOString().split('T')[0];
    if (document.getElementById('purchaseOrderDate')) {
        document.getElementById('purchaseOrderDate').value = today;
    }

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const table = document.getElementById('purchaseOrdersTable');
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const cells = row.getElementsByTagName('td');
                if (cells.length > 0) {
                    const orderNumberCell = cells[1].textContent.toLowerCase();
                    const supplierCell = cells[2].textContent.toLowerCase();
                    const dateCell = cells[3].textContent.toLowerCase();
                    
                    if (orderNumberCell.includes(searchValue) || 
                        supplierCell.includes(searchValue) || 
                        dateCell.includes(searchValue)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            }
        });
    }

    // Filter functionality
    const filterLinks = document.querySelectorAll('[data-filter]');
    filterLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const filter = this.getAttribute('data-filter');
            
            const table = document.getElementById('purchaseOrdersTable');
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const cells = row.getElementsByTagName('td');
                if (cells.length > 0) {
                    const statusCell = cells[5].textContent.toLowerCase();
                    
                    if (filter === 'all') {
                        row.style.display = '';
                    } else if (filter === 'received' && statusCell.includes('مستلم')) {
                        row.style.display = '';
                    } else if (filter === 'pending' && statusCell.includes('قيد الانتظار')) {
                        row.style.display = '';
                    } else if (filter === 'cancelled' && statusCell.includes('ملغي')) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            }
        });
    });

    // View purchase order details
    const viewPurchaseOrderButtons = document.querySelectorAll('.view-purchase-order');
    viewPurchaseOrderButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const orderId = this.getAttribute('data-id');
            
            // Show loading state
            document.querySelector('.purchase-order-number').textContent = 'جاري التحميل...';
            document.querySelector('.purchase-order-date').textContent = 'جاري التحميل...';
            document.querySelector('.purchase-order-supplier-name').textContent = 'جاري التحميل...';
            document.querySelector('.purchase-order-items').innerHTML = '<tr><td colspan="5" class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></td></tr>';
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('purchaseOrderDetailsModal'));
            modal.show();
            
            // Fetch purchase order details via AJAX
            fetch(`/api/purchase-orders/${orderId}/details/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const purchaseOrder = data.purchase_order;
                    
                    // Update purchase order details
                    document.querySelector('.purchase-order-number').textContent = purchaseOrder.reference_number || `PO-${purchaseOrder.id}`;
                    document.querySelector('.purchase-order-date').textContent = purchaseOrder.date;
                    document.querySelector('.purchase-order-status').innerHTML = getStatusBadge(purchaseOrder.status);
                    document.querySelector('.purchase-order-supplier-name').textContent = purchaseOrder.supplier_name;
                    document.querySelector('.purchase-order-contact-person').textContent = purchaseOrder.supplier_contact_person || '--';
                    document.querySelector('.purchase-order-supplier-phone').textContent = purchaseOrder.supplier_phone || '--';
                    
                    // Update purchase order items
                    let itemsHtml = '';
                    if (purchaseOrder.items && purchaseOrder.items.length > 0) {
                        purchaseOrder.items.forEach((item, index) => {
                            itemsHtml += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${item.product_name || ''}</td>
                    <td>${item.quantity || 0}</td>
                    <td>${(item.price || 0).toFixed(2)} ج.م</td>
                    <td>${(item.total || 0).toFixed(2)} ج.م</td>
                </tr>
            `;
                        });
                    } else {
                        itemsHtml = `
                            <tr>
                                <td colspan="5" class="text-center py-4">
                                    <span class="text-muted">لا توجد منتجات متاحة</span>
                                </td>
                            </tr>
                        `;
                    }
                    document.querySelector('.purchase-order-items').innerHTML = itemsHtml;
                    
                    // Update totals
                    document.querySelector('.purchase-order-subtotal').textContent = `${(purchaseOrder.subtotal || 0).toFixed(2)} ج.م`;
                    document.querySelector('.purchase-order-discount').textContent = `${(purchaseOrder.discount || 0).toFixed(2)} ج.م`;
                    document.querySelector('.purchase-order-total').textContent = `${(purchaseOrder.total || 0).toFixed(2)} ج.م`;
                    
                    // Update notes
                    document.querySelector('.purchase-order-notes').textContent = purchaseOrder.notes || 'لا توجد ملاحظات متاحة';
                    
                    // Set purchase order ID for edit and print buttons
                    document.querySelector('.edit-purchase-order-btn').setAttribute('data-id', purchaseOrder.id);
                    document.querySelector('.print-purchase-order-btn').setAttribute('data-id', purchaseOrder.id);
                } else {
                    showAlert('حدث خطأ أثناء تحميل بيانات طلب الشراء', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('حدث خطأ أثناء الاتصال بالخادم', 'danger');
            });
        });
    });

    // Helper function to get status badge HTML
    function getStatusBadge(status) {
        switch (status) {
            case 'received':
                return '<span class="badge bg-success">مستلم</span>';
            case 'pending':
                return '<span class="badge bg-warning text-dark">قيد الانتظار</span>';
            case 'cancelled':
                return '<span class="badge bg-danger">ملغي</span>';
            default:
                return '<span class="badge bg-secondary">مسودة</span>';
        }
    }

    // Edit purchase order
    const editPurchaseOrderButtons = document.querySelectorAll('.edit-purchase-order');
    editPurchaseOrderButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const orderId = this.getAttribute('data-id');
            
            // Clear previous items
            const purchaseOrderItemsTableBody = document.querySelector('#purchaseOrderItemsTable tbody');
            purchaseOrderItemsTableBody.innerHTML = '<tr><td colspan="5" class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></td></tr>';
            
            // Change modal title
            document.getElementById('addPurchaseOrderModalLabel').textContent = 'تعديل طلب الشراء';
            
            // Add hidden input for purchase order ID
            let orderIdInput = document.getElementById('editPurchaseOrderId');
            if (!orderIdInput) {
                orderIdInput = document.createElement('input');
                orderIdInput.type = 'hidden';
                orderIdInput.id = 'editPurchaseOrderId';
                document.getElementById('addPurchaseOrderForm').appendChild(orderIdInput);
            }
            orderIdInput.value = orderId;
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('addPurchaseOrderModal'));
            modal.show();
            
            // Fetch purchase order details via AJAX
            fetch(`/api/purchase-orders/${orderId}/details/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const purchaseOrder = data.purchase_order;
                    
                    // Populate form fields
                    document.getElementById('purchaseOrderDate').value = purchaseOrder.date;
                    document.getElementById('supplierSelect').value = purchaseOrder.supplier_id;
                    document.getElementById('purchaseOrderNotes').value = purchaseOrder.notes || '';
                    document.getElementById('purchaseOrderDiscount').value = purchaseOrder.discount || 0;
                    
                    // Clear previous items
                    purchaseOrderItemsTableBody.innerHTML = '';
                    
                    // Add purchase order items
                    if (purchaseOrder.items && purchaseOrder.items.length > 0) {
                        purchaseOrder.items.forEach(item => {
                            // Add a new row for each item
                            const newRow = document.createElement('tr');
                            
                            // Create the product select element
                            const productSelectHtml = `
                                <div class="input-group">
                                    <select class="form-select product-select" required>
                                        <option value="">اختر المنتج</option>
                                    </select>
                                    <button class="btn btn-outline-primary add-new-product-btn" type="button">
                                        <i class="fas fa-plus"></i>
                                    </button>
                                </div>
                            `;
                            
                            newRow.innerHTML = `
                                <td>${productSelectHtml}</td>
                                <td>
                                    <input type="number" class="form-control item-quantity" min="1" value="${item.quantity}" required>
                                </td>
                                <td>
                                    <input type="number" class="form-control item-price" min="0" step="0.01" value="${(item.price || 0).toFixed(2)}" required>
                                </td>
                                <td>
                                    <input type="number" class="form-control item-total" min="0" step="0.01" value="${(item.total || 0).toFixed(2)}" readonly>
                                </td>
                                <td>
                                    <button type="button" class="btn btn-sm btn-danger remove-item">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </td>
                            `;
                            purchaseOrderItemsTableBody.appendChild(newRow);
                            
                            // Set the selected product
                            const productSelect = newRow.querySelector('.product-select');
                            
                            // First populate the product select
                            populateProductSelect(productSelect);
                            
                            // Use MutationObserver to detect when options are added to the select
                            const observer = new MutationObserver((mutations) => {
                                console.log('Product select options changed:', productSelect.options.length);
                                
                                // Try to select the product
                                if (productSelect.options.length > 1) {
                                    console.log('Trying to select product ID:', item.product_id);
                                    
                                    // Find and select the option
                                    for (let i = 0; i < productSelect.options.length; i++) {
                                        if (productSelect.options[i].value == item.product_id) {
                                            console.log('Found matching option at index:', i);
                                            productSelect.selectedIndex = i;
                                            
                                            // Trigger change event to update price
                                            const event = new Event('change');
                                            productSelect.dispatchEvent(event);
                                            
                                            // Disconnect the observer once we've found the option
                                            observer.disconnect();
                                            break;
                                        }
                                    }
                                }
                            });
                            
                            // Observe changes to the select element
                            observer.observe(productSelect, { childList: true });
                            
                            // Also try immediately in case options are already loaded
                            if (productSelect.options.length > 1) {
                                for (let i = 0; i < productSelect.options.length; i++) {
                                    if (productSelect.options[i].value == item.product_id) {
                                        productSelect.selectedIndex = i;
                                        
                                        // Trigger change event to update price
                                        const event = new Event('change');
                                        productSelect.dispatchEvent(event);
                                        break;
                                    }
                                }
                            }
                            
                            // Setup event listeners for the new row
                            setupItemEventListeners(newRow);
                        });
                    } else {
                        // Add an empty row if no items
                        const newRow = document.createElement('tr');
                        newRow.innerHTML = `
                            <td>${productSelectHtml}</td>
                            <td>
                                <input type="number" class="form-control item-quantity" min="1" value="1" required>
                            </td>
                            <td>
                                <input type="number" class="form-control item-price" min="0" step="0.01" value="0.00" required>
                            </td>
                            <td>
                                <input type="number" class="form-control item-total" min="0" step="0.01" value="0.00" readonly>
                            </td>
                            <td>
                                <button type="button" class="btn btn-sm btn-danger remove-item">
                                    <i class="fas fa-times"></i>
                                </button>
                            </td>
                        `;
                        purchaseOrderItemsTableBody.appendChild(newRow);
                        
                        console.log('Adding empty row with product select');
                        
                        // Setup event listeners for the new row
                        setupItemEventListeners(newRow);
                    }
                    
                    // Update totals
                    updateOrderTotals();
                    
                    // Change save button text
                    document.getElementById('savePurchaseOrderBtn').textContent = 'تحديث الطلب';
                } else {
                    showAlert('حدث خطأ أثناء تحميل بيانات طلب الشراء', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('حدث خطأ أثناء الاتصال بالخادم', 'danger');
            });
        });
    });

    // Print purchase order
    const printPurchaseOrderButtons = document.querySelectorAll('.print-purchase-order');
    printPurchaseOrderButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const orderId = this.getAttribute('data-id');
            showAlert('جاري طباعة طلب الشراء رقم ' + orderId + '...');
        });
    });

    // Delete purchase order
    const deletePurchaseOrderButtons = document.querySelectorAll('.delete-purchase-order');
    deletePurchaseOrderButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const orderId = this.getAttribute('data-id');
            const modal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'));
            modal.show();
            
            // Set up the confirm delete button
            document.getElementById('confirmDeleteBtn').setAttribute('data-id', orderId);
        });
    });

    // Confirm delete
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            const orderId = this.getAttribute('data-id');
            
            // Show loading state
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جاري الحذف...';
            
            // Send AJAX request to delete purchase order
            fetch(`/api/purchase-orders/${orderId}/delete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmationModal'));
                modal.hide();
                
                if (data.success) {
                    // Show success message
                    showAlert('تم حذف طلب الشراء بنجاح');
                    
                    // Remove the purchase order row from the table
                    const orderRow = document.querySelector(`.delete-purchase-order[data-id="${orderId}"]`).closest('tr');
                    if (orderRow) {
                        orderRow.remove();
                    }
                    
                    // Reload the page if no purchase orders left
                    const remainingRows = document.querySelectorAll('#purchaseOrdersTable tbody tr').length;
                    if (remainingRows === 0) {
                        window.location.reload();
                    }
                } else {
                    showAlert(data.message || 'حدث خطأ أثناء حذف طلب الشراء', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('حدث خطأ أثناء الاتصال بالخادم', 'danger');
            })
            .finally(() => {
                // Reset button state
                this.disabled = false;
                this.innerHTML = 'حذف';
            });
        });
    }

    // Save purchase order
    const savePurchaseOrderBtn = document.getElementById('savePurchaseOrderBtn');
    if (savePurchaseOrderBtn) {
        savePurchaseOrderBtn.addEventListener('click', function() {
            const form = document.getElementById('addPurchaseOrderForm');
            if (form.checkValidity()) {
                // Show loading state
                this.disabled = true;
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جاري الحفظ...';
                
                // Get form data
                const orderDate = document.getElementById('purchaseOrderDate').value;
                const supplierId = document.getElementById('supplierSelect').value;
                const notes = document.getElementById('purchaseOrderNotes').value;
                const subtotal = parseFloat(document.getElementById('purchaseOrderSubtotal').value);
                const discount = parseFloat(document.getElementById('purchaseOrderDiscount').value);
                const total = parseFloat(document.getElementById('purchaseOrderTotal').value);
                
                // Get order items
                const items = [];
                const rows = document.querySelectorAll('#purchaseOrderItemsTable tbody tr');
                
                let isValid = true;
                rows.forEach((row, index) => {
                    const productSelect = row.querySelector('.product-select');
                    const productId = productSelect.value;
                    
                    if (!productId || productId === 'new') {
                        showAlert(`يرجى اختيار منتج للصف رقم ${index + 1}`, 'warning');
                        isValid = false;
                        return;
                    }
                    
                    const productName = productSelect.options[productSelect.selectedIndex].text;
                    const quantity = parseInt(row.querySelector('.item-quantity').value, 10);
                    const price = parseFloat(row.querySelector('.item-price').value);
                    const itemTotal = parseFloat(row.querySelector('.item-total').value);
                    
                    // Skip empty rows or rows with zero quantity
                    if (quantity <= 0) {
                        showAlert(`الكمية يجب أن تكون أكبر من صفر للصف رقم ${index + 1}`, 'warning');
                        isValid = false;
                        return;
                    }
                    
                    // Log each item for debugging
                    console.log('Processing item:', {
                        product_id: parseInt(productId, 10),
                        product_name: productName,
                        quantity: quantity,
                        price: price,
                        total: itemTotal
                    });
                    
                    items.push({
                        product_id: parseInt(productId, 10), // Convert to integer
                        product_name: productName,
                        quantity: quantity,
                        price: price,
                        total: itemTotal
                    });
                });
                
                // Check if supplier is selected
                if (!supplierId) {
                    showAlert('يرجى اختيار مورد', 'warning');
                    this.disabled = false;
                    this.innerHTML = 'حفظ الطلب';
                    return;
                }
                
                if (!isValid) {
                    this.disabled = false;
                    this.innerHTML = 'حفظ الطلب';
                    return;
                }
                
                if (items.length === 0) {
                    showAlert('يجب إضافة منتج واحد على الأقل إلى الطلب', 'warning');
                    console.error('خطأ: لا يوجد منتجات مضافة إلى الطلب');
                    this.disabled = false;
                    this.innerHTML = 'حفظ الطلب';
                    return;
                }
                
                // Create purchase order data object
                const purchaseOrderData = {
                    supplier_id: parseInt(supplierId, 10), // Convert to integer
                    notes: notes,
                    status: 'pending', // Default status
                    discount: discount, // Send as number
                    // Ensure items array is properly formatted
                    items: items.length > 0 ? items.map(item => {
                        console.log('Processing item:', item);
                        return {
                            product_id: parseInt(item.product_id, 10), // Convert to integer
                            quantity: parseInt(item.quantity, 10), // Convert to integer
                            price: parseFloat(item.price) // Convert to float
                        };
                    }) : []
                };

                // Add order_date if needed
                if (orderDate) {
                    // Ensure date is in YYYY-MM-DD format
                    const formattedDate = new Date(orderDate).toISOString().split('T')[0];
                    purchaseOrderData.date = formattedDate;
                    console.log('Formatted order date:', formattedDate);
                }
                
                // Log the data being sent for debugging
                console.log('Sending purchase order data:', purchaseOrderData);
                
                // Get and log CSRF token
                const csrfToken = getCookie('csrftoken');
                console.log('CSRF Token:', csrfToken);
                
                // Check if we're editing an existing purchase order or creating a new one
                const editPurchaseOrderId = document.getElementById('editPurchaseOrderId')?.value;
                let apiUrl;
                let method;
                
                if (editPurchaseOrderId) {
                    // We're updating an existing purchase order
                    apiUrl = window.location.origin + `/api/purchase-orders/${editPurchaseOrderId}/update/`;
                    method = 'POST';
                    console.log('Updating existing purchase order:', editPurchaseOrderId);
                } else {
                    // We're creating a new purchase order
                    apiUrl = window.location.origin + '/api/purchase-orders/create/';
                    method = 'POST';
                    console.log('Creating new purchase order');
                }
                
                console.log('API URL:', apiUrl);
                
                fetch(apiUrl, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken, // Include CSRF token
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(purchaseOrderData)
                })
                .then(response => {
                    console.log('Response status:', response.status);
                    console.log('Response headers:', response.headers);
                    
                    if (!response.ok) {
                        return response.json().then(errorData => {
                            console.error('Server error response:', errorData);
                            throw new Error(errorData.message || 'Server error');
                        });
                    }
                    
                    return response.json().catch(error => {
                        console.error('Error parsing JSON:', error);
                        throw new Error('Invalid JSON response');
                    });
                })
                .then(data => {
                    console.log('Success response:', data);
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addPurchaseOrderModal'));
                    modal.hide();
                    
                    // Show success message
                    showAlert('تم حفظ طلب الشراء بنجاح');
                    
                    // Reload the page to show the new purchase order
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Error:', error);
                    
                    // Show more detailed error message
                    let errorMessage = 'حدث خطأ أثناء الاتصال بالخادم';
                    if (error.message) {
                        errorMessage += ': ' + error.message;
                    }
                    
                    showAlert(errorMessage, 'danger');
                })
                .finally(() => {
                    // Reset button state
                    this.disabled = false;
                    this.innerHTML = 'حفظ الطلب';
                });
            } else {
                form.reportValidity();
            }
        });
    }

    // Edit purchase order button in details modal
    const editPurchaseOrderBtn = document.querySelector('.edit-purchase-order-btn');
    if (editPurchaseOrderBtn) {
        editPurchaseOrderBtn.addEventListener('click', function() {
            const orderId = this.getAttribute('data-id');
            if (!orderId) {
                showAlert('لم يتم العثور على معرف طلب الشراء', 'warning');
                return;
            }
            
            // Close the details modal
            const detailsModal = bootstrap.Modal.getInstance(document.getElementById('purchaseOrderDetailsModal'));
            detailsModal.hide();
            
            // Find the edit button for this purchase order and click it
            const editButton = document.querySelector(`.edit-purchase-order[data-id="${orderId}"]`);
            if (editButton) {
                editButton.click();
            } else {
                // If we can't find the button, we'll manually trigger the edit process
                // This is a fallback and should not normally be needed
                showAlert('لم يتم العثور على زر التعديل، يرجى تحديث الصفحة والمحاولة مرة أخرى', 'warning');
            }
        });
    }

    // Print purchase order button
    const printPurchaseOrderBtn = document.querySelector('.print-purchase-order-btn');
    if (printPurchaseOrderBtn) {
        printPurchaseOrderBtn.addEventListener('click', function() {
            showAlert('جاري طباعة طلب الشراء...');
        });
    }

    // Add New Supplier Button
    const addNewSupplierBtn = document.getElementById('addNewSupplierBtn');
    if (addNewSupplierBtn) {
        addNewSupplierBtn.addEventListener('click', function() {
            // Show the supplier modal
            const modal = new bootstrap.Modal(document.getElementById('addNewSupplierModal'));
            modal.show();
        });
    }

    // Handle save new supplier button click
    const saveNewSupplierBtn = document.getElementById('saveNewSupplierBtn');
    if (saveNewSupplierBtn) {
        saveNewSupplierBtn.addEventListener('click', function() {
            const form = document.getElementById('newSupplierForm');
            if (form.checkValidity()) {
                // Show loading state
                this.disabled = true;
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جاري الحفظ...';
                
                // Get form data
                const supplierData = {
                    name: document.getElementById('newSupplierName').value,
                    contact_person: document.getElementById('newSupplierContactPerson').value || '',
                    phone: document.getElementById('newSupplierPhone').value || '',
                    email: document.getElementById('newSupplierEmail').value || '',
                    address: document.getElementById('newSupplierAddress').value || ''
                };
                
                // Log the data being sent
                console.log('Sending supplier data:', supplierData);
                
                // Send AJAX request to save the supplier
                fetch('/api/suppliers/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(supplierData)
                })
                .then(response => {
                    console.log('Response status:', response.status);
                    // Clone the response so we can log it and still use it
                    const responseClone = response.clone();
                    responseClone.text().then(text => {
                        console.log('Response body:', text);
                    });
                    
                    // Check if response is ok (status in the range 200-299)
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    
                    // Try to parse as JSON, but handle errors
                    return response.text().then(text => {
                        try {
                            return JSON.parse(text);
                        } catch (e) {
                            console.error('Error parsing JSON:', e);
                            console.error('Response text:', text);
                            throw new Error('Invalid JSON response from server');
                        }
                    });
                })
                .then(data => {
                    if (data.success) {
                        // Close the modal
                        const modal = bootstrap.Modal.getInstance(document.getElementById('addNewSupplierModal'));
                        modal.hide();
                        
                        // Add the new supplier to the supplier select dropdown
                        const supplierSelect = document.getElementById('supplierSelect');
                        const option = document.createElement('option');
                        option.value = data.supplier.id;
                        option.textContent = data.supplier.name;
                        supplierSelect.appendChild(option);
                        
                        // Select the new supplier
                        supplierSelect.value = data.supplier.id;
                        
                        // Show success message
                        showAlert('تم إضافة المورد بنجاح');
                    } else {
                        // Show error
                        showAlert('حدث خطأ أثناء حفظ المورد: ' + (data.error || 'خطأ غير معروف'), 'danger');
                        
                        // Reset button state
                        const saveBtn = document.getElementById('saveNewSupplierBtn');
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = 'حفظ';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('حدث خطأ أثناء حفظ المورد', 'danger');
                    
                    // Reset button state
                    const saveBtn = document.getElementById('saveNewSupplierBtn');
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = 'حفظ';
                });
            } else {
                // Trigger form validation
                form.reportValidity();
            }
        });
    }

    // Add New Product Button
    document.querySelectorAll('.add-new-product-btn').forEach(button => {
        button.addEventListener('click', function() {
            // Create a modal for adding a new product
            const modalHtml = `
                <div class="modal fade" id="addNewProductModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">إضافة منتج جديد</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <form id="newProductForm">
                                    <div class="mb-3">
                                        <label for="newProductName" class="form-label">اسم المنتج <span class="text-danger">*</span></label>
                                        <input type="text" class="form-control" id="newProductName" required>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label for="newProductPrice" class="form-label">سعر البيع <span class="text-danger">*</span></label>
                                                <input type="number" class="form-control" id="newProductPrice" step="0.01" min="0" required>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label for="newProductCostPrice" class="form-label">سعر التكلفة <span class="text-danger">*</span></label>
                                                <input type="number" class="form-control" id="newProductCostPrice" step="0.01" min="0" required>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="mb-3">
                                        <label for="newProductQuantity" class="form-label">الكمية المتوفرة <span class="text-danger">*</span></label>
                                        <input type="number" class="form-control" id="newProductQuantity" min="0" value="0" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="newProductDescription" class="form-label">الوصف</label>
                                        <textarea class="form-control" id="newProductDescription" rows="2"></textarea>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                                <button type="button" class="btn btn-primary" id="saveNewProductBtn">حفظ</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Add modal to the document
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer);
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('addNewProductModal'));
            modal.show();
            
            // Get the current row
            const currentRow = this.closest('tr');
            
            // Handle save button click
            document.getElementById('saveNewProductBtn').addEventListener('click', function() {
                const form = document.getElementById('newProductForm');
                if (form.checkValidity()) {
                    // Show loading state
                    this.disabled = true;
                    this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> جاري الحفظ...';
                    
                    // Get form data
                    const productData = {
                        name: document.getElementById('newProductName').value,
                        price: parseFloat(document.getElementById('newProductPrice').value),
                        cost_price: parseFloat(document.getElementById('newProductCostPrice').value),
                        quantity: parseInt(document.getElementById('newProductQuantity').value, 10),
                        description: document.getElementById('newProductDescription').value,
                        // Add required fields with default values
                        sku: 'SKU-' + Math.floor(Math.random() * 10000), // Generate a random SKU
                        reorder_level: 10
                    };
                    
                    // Log the data being sent
                    console.log('Sending product data:', productData);
                    
                    // Send AJAX request to save the product
                    fetch('/api/products/create/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken'),
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify(productData)
                    })
                    .then(response => {
                        console.log('Response status:', response.status);
                        // Clone the response so we can log it and still use it
                        const responseClone = response.clone();
                        responseClone.text().then(text => {
                            console.log('Response body:', text);
                        });
                        
                        // Check if response is ok (status in the range 200-299)
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        
                        // Try to parse as JSON, but handle errors
                        return response.text().then(text => {
                            try {
                                return JSON.parse(text);
                            } catch (e) {
                                console.error('Error parsing JSON:', e);
                                console.error('Response text:', text);
                                throw new Error('Invalid JSON response from server');
                            }
                        });
                    })
                    .then(data => {
                        if (data.success) {
                            // Close the modal
                            const modal = bootstrap.Modal.getInstance(document.getElementById('addNewProductModal'));
                            modal.hide();
                            
                            // Add the new product to all product select dropdowns
                            const productSelects = document.querySelectorAll('.product-select');
                            productSelects.forEach(select => {
                                const option = document.createElement('option');
                                option.value = data.product_id;
                                option.textContent = productData.name;
                                option.setAttribute('data-price', productData.price);
                                option.setAttribute('data-stock', productData.quantity);
                                select.appendChild(option);
                                
                                // If this is the current row's select, select the new product
                                if (select === currentRow.querySelector('.product-select')) {
                                    select.value = data.product_id;
                                    // Trigger change event to update price
                                    const event = new Event('change');
                                    select.dispatchEvent(event);
                                }
                            });
                            
                            // Show success message
                            showAlert('تم إضافة المنتج بنجاح');
                            
                            // Remove the modal from DOM after hiding
                            document.getElementById('addNewProductModal').addEventListener('hidden.bs.modal', function() {
                                this.remove();
                            });
                        } else {
                            // Show error
                            showAlert('حدث خطأ أثناء حفظ المنتج: ' + (data.error || 'خطأ غير معروف'), 'danger');
                            
                            // Reset button state
                            const saveBtn = document.getElementById('saveNewProductBtn');
                            saveBtn.disabled = false;
                            saveBtn.innerHTML = 'حفظ';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showAlert('حدث خطأ أثناء حفظ المنتج', 'danger');
                        
                        // Reset button state
                        const saveBtn = document.getElementById('saveNewProductBtn');
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = 'حفظ';
                    });
                } else {
                    // Trigger form validation
                    form.reportValidity();
                }
            });
        });
    });

    // Add item button
    const addItemBtn = document.getElementById('addItemBtn');
    if (addItemBtn) {
        addItemBtn.addEventListener('click', function() {
            const tbody = document.querySelector('#purchaseOrderItemsTable tbody');
            const newRow = document.createElement('tr');
            
            // Create the product select element
            const productSelectHtml = `
                <div class="input-group">
                    <select class="form-select product-select" required>
                        <option value="">اختر المنتج</option>
                    </select>
                    <button class="btn btn-outline-primary add-new-product-btn" type="button">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            `;
            
            newRow.innerHTML = `
                <td>${productSelectHtml}</td>
                <td>
                    <input type="number" class="form-control item-quantity" min="1" value="1" required>
                </td>
                <td>
                    <input type="number" class="form-control item-price" min="0" step="0.01" value="0.00" required>
                </td>
                <td>
                    <input type="number" class="form-control item-total" min="0" step="0.01" value="0.00" readonly>
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger remove-item">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(newRow);
            
            // Set up event listeners for the new row
            setupItemEventListeners(newRow);
            
            // Update totals
            updateOrderTotals();
        });
    }

    // Setup item event listeners
    function setupItemEventListeners(row) {
        const productSelect = row.querySelector('.product-select');
        const quantityInput = row.querySelector('.item-quantity');
        const priceInput = row.querySelector('.item-price');
        const totalInput = row.querySelector('.item-total');
        const removeButton = row.querySelector('.remove-item');
        
        // Populate the product select with available products
        populateProductSelect(productSelect);
        
        // Product select change
        productSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const price = selectedOption.getAttribute('data-price') || 0;
            
            // Set price
            priceInput.value = parseFloat(price).toFixed(2);
            
            updateItemTotal(row);
            updateOrderTotals();
        });
        
        // Quantity change
        quantityInput.addEventListener('input', function() {
            updateItemTotal(row);
            updateOrderTotals();
        });
        
        // Price change
        priceInput.addEventListener('input', function() {
            updateItemTotal(row);
            updateOrderTotals();
        });
        
        // Remove item
        removeButton.addEventListener('click', function() {
            row.remove();
            updateOrderTotals();
        });
    }

    // Update item total
    function updateItemTotal(row) {
        const quantity = parseFloat(row.querySelector('.item-quantity').value) || 0;
        const price = parseFloat(row.querySelector('.item-price').value) || 0;
        const total = quantity * price;
        row.querySelector('.item-total').value = total.toFixed(2);
    }

    // Update order totals
    function updateOrderTotals() {
        const itemTotals = document.querySelectorAll('.item-total');
        let subtotal = 0;
        
        itemTotals.forEach(item => {
            subtotal += parseFloat(item.value) || 0;
        });
        
        const discount = parseFloat(document.getElementById('purchaseOrderDiscount').value) || 0;
        const total = subtotal - discount;
        
        document.getElementById('purchaseOrderSubtotal').value = subtotal.toFixed(2);
        document.getElementById('purchaseOrderTotal').value = total.toFixed(2);
    }

    // Discount change
    const purchaseOrderDiscount = document.getElementById('purchaseOrderDiscount');
    if (purchaseOrderDiscount) {
        purchaseOrderDiscount.addEventListener('input', updateOrderTotals);
    }

    // Setup initial event listeners for the first row
    const firstRow = document.querySelector('#purchaseOrderItemsTable tbody tr');
    if (firstRow) {
        setupItemEventListeners(firstRow);
    }
});
