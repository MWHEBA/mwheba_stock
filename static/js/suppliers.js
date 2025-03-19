/**
 * JavaScript functions for suppliers management
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize event handlers
    initViewSupplierBtns();
    initEditSupplierBtns();
    initAddSupplierForm();
    initDeleteSupplierModal();
    initShowEntriesSelect();
});

/**
 * Initialize view supplier buttons
 */
function initViewSupplierBtns() {
    const viewSupplierBtns = document.querySelectorAll('.view-supplier-btn');
    viewSupplierBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const supplierId = this.getAttribute('data-id');
            const modal = document.getElementById('viewSupplierModal');
            const modalContent = modal.querySelector('.modal-content');

            // Show loading spinner
            modalContent.innerHTML = `
                <div class="d-flex justify-content-center p-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">جاري التحميل...</span>
                    </div>
                </div>
            `;

            // Open modal
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();

            // Fetch supplier details
            fetch(`/suppliers/${supplierId}/modal-detail/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    modalContent.innerHTML = html;

                    // Setup payment button if exists
                    const recordPaymentBtn = modalContent.querySelector('#recordPaymentBtn');
                    if (recordPaymentBtn) {
                        recordPaymentBtn.addEventListener('click', function() {
                            const supplierId = this.getAttribute('data-id');
                            // Close current modal
                            modalInstance.hide();
                            
                            // Show payment modal
                            setTimeout(() => {
                                loadModalContent(`/suppliers/${supplierId}/payment-form/`, 'recordPaymentModal');
                            }, 500);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    modalContent.innerHTML = `
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title"><i class="fas fa-exclamation-triangle me-2"></i> خطأ</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="text-center">
                                <i class="fas fa-times-circle fa-4x text-danger mb-3"></i>
                                <h5>حدث خطأ أثناء تحميل بيانات المورد</h5>
                                <p>يرجى المحاولة مرة أخرى لاحقاً</p>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إغلاق</button>
                        </div>
                    `;
                });
        });
    });
}

/**
 * Initialize edit supplier buttons
 */
function initEditSupplierBtns() {
    const editSupplierBtns = document.querySelectorAll('.edit-supplier-btn');
    editSupplierBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const supplierId = this.getAttribute('data-id');
            const modal = document.getElementById('editSupplierModal');
            const modalBody = modal.querySelector('.modal-body');

            // Show loading spinner
            modalBody.innerHTML = `
                <div class="d-flex justify-content-center my-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">جاري التحميل...</span>
                    </div>
                </div>
            `;

            // Open modal
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();

            // Fetch supplier edit form
            fetch(`/suppliers/${supplierId}/modal-edit/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    modalBody.innerHTML = html;
                    
                    // Set up form submission
                    const updateBtn = document.getElementById('updateSupplierBtn');
                    const form = document.getElementById('editSupplierForm');
                    
                    if (updateBtn && form) {
                        updateBtn.addEventListener('click', function() {
                            submitSupplierForm(form, modalInstance);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('حدث خطأ أثناء تحميل نموذج تعديل المورد', 'error');
                });
        });
    });
}

/**
 * Initialize add supplier form
 */
function initAddSupplierForm() {
    const addSupplierForm = document.getElementById('addSupplierForm');
    const saveSupplierBtn = document.getElementById('saveSupplierBtn');
    
    if (addSupplierForm && saveSupplierBtn) {
        saveSupplierBtn.addEventListener('click', function() {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addSupplierModal'));
            submitSupplierForm(addSupplierForm, modal);
        });
    }
}

/**
 * Initialize delete supplier modal
 */
function initDeleteSupplierModal() {
    const deleteSupplierModal = document.getElementById('deleteSupplierModal');
    if (deleteSupplierModal) {
        deleteSupplierModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const supplierId = button.getAttribute('data-id');
            const supplierName = button.getAttribute('data-name');
            
            const supplierNameSpan = deleteSupplierModal.querySelector('#supplierNameToDelete');
            const supplierIdInput = deleteSupplierModal.querySelector('#supplierIdToDelete');
            
            if (supplierNameSpan) supplierNameSpan.textContent = supplierName;
            if (supplierIdInput) supplierIdInput.value = supplierId;
        });
        
        const confirmDeleteBtn = document.getElementById('confirmDeleteSupplier');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', function() {
                const deleteForm = document.getElementById('deleteSupplierForm');
                if (deleteForm) {
                    const supplierId = deleteForm.querySelector('#supplierIdToDelete').value;
                    
                    fetch(`/suppliers/${supplierId}/delete/`, {
                        method: 'POST',
                        body: new FormData(deleteForm),
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Close modal
                            const modal = bootstrap.Modal.getInstance(deleteSupplierModal);
                            modal.hide();
                            
                            // Show success message and reload page
                            showToast('تم حذف المورد بنجاح', 'success');
                            setTimeout(() => {
                                window.location.reload();
                            }, 1000);
                        } else {
                            // Show error message
                            showToast(data.message || 'فشلت عملية الحذف', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showToast('حدث خطأ أثناء محاولة حذف المورد', 'error');
                    });
                }
            });
        }
    }
}

