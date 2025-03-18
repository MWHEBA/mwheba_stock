// ملف جافاسكريبت خاص بصفحة العملاء

document.addEventListener('DOMContentLoaded', function() {
    // تفعيل التلميحات
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // تفعيل البحث إذا كان هناك قيم فلترة فعالة
    if (document.querySelector('#searchCollapse')) {
        const hasFilters = document.querySelector('.badge.rounded-pill.bg-primary.bg-opacity-10') || 
                        document.querySelector('.badge.bg-opacity-10');
        if (hasFilters) {
            new bootstrap.Collapse(document.getElementById('searchCollapse')).show();
        }
    }

    // تغيير عدد العناصر المعروضة
    const showEntriesSelect = document.getElementById('show-entries');
    if (showEntriesSelect) {
        showEntriesSelect.addEventListener('change', function() {
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('page_size', this.value);
            window.location.href = currentUrl;
        });
    }
    
    // تطبيق التصفية عند تغيير أي من الحقول
    document.querySelectorAll('#filter-form select').forEach(function(select) {
        select.addEventListener('change', function() {
            document.getElementById('filter-form').submit();
        });
    });
    
    // إعداد مودال حذف العميل
    const deleteModal = document.getElementById('deleteCustomerModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const customerId = button.getAttribute('data-id');
            const customerName = button.getAttribute('data-name');
            
            document.getElementById('customer-name-to-delete').textContent = customerName;
            document.getElementById('delete-customer-form').action = `/customers/${customerId}/delete/`;
        });
    }

    // تعديل الأزرار لفتح المودال بدلاً من الانتقال للصفحة
    document.querySelectorAll('.view-customer-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            loadCustomerDetails(this.getAttribute('data-id'));
        });
    });
    
    document.querySelectorAll('.edit-customer-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            loadCustomerForEdit(this.getAttribute('data-id'));
        });
    });
    
    // حفظ العميل الجديد
    const saveCustomerBtn = document.getElementById('saveCustomerBtn');
    if (saveCustomerBtn) {
        saveCustomerBtn.addEventListener('click', function() {
            const form = document.getElementById('addCustomerForm');
            
            // التحقق من صحة النموذج
            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                return;
            }
            
            // إظهار مؤشر التحميل
            document.getElementById('loading-overlay').classList.remove('d-none');
            
            // إرسال النموذج
            const formData = new FormData(form);
            
            fetch(form.getAttribute('action'), {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'  // إضافة هذا الخيار للتأكد من إرسال الكوكيز
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // إخفاء مؤشر التحميل
                document.getElementById('loading-overlay').classList.add('d-none');
                
                if (data.success) {
                    // إغلاق المودال
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addCustomerModal'));
                    modal.hide();
                    
                    // عرض رسالة نجاح
                    showToast('تم إضافة العميل ' + data.customer_name + ' بنجاح', 'success');
                    
                    // إعادة تحميل الصفحة بعد فترة قصيرة
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    // تحسين معالجة رسائل الخطأ
                    console.log('Error response details:', data);
                    
                    let errorMessage = 'حدث خطأ أثناء إضافة العميل';
                    
                    // إذا كان هناك أخطاء محددة
                    if (data.errors) {
                        if (typeof data.errors === 'object') {
                            // تحويل كائن الأخطاء إلى نص مقروء
                            errorMessage = Object.entries(data.errors)
                                .map(([field, error]) => `${getFieldName(field)}: ${error}`)
                                .join('<br>');
                        } else if (typeof data.errors === 'string') {
                            errorMessage = data.errors;
                        }
                    } else if (data.error) {
                        errorMessage = data.error;
                    }
                    
                    // عرض رسائل الخطأ
                    showToast(errorMessage, 'error');
                }
            })
            .catch(error => {
                // إخفاء مؤشر التحميل
                document.getElementById('loading-overlay').classList.add('d-none');
                
                console.error('Error details:', error);
                showToast('حدث خطأ في الاتصال بالخادم. يرجى المحاولة مرة أخرى.', 'error');
            });
        });
    }
    
    // حدث نقر زر التعديل من مودال العرض
    const openEditModalBtn = document.getElementById('openEditModalBtn');
    if (openEditModalBtn) {
        openEditModalBtn.addEventListener('click', function() {
            const customerId = this.getAttribute('data-id');
            loadCustomerForEdit(customerId);
        });
    }
    
    // حفظ تعديلات العميل
    const updateCustomerBtn = document.getElementById('updateCustomerBtn');
    if (updateCustomerBtn) {
        updateCustomerBtn.addEventListener('click', function() {
            const form = document.getElementById('editCustomerForm');
            
            // التحقق من صحة النموذج
            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                return;
            }
            
            // إرسال النموذج
            const formData = new FormData(form);
            
            fetch(form.getAttribute('action'), {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // إغلاق المودال
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editCustomerModal'));
                    modal.hide();
                    
                    // عرض رسالة نجاح
                    showToast('تم تحديث بيانات العميل بنجاح', 'success');
                    
                    // إعادة تحميل الصفحة
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    // عرض رسائل الخطأ
                    showToast('حدث خطأ: ' + (data.errors || 'خطأ غير معروف'), 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('حدث خطأ أثناء معالجة الطلب', 'error');
            });
        });
    }
    
    // تنسيق أرقام الهواتف
    document.querySelectorAll('.phone-input').forEach(input => {
        input.addEventListener('input', function() {
            let value = this.value.replace(/[^\d+]/g, '');
            this.value = value;
        });
    });

    // إضافة تأثير التلميح للبطاقات
    document.querySelectorAll('.card-hover').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('shadow');
        });

        card.addEventListener('mouseleave', function() {
            this.classList.remove('shadow');
        });
    });

    // تفعيل زر الشريط الجانبي في الصفحة التفصيلية للعميل
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-customer');
    if (sidebarToggleBtn) {
        const customerSidebar = document.getElementById('customer-sidebar');
        sidebarToggleBtn.addEventListener('click', function() {
            customerSidebar.classList.toggle('collapsed');
            document.getElementById('customer-main-content').classList.toggle('expanded');
        });
    }

    // تحديث حالة الدفع عند تغيير المبلغ المدفوع
    const paymentAmountInput = document.getElementById('payment-amount');
    if (paymentAmountInput) {
        paymentAmountInput.addEventListener('input', updatePaymentSummary);
    }
});

