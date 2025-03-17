/**
 * أداة مساعدة لتحميل البيانات المقسمة من API
 */
class PaginatedDataLoader {
    constructor(options) {
        this.apiUrl = options.apiUrl;
        this.container = options.container;
        this.template = options.template;
        this.pageSize = options.pageSize || 50;
        this.currentPage = 1;
        this.totalPages = 0;
        this.loading = false;
        this.filters = options.filters || {};
        
        // إنشاء عنصر زر "تحميل المزيد"
        this.loadMoreBtn = document.createElement('button');
        this.loadMoreBtn.className = 'btn btn-primary d-block mx-auto mt-3';
        this.loadMoreBtn.innerHTML = 'تحميل المزيد <i class="fas fa-chevron-down ms-1"></i>';
        this.loadMoreBtn.addEventListener('click', () => this.loadNextPage());
        
        // إنشاء عنصر التحميل
        this.loadingIndicator = document.createElement('div');
        this.loadingIndicator.className = 'd-flex justify-content-center mt-3';
        this.loadingIndicator.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري التحميل...</span>
            </div>
        `;
        
        // التهيئة الأولية
        this.init();
    }
    
    async init() {
        // تنظيف الحاوية
        this.container.innerHTML = '';
        
        // إضافة مؤشر التحميل
        this.container.appendChild(this.loadingIndicator);
        
        // تحميل الصفحة الأولى
        await this.loadPage(1);
        
        // إزالة مؤشر التحميل
        this.container.removeChild(this.loadingIndicator);
        
        // إضافة زر "تحميل المزيد" إذا كان هناك صفحات أخرى
        if (this.currentPage < this.totalPages) {
            this.container.appendChild(this.loadMoreBtn);
        }
    }
    
    async loadPage(page) {
        if (this.loading) return;
        
        this.loading = true;
        
        try {
            // بناء URL مع المعلمات
            let url = new URL(this.apiUrl, window.location.origin);
            url.searchParams.append('page', page);
            url.searchParams.append('page_size', this.pageSize);
            
            // إضافة المرشحات
            for (const [key, value] of Object.entries(this.filters)) {
                if (value) {
                    url.searchParams.append(key, value);
                }
            }
            
            // إرسال الطلب
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                // تحديث معلومات الصفحات
                this.currentPage = data.data.page;
                this.totalPages = data.data.total_pages;
                
                // عرض البيانات
                data.data.data.forEach(item => {
                    const renderedItem = this.template(item);
                    this.container.insertAdjacentHTML('beforeend', renderedItem);
                });
                
                // تحديث حالة زر تحميل المزيد
                if (this.currentPage >= this.totalPages) {
                    // إزالة زر "تحميل المزيد" إذا وصلنا للنهاية
                    if (this.container.contains(this.loadMoreBtn)) {
                        this.container.removeChild(this.loadMoreBtn);
                    }
                } else {
                    // إضافة زر "تحميل المزيد" إذا لم يكن موجودًا
                    if (!this.container.contains(this.loadMoreBtn)) {
                        this.container.appendChild(this.loadMoreBtn);
                    }
                }
            } else {
                console.error('خطأ في تحميل البيانات:', data.error || data.message);
            }
        } catch (error) {
            console.error('خطأ في تحميل البيانات:', error);
        } finally {
            this.loading = false;
        }
    }
    
    loadNextPage() {
        if (this.currentPage < this.totalPages) {
            // إزالة زر التحميل مؤقتاً
            this.container.removeChild(this.loadMoreBtn);
            
            // إضافة مؤشر التحميل
            this.container.appendChild(this.loadingIndicator);
            
            // تحميل الصفحة التالية
            this.loadPage(this.currentPage + 1).then(() => {
                // إزالة مؤشر التحميل
                this.container.removeChild(this.loadingIndicator);
            });
        }
    }
    
    updateFilters(newFilters) {
        this.filters = { ...this.filters, ...newFilters };
        this.init();
    }
}