/**
 * Initialize show entries select
 */
function initShowEntriesSelect() {
    const showEntriesSelect = document.getElementById('show-entries');
    if (showEntriesSelect) {
        showEntriesSelect.addEventListener('change', function() {
            const pageSize = this.value;
            const url = new URL(window.location.href);
            url.searchParams.set('page_size', pageSize);
            window.location.href = url.toString();
        });
    }
}

/**
 * Submit supplier form via AJAX
 */
function submitSupplierForm(form, modalInstance) {
    // تأكد من أن النموذج يحتوي على توكن CSRF صالح
    const submitBtn = form.querySelector('button[type="submit"]') || document.getElementById('saveSupplierBtn') || document.getElementById('updateSupplierBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> جاري الحفظ...';
    }
    
    const formData = new FormData(form);
    
    // أضف رقمًا عشوائيًا لمنع التخزين المؤقت
    const timestamp = new Date().getTime();
    const url = form.action.includes('?') ? 
        `${form.action}&_=${timestamp}` : 
        `${form.action}?_=${timestamp}`;
    
    // تأكد من وجود توكن CSRF في الرأس
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            // معالجة استجابات الخطأ
            if (response.status === 401 || response.status === 403) {
                throw new Error('جلسة غير صالحة. يرجى تحديث الصفحة');
            }
            throw new Error(`خطأ في الخادم: ${response.status}`);
        }
        
        // تحقق من نوع المحتوى
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        }
        
        // إذا لم يكن JSON، حاول تشخيص المشكلة
        return response.text().then(text => {
            console.error('استجابة غير متوقعة:', text.substring(0, 200));
            throw new Error('استجابة غير صالحة من الخادم');
        });
    })
    .then(data => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> حفظ';
        }
        
        if (data.success) {
            showToast('تم حفظ بيانات المورد بنجاح', 'success');
            if (modalInstance) modalInstance.hide();
            setTimeout(() => window.location.reload(), 1000);
        } else {
            // إظهار أخطاء التحقق
            if (data.errors) {
                // عرض الأخطاء على الحقول
                Object.keys(data.errors).forEach(field => {
                    const inputEl = document.getElementById(`id_${field}`);
                    if (inputEl) {
                        inputEl.classList.add('is-invalid');
                        const feedback = document.createElement('div');
                        feedback.className = 'invalid-feedback';
                        feedback.textContent = data.errors[field];
                        inputEl.parentNode.appendChild(feedback);
                    }
                });
            }
            
            if (data.message) {
                showToast(data.message, 'error');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> حفظ';
        }
        
        showToast(error.message || 'حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى', 'error');
    });
}

/**
 * Display toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of toast (success, error, warning, info)
 */
function showToast(message, type) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        // Create toast container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    const toastInstance = new bootstrap.Toast(toast, { delay: 5000 });
    toastInstance.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Helper function to load modal content
 * @param {string} url - The URL to fetch content from
 * @param {string} modalId - The ID of the modal to load content into
 */
function loadModalContent(url, modalId) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            const modal = document.getElementById(modalId);
            const modalBody = modal.querySelector('.modal-body');
            modalBody.innerHTML = html;
            
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
        })
        .catch(error => {
            console.error('Error loading modal content:', error);
            showToast('فشل في تحميل البيانات، يرجى المحاولة لاحقًا', 'error');
        });
}

/**
 * MWHEBA Stock - وحدة إدارة الموردين
 */

// تنفيذ التهيئة عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // تهيئة أزرار الإجراءات
    initializeActionButtons();
    
    // تهيئة الوظائف الأخرى
    initFormHandlers();
});

/**
 * تهيئة أزرار الإجراءات مع تأثيرات متقدمة
 */
function initializeActionButtons() {
    // إضافة تأثير تفاعلي للأزرار
    document.querySelectorAll('.btn-action').forEach(btn => {
        // إضافة تأثير عند تمرير المؤشر
        btn.addEventListener('mouseenter', function() {
            const tooltip = this.getAttribute('title');
            if (tooltip) {
                this.setAttribute('data-original-title', tooltip);
                this.setAttribute('aria-label', tooltip);
            }
        });
        
        // إضافة تأثير نقرة للأزرار
        btn.addEventListener('click', function() {
            this.classList.add('btn-pulse');
            setTimeout(() => {
                this.classList.remove('btn-pulse');
            }, 300);
        });
    });
    
    // تحسين زر حذف المورد
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            const supplierId = this.getAttribute('data-id');
            const supplierName = this.getAttribute('data-name');
            
            // تعيين اسم المورد في مودال التأكيد
            const supplierNameEl = document.getElementById('supplier-name-to-delete');
            if (supplierNameEl) {
                supplierNameEl.textContent = supplierName;
            }
            
            // تعيين رابط الحذف
            const deleteForm = document.getElementById('delete-supplier-form');
            if (deleteForm) {
                deleteForm.action = `/suppliers/${supplierId}/delete/`;
            }
        });
    });
}

