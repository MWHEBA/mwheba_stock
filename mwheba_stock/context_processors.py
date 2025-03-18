from django.urls import resolve
from django.utils.translation import gettext_lazy as _

def page_info(request):
    """
    Context processor to add page title and breadcrumbs information
    """
    # Default values
    page_info = {
        'module': None,
        'submodule': None,
        'title': _('صفحة'),
        'icon_class': 'fas fa-file',
        'color_class': 'primary',  # Always use primary color
    }
    
    # Try to determine current page info based on URL
    try:
        url_name = resolve(request.path_info).url_name
        
        # Define module information based on URL patterns
        if url_name == 'dashboard':
            page_info['module'] = _('لوحة التحكم')
            page_info['title'] = _('لوحة التحكم')
            page_info['icon_class'] = 'fas fa-tachometer-alt'
        
        elif 'sale' in url_name:
            page_info['module'] = _('المبيعات')
            page_info['icon_class'] = 'fas fa-shopping-cart'
            
            if 'create' in url_name:
                page_info['submodule'] = _('فاتورة بيع جديدة')
                page_info['title'] = _('فاتورة بيع جديدة')
            elif 'list' in url_name:
                page_info['submodule'] = _('قائمة المبيعات')
                page_info['title'] = _('قائمة المبيعات')
            elif 'report' in url_name:
                page_info['submodule'] = _('تقرير المبيعات')
                page_info['title'] = _('تقرير المبيعات')
            elif 'detail' in url_name:
                page_info['submodule'] = _('تفاصيل الفاتورة')
                page_info['title'] = _('تفاصيل الفاتورة')
        
        elif 'purchase' in url_name:
            page_info['module'] = _('المشتريات')
            page_info['icon_class'] = 'fas fa-truck-loading'
            
            if 'create' in url_name:
                page_info['submodule'] = _('أمر شراء جديد')
                page_info['title'] = _('أمر شراء جديد')
            elif 'list' in url_name:
                page_info['submodule'] = _('قائمة المشتريات')
                page_info['title'] = _('قائمة المشتريات')
            elif 'detail' in url_name:
                page_info['submodule'] = _('تفاصيل الطلب')
                page_info['title'] = _('تفاصيل الطلب')
        
        elif 'product' in url_name or 'inventory' in url_name:
            page_info['module'] = _('المنتجات')
            page_info['icon_class'] = 'fas fa-box'
            
            if 'create' in url_name:
                page_info['submodule'] = _('إضافة منتج جديد')
                page_info['title'] = _('إضافة منتج جديد')
            elif 'list' in url_name:
                page_info['submodule'] = _('قائمة المنتجات')
                page_info['title'] = _('قائمة المنتجات')
            elif 'inventory-report' in url_name:
                page_info['submodule'] = _('تقرير المخزون')
                page_info['title'] = _('تقرير المخزون')
            elif 'inventory-analysis' in url_name:
                page_info['submodule'] = _('تحليل المخزون')
                page_info['title'] = _('تحليل المخزون')
        
        # Add more sections based on your application's URL structure
    
    except (AttributeError, ValueError):
        # If URL resolution fails or any other error, use defaults
        pass
    
    return {'page_info': page_info}
