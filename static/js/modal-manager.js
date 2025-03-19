/**
 * مدير المودالات المتداخلة
 * يسمح بفتح مودال داخل مودال آخر دون إغلاق المودال الأصلي
 * نسخة محسنة 1.1
 */
class NestedModalManager {
    constructor() {
        this.modalStack = [];
        this.backdrops = [];
        this.baseZIndex = 1050; // القيمة الافتراضية في Bootstrap
        this.zIndexIncrement = 10;
        this.initListeners();
        
        // إضافة أنماط CSS ديناميكياً إذا لم تكن مضافة سابقاً
        this.injectCSS();
    }
    
    injectCSS() {
        if (!document.getElementById('nested-modal-dynamic-css')) {
            const css = `
                body.modal-open.prevent-backdrop-removal .modal-backdrop {
                    opacity: 0.5 !important;
                }
                body.modal-open .modal[data-is-nested="true"] {
                    padding-right: 0 !important;
                }
            `;
            
            const style = document.createElement('style');
            style.id = 'nested-modal-dynamic-css';
            style.textContent = css;
            document.head.appendChild(style);
        }
    }
    
    initListeners() {
        // استمع إلى أحداث فتح المودالات
        document.addEventListener('show.bs.modal', this.handleModalShow.bind(this), true);
        
        // استمع إلى أحداث إغلاق المودالات
        document.addEventListener('hidden.bs.modal', this.handleModalHidden.bind(this), true);
        
        // استمع إلى أحداث اكتمال فتح المودالات
        document.addEventListener('shown.bs.modal', this.handleModalShown.bind(this), true);
    }
    
    handleModalShow(event) {
        const modalEl = event.target;
        if (!modalEl.classList.contains('modal')) return;
        
        // تحقق ما إذا كان هناك مودال آخر مفتوح
        const openModals = this.getOpenModals();
        if (openModals.length > 0) {
            // هذا مودال متداخل
            const parentModal = openModals[openModals.length - 1];
            
            // إضافة سمات المودال المتداخل
            modalEl.setAttribute('data-is-nested', 'true');
            modalEl.setAttribute('data-parent-modal-id', parentModal.id || 'unknown');
            
            // إضافة المودال الحالي للمكدس
            this.modalStack.push({
                element: modalEl,
                parentModal: parentModal,
                zIndex: this.calculateZIndex(this.modalStack.length + 1)
            });
            
            // إضافة طبقة إضافية من التحقق من الخلفية
            document.body.classList.add('prevent-backdrop-removal');
        } else {
            // أول مودال
            this.modalStack = [{
                element: modalEl,
                parentModal: null,
                zIndex: this.baseZIndex
            }];
        }
    }
    
    handleModalShown(event) {
        const modalEl = event.target;
        if (!modalEl.classList.contains('modal')) return;
        
        // ضبط z-index للمودال المتداخل وخلفيته (بعد اكتمال الفتح)
        if (modalEl.getAttribute('data-is-nested') === 'true') {
            const modalInfo = this.findModalInfo(modalEl);
            if (modalInfo) {
                // العثور على آخر خلفية مضافة
                setTimeout(() => {
                    const backdrops = document.querySelectorAll('.modal-backdrop');
                    if (backdrops.length > 0) {
                        const lastBackdrop = backdrops[backdrops.length - 1];
                        
                        // ضبط z-index للخلفية والمودال
                        lastBackdrop.style.zIndex = (modalInfo.zIndex - 1).toString();
                        modalEl.style.zIndex = modalInfo.zIndex.toString();
                        
                        // تخزين الخلفية للاستخدام لاحقاً
                        this.backdrops.push({
                            element: lastBackdrop,
                            forModal: modalEl,
                            zIndex: modalInfo.zIndex - 1
                        });
                    }
                }, 50);
            }
        }
    }
    
    handleModalHidden(event) {
        const modalEl = event.target;
        if (!modalEl.classList.contains('modal')) return;
        
        // تأكد من أنه مودال متداخل
        const isNested = modalEl.getAttribute('data-is-nested') === 'true';
        const modalIndex = this.findModalIndex(modalEl);
        
        if (modalIndex !== -1) {
            // إزالة المودال من المكدس
            const modalInfo = this.modalStack[modalIndex];
            this.modalStack.splice(modalIndex, 1);
            
            // إذا كان لديه مودال أصلي، تأكد من إعادة تنشيطه
            if (isNested && modalInfo.parentModal) {
                this.reactivateParentModal(modalInfo.parentModal);
            }
            
            // إزالة الخلفية المرتبطة بهذا المودال
            const backdropIndex = this.backdrops.findIndex(b => b.forModal === modalEl);
            if (backdropIndex !== -1) {
                this.backdrops.splice(backdropIndex, 1);
            }
            
            // إزالة فئة منع إزالة الخلفية إذا لم يبق مودالات متداخلة
            if (this.modalStack.filter(m => m.element.getAttribute('data-is-nested') === 'true').length === 0) {
                document.body.classList.remove('prevent-backdrop-removal');
            }
        }
    }
    
    reactivateParentModal(parentModal) {
        if (!parentModal) return;
        
        // تأكد من أن المودال الأصلي ما زال مفتوحاً (بعد إغلاق المودال المتداخل)
        setTimeout(() => {
            // التأكد من وجود خلفية نشطة أولاً
            if (document.querySelectorAll('.modal-backdrop').length > 0) {
                if (!parentModal.classList.contains('show')) {
                    parentModal.classList.add('show');
                }
                document.body.classList.add('modal-open');
            }
        }, 150);
    }
    
    getOpenModals() {
        return Array.from(document.querySelectorAll('.modal.show'));
    }
    
    calculateZIndex(level) {
        return this.baseZIndex + (level * this.zIndexIncrement);
    }
    
    findModalInfo(modalEl) {
        return this.modalStack.find(info => info.element === modalEl);
    }
    
    findModalIndex(modalEl) {
        return this.modalStack.findIndex(info => info.element === modalEl);
    }
}

// تهيئة الإدارة عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // تأكد من عدم إنشاء نسخة أخرى إذا كانت موجودة بالفعل
    if (!window.nestedModalManager) {
        window.nestedModalManager = new NestedModalManager();
        console.debug('NestedModalManager initialized');
    }
});