/**
 * تهيئة معالجات النماذج
 */
function initFormHandlers() {
    // تهيئة عنصر اختيار عدد العناصر في الصفحة
    const showEntriesSelect = document.getElementById('show-entries');
    if (showEntriesSelect) {
        showEntriesSelect.addEventListener('change', function() {
            const pageSize = this.value;
            const url = new URL(window.location.href);
            url.searchParams.set('page_size', pageSize);
            window.location.href = url.toString();
        });
    }
    
    // تهيئة مودال تسجيل الدفعة
    const paymentBtns = document.querySelectorAll('[data-action="record-payment"]');
    paymentBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const supplierId = this.getAttribute('data-id');
            loadRecordPaymentModal(supplierId);
        });
    });
}

/**
 * تحميل مودال تسجيل دفعة
 */
function loadRecordPaymentModal(supplierId) {
    const modal = new bootstrap.Modal(document.getElementById('recordPaymentModal'));
    modal.show();
    
    const modalBody = document.querySelector('#recordPaymentModal .modal-body');
    
    // تحميل نموذج تسجيل الدفعة
    fetch(`/suppliers/${supplierId}/record-payment-form/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('حدث خطأ أثناء تحميل النموذج');
            }
            return response.text();
        })
        .then(html => {
            modalBody.innerHTML = html;
            
            // تهيئة نموذج الدفع
            const form = modalBody.querySelector('form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    submitPaymentForm(form, supplierId);
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            modalBody.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-danger fa-3x mb-3"></i>
                    <h5>تعذر تحميل نموذج تسجيل الدفعة</h5>
                    <p>حدث خطأ أثناء محاولة الاتصال بالخادم. يرجى المحاولة مرة أخرى.</p>
                </div>
            `;
        });
}

/**
 * إرسال نموذج تسجيل دفعة
 */
function submitPaymentForm(form, supplierId) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const formData = new FormData(form);
    
    // تعطيل زر الإرسال
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> جاري التسجيل...';
    }
    
    fetch(`/suppliers/${supplierId}/record-payment/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // إعادة تفعيل زر الإرسال
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> تسجيل الدفعة';
        }
        
        if (data.success) {
            // إغلاق المودال
            const modal = bootstrap.Modal.getInstance(document.getElementById('recordPaymentModal'));
            modal.hide();
            
            // عرض رسالة نجاح وإعادة تحميل الصفحة
            showNotification(`تم تسجيل دفعة بقيمة ${data.amount} ج.م بنجاح`, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            // عرض رسائل الخطأ
            showFormErrors(form, data.errors);
            showNotification(data.message || 'فشل تسجيل الدفعة', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        // إعادة تفعيل زر الإرسال
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> تسجيل الدفعة';
        }
        
        showNotification('حدث خطأ أثناء الاتصال بالخادم', 'error');
    });
}

/**
 * عرض أخطاء النموذج
 */
function showFormErrors(form, errors) {
    if (!errors) return;
    
    // إزالة رسائل الخطأ السابقة
    form.querySelectorAll('.is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
    
    form.querySelectorAll('.invalid-feedback').forEach(el => {
        el.remove();
    });
    
    // إضافة رسائل الخطأ الجديدة
    for (const field in errors) {
        const inputEl = form.querySelector(`[name="${field}"]`);
        if (inputEl) {
            inputEl.classList.add('is-invalid');
            
            // إنشاء عنصر التغذية الراجعة
            const feedbackEl = document.createElement('div');
            feedbackEl.className = 'invalid-feedback d-block';
            feedbackEl.textContent = Array.isArray(errors[field]) ? errors[field][0] : errors[field];
            
            // إضافة العنصر بعد حقل الإدخال مباشرة
            const fieldContainer = inputEl.closest('.mb-3') || inputEl.parentNode;
            fieldContainer.appendChild(feedbackEl);
        }
    }
}

/**
 * عرض إشعار
 */
function showNotification(message, type = 'info') {
    // استخدام Toast Bootstrap
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Toast !== 'undefined') {
        // وجود حاوية الإشعارات أو إنشاؤها
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // إنشاء Toast جديد
        const toastId = 'toast-' + Date.now();
        const toastEl = document.createElement('div');
        toastEl.id = toastId;
        toastEl.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        
        // إظهار Toast
        const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
        toast.show();
        
        // إزالة Toast بعد الإخفاء
        toastEl.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    } else {
        // استخدام alert كبديل
        alert(message);
    }
}
