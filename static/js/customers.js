/**
 * MWHEBA Stock - وحدة إدارة العملاء
 * تم إعادة هيكلته لتحسين الأداء ومنع التكرار
 */

// ==========================================
// المتغيرات العالمية والتهيئة
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    // تهيئة جميع الوظائف عند تحميل الصفحة
    initializeCustomerModule();
    initializeActionButtons();
});

/**
 * الدالة الرئيسية لتهيئة وحدة العملاء
 */
function initializeCustomerModule() {
    // معالجة نظام التنقل بين التبويبات في النماذج
    initTabNavigation();
    
    // تهيئة الأزرار والمودالات ونماذج الإدخال
    initCustomerActionButtons();
    initModals();
    initFormInputs();
    
    // تهيئة مودال إضافة تصنيف
    initCategoryFunctionality();
    
    // معالجة نماذج العملاء
    initCustomerForms();
}

// ==========================================
// وظائف المعالجة الرئيسية
// ==========================================

/**
 * تهيئة وظائف التنقل بين التبويبات
 */
function initTabNavigation() {
    // أزرار التنقل للأمام
    document.querySelectorAll('.next-tab').forEach(button => {
        button.addEventListener('click', function() {
            const nextTabId = this.getAttribute('data-next');
            activateTab(nextTabId);
        });
    });

    // أزرار التنقل للخلف
    document.querySelectorAll('.prev-tab').forEach(button => {
        button.addEventListener('click', function() {
            const prevTabId = this.getAttribute('data-prev');
            activateTab(prevTabId);
        });
    });
}

/**
 * تفعيل تبويب معين
 */
function activateTab(tabId) {
    const tabElement = document.getElementById(tabId);
    if (tabElement) {
        const tab = new bootstrap.Tab(tabElement);
        tab.show();
    }
}

/**
 * تهيئة أزرار إجراءات العملاء
 */
function initCustomerActionButtons() {
    // زر إضافة/تعديل عميل
    initSaveCustomerButton();
    
    // أزرار عرض وحذف العميل
    initViewCustomerButtons();
    initDeleteCustomerButtons();
    
    // أزرار دفعات العملاء
    initPaymentButtons();
    
    // زر معاينة بيانات العميل
    initPreviewButton();
}

/**
 * تهيئة زر حفظ العميل
 */
function initSaveCustomerButton() {
    const saveBtn = document.getElementById('saveCustomerBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function(e) {
            e.preventDefault();
            submitCustomerForm();
        });
    }
}

/**
 * إرسال نموذج بيانات العميل
 */
function submitCustomerForm() {
    const form = document.getElementById('addCustomerForm') || document.getElementById('editCustomerForm') || document.getElementById('customerForm');
    if (!form) return;
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // حفظ زر الإرسال المستخدم، إذا كان موجوداً
    let submitAction = '';
    if (event && event.submitter && event.submitter.name) {
        submitAction = event.submitter.name;
    }
    
    // تحديد ما إذا كان يجب استخدام AJAX
    const useAjax = form.hasAttribute('data-ajax') && form.getAttribute('data-ajax') === 'true';
    
    // إذا كنا لا نستخدم AJAX، فقط قم بتقديم النموذج بالطريقة التقليدية
    if (!useAjax) {
        // تغيير قيمة is_ajax إلى 0 للتأكد من الحصول على استجابة كاملة
        const isAjaxField = form.querySelector('input[name="is_ajax"]');
        if (isAjaxField) {
            isAjaxField.value = '0';
        }
        form.submit();
        return;
    }
    
    // إرسال النموذج بواسطة AJAX
    const formData = new FormData(form);
    formData.set('is_ajax', '1'); // تعيين القيمة إلى 1 لاستجابة Ajax
    
    // إضافة قيمة زر الإرسال المستخدم، إذا كان موجوداً
    if (submitAction) {
        formData.append(submitAction, 'true');
    }
    
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> جاري الحفظ...';
    }
    
    const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]').value;
    
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // إعادة تفعيل زر الحفظ
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> حفظ';
        }
        
        if (data.success) {
            showNotification(`تم حفظ بيانات العميل ${data.customer_name} بنجاح`, 'success');
            
            // التحويل إلى صفحة أخرى بعد فترة قصيرة حسب الزر المضغوط
            setTimeout(() => {
                let redirectUrl = form.getAttribute('data-redirect-url') || `/customers/${data.customer_id}/`;
                
                // معالجة التحويل بناءً على زر الإرسال
                if (submitAction === 'save_and_add_another' || submitAction === 'save_and_add_new') {
                    redirectUrl = '/customers/create/';
                } else if (submitAction === 'save_and_add_sale') {
                    redirectUrl = `/invoices/create/?customer=${data.customer_id}`;
                }
                
                window.location.href = redirectUrl;
            }, 1000);
        } else {
            // إظهار أخطاء التحقق
            showFormErrors(form, data.errors);
            showNotification('يرجى تصحيح الأخطاء وإعادة المحاولة', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> حفظ';
        }
        
        showNotification('حدث خطأ أثناء إرسال البيانات. يرجى المحاولة مرة أخرى.', 'error');
    });
}