// وظائف مساعدة
function loadCustomerDetails(customerId) {
    const detailContent = document.getElementById('customerDetailContent');
    detailContent.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري التحميل...</span>
            </div>
        </div>
    `;
    
    // فتح المودال
    const modal = new bootstrap.Modal(document.getElementById('viewCustomerModal'));
    modal.show();
    
    // تحميل البيانات عبر AJAX
    fetch(`/customers/${customerId}/detail/?format=modal`)
        .then(response => response.text())
        .then(html => {
            detailContent.innerHTML = html;
            const editBtn = document.getElementById('openEditModalBtn');
            if (editBtn) {
                editBtn.setAttribute('data-id', customerId);
            }
            const viewFullPageBtn = document.getElementById('viewFullPageBtn');
            if (viewFullPageBtn) {
                viewFullPageBtn.href = `/customers/${customerId}/`;
            }
            const createInvoiceBtn = document.getElementById('createInvoiceBtn');
            if (createInvoiceBtn) {
                createInvoiceBtn.href = `/sales/create/?customer_id=${customerId}`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            detailContent.innerHTML = `<div class="alert alert-danger">حدث خطأ أثناء تحميل البيانات</div>`;
        });
}

function loadCustomerForEdit(customerId) {
    // إغلاق مودال العرض إذا كان مفتوحاً
    const viewModal = bootstrap.Modal.getInstance(document.getElementById('viewCustomerModal'));
    if (viewModal) {
        viewModal.hide();
    }
    
    // إعداد رابط الإرسال
    document.getElementById('editCustomerForm').setAttribute('action', `/customers/${customerId}/edit/`);
    
    // تحميل بيانات العميل
    fetch(`/customers/${customerId}/get-data/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const customer = data.customer;
                
                // ملء النموذج
                document.getElementById('edit-name').value = customer.name;
                document.getElementById('edit-code').value = customer.code || ''; // إضافة كود العميل
                document.getElementById('edit-phone').value = customer.phone || '';
                document.getElementById('edit-email').value = customer.email || '';
                document.getElementById('edit-address').value = customer.address || '';
                document.getElementById('edit-credit_limit').value = customer.credit_limit;
                document.getElementById('edit-category').value = customer.category_id || '';
                document.getElementById('edit-status').value = customer.status;
                
                // فتح المودال
                const modal = new bootstrap.Modal(document.getElementById('editCustomerModal'));
                modal.show();
            } else {
                showToast('خطأ: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('حدث خطأ أثناء تحميل البيانات', 'error');
        });
}

function showToast(message, type = 'info') {
    // التحقق من وجود عنصر الإشعارات، وإنشاءه إذا كان غير موجود
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '5000';
        document.body.appendChild(toastContainer);
    }
    
    // إنشاء الإشعار
    const toastId = 'toast-' + Date.now();
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type}`;
    toastEl.id = toastId;
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
    
    // إظهار الإشعار
    const toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
    toast.show();
    
    // إزالة الإشعار بعد إخفائه
    toastEl.addEventListener('hidden.bs.toast', function () {
        toastEl.remove();
    });
}

// تحويل اسم الحقل التقني إلى اسم عربي مقروء
function getFieldName(field) {
    const fieldNames = {
        'name': 'الاسم',
        'phone': 'رقم الهاتف',
        'email': 'البريد الإلكتروني',
        'address': 'العنوان',
        'credit_limit': 'حد الائتمان',
        'category': 'التصنيف',
        'status': 'الحالة'
    };
    
    return fieldNames[field] || field;
}

// وظيفة لتحديث ملخص الدفع
function updatePaymentSummary() {
    const amount = parseFloat(document.getElementById('payment-amount').value) || 0;
    const totalDebt = parseFloat(document.getElementById('total-debt').dataset.value) || 0;
    const remainingAmount = Math.max(0, totalDebt - amount);
    
    document.getElementById('payment-summary-amount').textContent = amount.toFixed(2);
    document.getElementById('payment-summary-remaining').textContent = remainingAmount.toFixed(2);
    
    // تحديث لون المبلغ المتبقي
    const remainingElement = document.getElementById('payment-summary-remaining-container');
    if (remainingAmount > 0) {
        remainingElement.className = 'text-danger';
    } else {
        remainingElement.className = 'text-success';
    }
}