/**
 * تهيئة أزرار عرض تفاصيل العميل
 */
function initViewCustomerButtons() {
    document.querySelectorAll('.view-customer-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const customerId = this.getAttribute('data-id');
            loadCustomerDetails(customerId);
        });
    });
}

/**
 * تحميل تفاصيل العميل
 */
function loadCustomerDetails(customerId) {
    // إظهار المودال الرئيسي
    const modal = new bootstrap.Modal(document.getElementById('viewCustomerModal'));
    modal.show();
    
    const modalContent = document.querySelector('#viewCustomerModal .modal-content');
    
    // إظهار مؤشر التحميل
    modalContent.innerHTML = `
        <div class="d-flex justify-content-center p-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري التحميل...</span>
            </div>
        </div>
    `;
    
    // تحميل محتوى المودال من الخادم
    fetch(`/customers/${customerId}/get-data/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('حدث خطأ أثناء تحميل البيانات');
            }
            return response.text();
        })
        .then(html => {
            modalContent.innerHTML = html;
            
            // إعادة تهيئة وظائف أزرار تسجيل الدفعات
            const paymentBtn = modalContent.querySelector('#recordPaymentBtn');
            if (paymentBtn) {
                paymentBtn.addEventListener('click', function() {
                    modal.hide();
                    loadPaymentModal(this.getAttribute('data-id'));
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            modalContent.innerHTML = `
                <div class="modal-header bg-danger text-white">
                    <h5 class="modal-title">خطأ</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body p-4 text-center">
                    <i class="fas fa-exclamation-triangle text-danger fa-3x mb-3"></i>
                    <h5>تعذر تحميل بيانات العميل</h5>
                    <p>حدث خطأ أثناء محاولة الاتصال بالخادم. يرجى المحاولة مرة أخرى.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إغلاق</button>
                </div>
            `;
        });
}

/**
 * تهيئة أزرار حذف العميل
 */
function initDeleteCustomerButtons() {
    // تهيئة مودال الحذف
    const deleteModal = document.getElementById('deleteCustomerModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const customerId = button.getAttribute('data-id');
            const customerName = button.getAttribute('data-name');
            
            // تحديث بيانات المودال
            document.getElementById('customerIdToDelete').value = customerId;
            document.getElementById('customerNameToDelete').textContent = customerName;
        });
        
        // تنفيذ الحذف عند التأكيد
        const confirmDeleteBtn = document.getElementById('confirmDeleteCustomer');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', deleteCustomer);
        }
    }
}

/**
 * حذف العميل
 */
function deleteCustomer() {
    const form = document.getElementById('deleteCustomerForm');
    const customerId = document.getElementById('customerIdToDelete').value;
    
    if (!customerId || !form) return;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const formData = new FormData(form);
    
    // تعطيل زر الحذف
    this.disabled = true;
    this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> جاري الحذف...';
    
    fetch(`/customers/${customerId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // إعادة تفعيل زر الحذف
        this.disabled = false;
        this.innerHTML = '<i class="fas fa-trash-alt me-1"></i> حذف';
        
        if (data.success) {
            // إغلاق المودال
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteCustomerModal'));
            modal.hide();
            
            showNotification('تم حذف العميل بنجاح', 'success');
            
            // إعادة تحميل الصفحة بعد فترة قصيرة
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(data.message || 'فشلت عملية الحذف', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        // إعادة تفعيل زر الحذف
        this.disabled = false;
        this.innerHTML = '<i class="fas fa-trash-alt me-1"></i> حذف';
        
        showNotification('حدث خطأ أثناء الاتصال بالخادم', 'error');
    });
}

/**
 * تهيئة أزرار تسجيل الدفعات
 */
function initPaymentButtons() {
    document.querySelectorAll('[data-action="record-payment"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const customerId = this.getAttribute('data-id');
            loadPaymentModal(customerId);
        });
    });
}

/**
 * تحميل مودال تسجيل دفعة
 */
function loadPaymentModal(customerId) {
    const modal = new bootstrap.Modal(document.getElementById('recordPaymentModal'));
    modal.show();
    
    const modalBody = document.querySelector('#recordPaymentModal .modal-body');
    
    // تحميل نموذج تسجيل الدفعة
    fetch(`/customers/${customerId}/record-payment-form/`)
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
                    submitPaymentForm(form, customerId);
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
function submitPaymentForm(form, customerId) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const formData = new FormData(form);
    
    // تعطيل زر الإرسال
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> جاري التسجيل...';
    }
    
    fetch(`/customers/${customerId}/record-payment/`, {
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
            
            showNotification(`تم تسجيل دفعة بقيمة ${data.amount} ج.م بنجاح`, 'success');
            
            // إعادة تحميل الصفحة بعد فترة قصيرة
            setTimeout(() => location.reload(), 1500);
        } else {
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
 * تهيئة زر معاينة بيانات العميل
 */
function initPreviewButton() {
    const previewBtn = document.getElementById('previewCustomerBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', function() {
            updatePreviewData();
        });
    }
}

/**
 * تحديث بيانات المعاينة
 */
function updatePreviewData() {
    const name = document.getElementById('id_name').value || '--';
    const phone = document.getElementById('id_phone').value || '--';
    const email = document.getElementById('id_email').value || '--';
    const address = document.getElementById('id_address').value || '--';
    
    // تحديث عناصر المعاينة
    document.getElementById('preview_name').textContent = name;
    document.getElementById('preview_phone').textContent = phone;
    document.getElementById('preview_email').textContent = email;
    document.getElementById('preview_address').textContent = address;
    
    // عرض قسم المعاينة
    document.getElementById('customerPreview').style.display = 'block';
}

/**
 * تهيئة عرض المودالات
 */
function initModals() {
    // تهيئة مودال العرض عند الإغلاق
    const viewModal = document.getElementById('viewCustomerModal');
    if (viewModal) {
        viewModal.addEventListener('hidden.bs.modal', function() {
            const modalContent = this.querySelector('.modal-content');
            modalContent.innerHTML = `
                <div class="d-flex justify-content-center p-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">جاري التحميل...</span>
                    </div>
                </div>
            `;
        });
    }
    
    // تهيئة باقي المودالات...
}

/**
 * تهيئة حقول الإدخال
 */
function initFormInputs() {
    // تهيئة حقول إدخال الهاتف
    document.querySelectorAll('.phone-input').forEach(input => {
        input.addEventListener('input', function() {
            let value = this.value.replace(/[^\d+]/g, '');
            this.value = value;
        });
    });
    
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
}

/**
 * تهيئة وظائف إضافة/تعديل التصنيفات
 */
function initCategoryFunctionality() {
    // التحقق مما إذا كان يجب تخطي معالج التصنيف (في حالة وجود معالج مخصص في الصفحة)
    const skipCategoryHandler = document.currentScript && 
                             document.currentScript.getAttribute('data-skip-category-handler') === "true";
    
    if (!skipCategoryHandler) {
        const saveNewCategoryBtn = document.getElementById('save-new-category');
        if (saveNewCategoryBtn && !saveNewCategoryBtn.hasAttribute('data-handler-attached')) {
            saveNewCategoryBtn.setAttribute('data-handler-attached', 'true');
            
            // تهيئة معالج مودال التصنيف
            const categoryModal = document.getElementById('newCategoryModal');
            if (categoryModal) {
                initNestedModal(categoryModal);
            }
            
            // ربط حدث النقر على زر الحفظ
            saveNewCategoryBtn.addEventListener('click', saveCategoryHandler);
        }
    }
}

/**
 * مساعد لتهيئة المودال المتداخل
 */
function initNestedModal(modal) {
    if (!modal) return;
    
    // تأكد من وجود نافذة مدير المودالات المتداخلة
    if (typeof window.nestedModalManager === 'undefined') {
        // إذا لم يكن موجوداً، أنشئ تهيئة محلية بسيطة
        modal.addEventListener('show.bs.modal', function() {
            // حفظ مرجع للمودال المفتوح
            const parentModals = document.querySelectorAll('.modal.show');
            if (parentModals.length > 0) {
                const parentModal = parentModals[parentModals.length - 1];
                modal.setAttribute('data-parent-modal', parentModal.id);
                
                // زيادة z-index للمودال الجديد والخلفية
                setTimeout(() => {
                    const backdrops = document.querySelectorAll('.modal-backdrop');
                    if (backdrops.length > 0) {
                        const lastBackdrop = backdrops[backdrops.length - 1];
                        const zIndex = parseInt(getComputedStyle(parentModal).zIndex || 1050);
                        modal.style.zIndex = (zIndex + 10).toString();
                        lastBackdrop.style.zIndex = (zIndex + 9).toString();
                    }
                }, 10);
            }
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            // إعادة فتح المودال الأصلي إذا كان موجوداً
            const parentModalId = modal.getAttribute('data-parent-modal');
            if (parentModalId) {
                const parentModal = document.getElementById(parentModalId);
                if (parentModal) {
                    setTimeout(() => {
                        parentModal.classList.add('show');
                        parentModal.style.display = 'block';
                        document.body.classList.add('modal-open');
                    }, 150);
                }
            }
        });
    }
}

/**
 * معالج حدث حفظ التصنيف
 */
function saveCategoryHandler(e) {
    e.preventDefault();
    
    const categoryName = document.getElementById('new-category-name').value.trim();
    const categoryColor = document.getElementById('new-category-color').value;
    const categoryDescription = document.getElementById('new-category-description').value.trim();
    
    if (!categoryName) {
        showNotification('يرجى إدخال اسم التصنيف', 'warning');
        return;
    }
    
    // تعطيل الزر لمنع النقر المتكرر
    this.disabled = true;
    this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> جاري الحفظ...';
    
    // الحصول على URL المناسب (من متغير عالمي أو مسار افتراضي)
    const url = typeof categoryCreateAjaxUrl !== 'undefined' ? 
        categoryCreateAjaxUrl : '/customers/categories/create/';
    
    // الحصول على CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // إرسال البيانات
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            name: categoryName,
            color_code: categoryColor,
            description: categoryDescription
        })
    })
    .then(response => response.json())
    .then(data => {
        // إعادة تفعيل الزر
        this.disabled = false;
        this.innerHTML = '<i class="fas fa-save me-1"></i> حفظ التصنيف';
        
        if (data.success) {
            // إضافة التصنيف الجديد لقائمة التصنيفات
            const categorySelect = document.getElementById('id_category');
            if (categorySelect) {
                const option = new Option(categoryName, data.id);
                categorySelect.add(option);
                option.selected = true;
            }
            
            // إغلاق المودال
            const modal = bootstrap.Modal.getInstance(document.getElementById('newCategoryModal'));
            if (modal) {
                modal.hide();
            }
            
            // مسح قيم الحقول
            document.getElementById('new-category-name').value = '';
            document.getElementById('new-category-description').value = '';
            
            // رسالة نجاح
            showNotification('تم إضافة التصنيف بنجاح', 'success');
        } else {
            showNotification(data.error || 'فشل إنشاء التصنيف', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        // إعادة تفعيل الزر
        this.disabled = false;
        this.innerHTML = '<i class="fas fa-save me-1"></i> حفظ التصنيف';
        
        showNotification('حدث خطأ أثناء الاتصال بالخادم', 'error');
    });
}

/**
 * تهيئة نماذج العملاء
 */
function initCustomerForms() {
    // نموذج العميل الرئيسي (صفحة الإضافة/التعديل)
    const customerForm = document.getElementById('customerForm');
    if (customerForm) {
        // التحقق مما إذا كان النموذج بالفعل في صفحة كاملة وليس في مودال
        const isInPage = !customerForm.closest('.modal');
        
        if (isInPage) {
            // مهم: لا تمنع السلوك الافتراضي للنموذج في الصفحة الكاملة
            customerForm.addEventListener('submit', function() {
                // تأكد من أن القيمة صفر للحصول على استجابة عادية (غير AJAX)
                const isAjaxField = this.querySelector('input[name="is_ajax"]');
                if (isAjaxField) {
                    isAjaxField.value = '0';
                }
            });
        }
    }
    
    // تهيئة النماذج في المودالات فقط
    initModalForms();
}

/**
 * تهيئة نماذج المودالات
 */
function initModalForms() {
    // نموذج إضافة العميل في المودال
    const addCustomerForm = document.getElementById('addCustomerForm');
    if (addCustomerForm && addCustomerForm.closest('.modal')) {
        addCustomerForm.addEventListener('submit', function(e) {
            e.preventDefault(); // منع السلوك الافتراضي للمودال فقط
            submitCustomerFormAjax(this);
        });
    }
    
    // نموذج تعديل العميل في المودال
    const editCustomerForm = document.getElementById('editCustomerForm');
    if (editCustomerForm && editCustomerForm.closest('.modal')) {
        editCustomerForm.addEventListener('submit', function(e) {
            e.preventDefault(); // منع السلوك الافتراضي للمودال فقط
            submitCustomerFormAjax(this);
        });
    }
}

/**
 * إرسال نموذج بيانات العميل بواسطة AJAX
 */
async function submitCustomerFormAjax(form) {
    if (!form) return;
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // الحصول على اسم العميل للتحقق من التشابه
    const customerNameInput = form.querySelector('input[name="name"]');
    if (customerNameInput && customerNameInput.value.trim()) {
        try {
            // فحص التشابه مع الأسماء الموجودة
            const result = await checkNameSimilarity(customerNameInput.value.trim());
            const similarCustomers = result.similar_customers || [];
            
            // إذا وجدت أسماء متشابهة، اعرض المودال
            if (similarCustomers.length > 0) {
                displayModalSimilarCustomers(similarCustomers, customerNameInput.value.trim(), () => {
                    // استدعاء هذه الدالة عند النقر على زر المتابعة
                    continueSubmitCustomerFormAjax(form);
                });
                return;
            }
        } catch (error) {
            console.error('Error in similarity check:', error);
            // في حالة الخطأ، نواصل الإرسال
        }
    }
    
    // إذا لم تكن هناك أسماء متشابهة أو حدث خطأ، أكمل الإرسال
    continueSubmitCustomerFormAjax(form);
}

/**
 * إظهار العملاء المتشابهين في مودال المودال
 */
function displayModalSimilarCustomers(customers, enteredName, onProceed) {
    const container = document.getElementById('modalSimilarCustomersContainer');
    if (!container) return;
    
    // إفراغ الحاوية
    container.innerHTML = '';
    
    // إضافة العملاء المتشابهين
    customers.forEach((customer) => {
        const customerCard = document.createElement('div');
        customerCard.className = 'card mb-2 border-warning';
        
        customerCard.innerHTML = `
            <div class="card-body py-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-0 fw-bold">${customer.name}</h6>
                        <small class="text-muted">${customer.phone || 'لا يوجد رقم هاتف'}</small>
                    </div>
                    <div>
                        <span class="badge rounded-pill bg-warning text-dark">
                            نسبة التشابه: ${customer.similarity}%
                        </span>
                    </div>
                </div>
            </div>
        `;
        
        // إضافة العنصر للحاوية
        container.appendChild(customerCard);
    });
    
    // إضافة ما تم إدخاله
    const enteredNameInfo = document.createElement('div');
    enteredNameInfo.className = 'alert alert-info mt-3 mb-0';
    enteredNameInfo.innerHTML = `
        <strong>الاسم الذي أدخلته:</strong> ${enteredName}
    `;
    container.appendChild(enteredNameInfo);
    
    // تهيئة زر المتابعة
    const proceedBtn = document.getElementById('modalProceedWithAddBtn');
    if (proceedBtn) {
        // إزالة معالجات الأحداث السابقة
        const newProceedBtn = proceedBtn.cloneNode(true);
        proceedBtn.parentNode.replaceChild(newProceedBtn, proceedBtn);
        
        // إضافة معالج حدث جديد
        newProceedBtn.addEventListener('click', function() {
            // إغلاق المودال
            const modalElement = document.getElementById('nameSimilarityModal');
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) modal.hide();
            
            // استدعاء دالة المتابعة
            if (typeof onProceed === 'function') {
                onProceed();
            }
        });
    }
    
    // عرض المودال
    const modalElement = document.getElementById('nameSimilarityModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

/**
 * متابعة إرسال نموذج العميل بعد فحص التشابه
 */
function continueSubmitCustomerFormAjax(form) {
    if (!form) return;
    
    // تحديد زر الإرسال المستخدم
    const submitButton = document.activeElement;
    let submitAction = '';
    if (submitButton && submitButton.name) {
        submitAction = submitButton.name;
    }
    
    // إعداد بيانات النموذج
    const formData = new FormData(form);
    formData.set('is_ajax', '1'); // تعيين القيمة إلى 1 لاستجابة AJAX
    
    // إضافة قيمة زر الإرسال المستخدم، إذا كان موجوداً
    if (submitAction) {
        formData.append(submitAction, 'true');
    }
    
    // تعطيل زر الإرسال
    const submitBtn = submitButton || form.querySelector('[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> جاري الحفظ...';
    }
    
    // الحصول على CSRF token
    const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]').value;
    
    // إرسال البيانات بواسطة AJAX
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // إعادة تفعيل زر الحفظ
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> حفظ';
        }
        
        if (data.success) {
            showNotification(`تم حفظ بيانات العميل ${data.customer_name} بنجاح`, 'success');
            
            // إغلاق المودال إذا كان موجوداً
            const modal = form.closest('.modal');
            if (modal) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
                
                // فتح المودال مرة أخرى بعد لحظة قصيرة
                setTimeout(() => {
                    modal.classList.add('show');
                    modal.style.display = 'block';
                    document.body.classList.add('modal-open');
                }, 150);
            }
            
            // التحويل إلى صفحة أخرى بعد فترة قصيرة حسب الزر المضغوط
            setTimeout(() => {
                let redirectUrl = `/customers/${data.customer_id}/`;
                
                // معالجة التحويل بناءً على زر الإرسال
                if (submitAction === 'save_and_add_another' || submitAction === 'save_and_add_new') {
                    redirectUrl = '/customers/create/';
                } else if (submitAction === 'save_and_add_sale') {
                    redirectUrl = `/invoices/create/?customer=${data.customer_id}`;
                }
                
                window.location.href = redirectUrl;
            }, 1000);
        } else {
            // إظهار أخطاء التحقق
            showFormErrors(form, data.errors);
            showNotification('يرجى تصحيح الأخطاء وإعادة المحاولة', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> حفظ';
        }
        
        showNotification('حدث خطأ أثناء إرسال البيانات. يرجى المحاولة مرة أخرى.', 'error');
    });
}

/**
 * إعادة تعيين نموذج العميل وتهيئته للإضافة مرة أخرى
 */
function resetCustomerForm(form) {
    if (!form) return;
    
    // إعادة تعيين قيم النموذج
    form.reset();
    
    // إزالة رسائل الخطأ
    form.querySelectorAll('.is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
    
    form.querySelectorAll('.invalid-feedback').forEach(el => {
        el.remove();
    });
    
    // إعادة تفعيل الزر الرئيسي
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = false;
    }
    
    // التركيز على الحقل الأول (الاسم عادة)
    const firstInput = form.querySelector('input[type="text"]');
    if (firstInput) {
        setTimeout(() => {
            firstInput.focus();
        }, 300);
    }
}

/**
 * دالة معالجة نقر زر "حفظ وإضافة آخر" في مودال العميل
 */
function handleSaveAndAddAnother(e) {
    e.preventDefault();
    const form = e.target.closest('form');
    const modalId = form.closest('.modal').id;
    submitCustomerFormAjax(form, 'save_and_add_another', modalId);
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
    // استخدام Toast Bootstrap أو alert بسيط
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
    
    // تحسين زر حذف العميل
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            const customerId = this.getAttribute('data-id');
            const customerName = this.getAttribute('data-name');
            
            // تعيين اسم العميل في مودال التأكيد
            const customerNameEl = document.getElementById('customer-name-to-delete');
            if (customerNameEl) {
                customerNameEl.textContent = customerName;
            }
            
            // تعيين رابط الحذف
            const deleteForm = document.getElementById('delete-customer-form');
            if (deleteForm) {
                deleteForm.action = `/customers/${customerId}/delete/`;
            }
        });
    });
}