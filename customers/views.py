from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F, Subquery, OuterRef, Avg, Max
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
import json
from decimal import Decimal, InvalidOperation
from .models import Customer, CustomerCategory
from .forms import CustomerForm, CustomerSearchForm, CustomerCategoryForm
from sales.models import Sale, CustomerPayment

@login_required
def customer_list(request):
    """عرض قائمة العملاء مع خيارات بحث وتصفية متقدمة"""
    # إنشاء نموذج البحث مع بيانات الطلب
    form = CustomerSearchForm(request.GET)
    
    # الحصول على المعلمات
    search_query = request.GET.get('search', '')
    debt_status = request.GET.get('debt_status', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    sort_by = request.GET.get('sort_by', '-created_at')
    
    # قاعدة بيانات العملاء
    customers = Customer.objects.all()
    
    # تطبيق البحث
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) | 
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    # تصفية حسب التصنيف
    if category_id and category_id.isdigit():
        customers = customers.filter(category_id=category_id)
    
    # تصفية حسب الحالة
    if status:
        customers = customers.filter(status=status)
    
    # تصفية حسب حالة الدين
    if debt_status == 'with_debts':
        customers = customers.filter(debt__gt=0)
    elif debt_status == 'no_debts':
        customers = customers.filter(debt__lte=0)
    elif debt_status == 'exceed_limit':
        # العملاء الذين تجاوزت مديونيتهم حد الائتمان
        customers = customers.filter(credit_limit__gt=0).filter(debt__gt=F('credit_limit'))
    
    # الترتيب
    if sort_by:
        customers = customers.order_by(sort_by)
    
    # حساب الإحصاءات
    customer_count = customers.count()
    total_sales = customers.aggregate(total=Sum('total_sales'))['total'] or 0
    total_debt = customers.aggregate(total=Sum('debt'))['total'] or 0
    
    # العملاء النشطون خلال الـ 30 يوم الماضية
    thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
    active_customers = customers.filter(last_purchase_date__gte=thirty_days_ago).count()
    
    # تقسيم الصفحات
    page_size = int(request.GET.get('page_size', 10))
    paginator = Paginator(customers, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # الحصول على جميع تصنيفات العملاء لعرضها في الواجهة
    categories = CustomerCategory.objects.all()
    
    context = {
        'customers': page_obj,
        'form': form,
        'categories': categories,
        'total_customers': customer_count,
        'active_customers': active_customers,
        'total_sales': total_sales,
        'total_debt': total_debt,
        'search_query': search_query,
        'debt_status': debt_status,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_size': page_size,
        'recent_customers': active_customers,
    }
    
    # إذا كان الطلب يخص التصدير
    export_format = request.GET.get('export')
    if export_format:
        return export_customers(request, customers, export_format)
    
    return render(request, 'customers/customer_list.html', context)

# دالة مساعدة لتصدير بيانات العملاء
def export_customers(request, customers, export_format):
    """تصدير بيانات العملاء بتنسيقات مختلفة"""
    from django.http import HttpResponse
    import csv
    from datetime import datetime
    
    filename = f"customers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if export_format == 'csv':  # تم تغيير الشرط من 'excel' إلى 'csv'
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        # استخدام UTF-8-sig لدعم الأحرف العربية في CSV
        response.write('\ufeff'.encode('utf8'))
        
        writer = csv.writer(response)
        writer.writerow(['الاسم', 'الهاتف', 'البريد الإلكتروني', 'التصنيف', 'المديونية', 'الحالة'])
        
        for customer in customers:
            writer.writerow([
                customer.name,
                customer.phone or '-',
                customer.email or '-',
                customer.category.name if customer.category else '-',
                customer.debt,
                customer.get_status_display(),
            ])
        
        return response
    
    elif export_format == 'pdf':
        # TODO: تنفيذ تصدير PDF باستخدام مكتبة مناسبة
        # سنقوم بتنفيذ هذا لاحقاً
        return HttpResponse("سيتم دعم تصدير PDF قريباً")
    
    elif export_format == 'print':
        context = {
            'customers': customers,
            'today': datetime.now(),
            'title': 'قائمة العملاء'
        }
        return render(request, 'customers/print_customer_list.html', context)
    
    return redirect('customer-list')

@login_required
def customer_create(request):
    """إضافة عميل جديد مع التحقق من البيانات"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            
            # تحديد ما إذا كان طلب AJAX
            is_ajax_request = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                request.POST.get('is_ajax') == '1'
            )
            
            # إرجاع استجابة بناءً على نوع الطلب
            if is_ajax_request:
                return JsonResponse({
                    'success': True,
                    'customer_id': customer.id,
                    'customer_name': customer.name,
                    'action': 'save_and_add_another' if 'save_and_add_another' in request.POST else 
                              'save_and_add_sale' if 'save_and_add_sale' in request.POST else 'save'
                })
            
            messages.success(request, f'تم إضافة العميل {customer.name} بنجاح')
            
            # تحديد إعادة التوجيه بناءً على زر الإرسال
            if 'save_and_add_another' in request.POST:
                return redirect('customer-create')
            elif 'save_and_add_sale' in request.POST:
                return redirect('invoice-create', customer_id=customer.id)
            else:
                return redirect('customer-detail', pk=customer.pk)
        else:
            # التعامل مع حالة وجود أخطاء
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('is_ajax') == '1':
                errors = {field: [str(e) for e in errors] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors})
            
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    else:
        # القيم المبدئية إذا تم تمريرها في الـ URL
        initial_data = {}
        for field in ['name', 'phone', 'email', 'address']:
            if request.GET.get(field):
                initial_data[field] = request.GET.get(field)
                
        form = CustomerForm(initial=initial_data)
    
    # تحضير جميع التصنيفات لعرضها في النموذج
    categories = CustomerCategory.objects.all()
    
    context = {
        'form': form,
        'categories': categories,
        'title': _('إضافة عميل جديد'),
    }
    
    # معالجة طلبات AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.GET.get('action') == 'get_form_html':
            return render(request, 'customers/includes/customer_form_fields.html', context)
        
    return render(request, 'customers/customer_form.html', context)

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    # Get customer sales
    sales = Sale.objects.filter(customer=customer).order_by('-sale_date')
    
    # Get customer payments
    payments = CustomerPayment.objects.filter(customer=customer).order_by('-payment_date')
    
        # حساب إحصائيات العميل
    sales_count = sales.count()
    total_sales = sales.aggregate(total=Sum('total_price'))['total'] or 0
    sales_items_count = sales.aggregate(count=Sum('items__quantity'))['count'] or 0
    
    # Days since last sale
    last_sale = sales.first()
    last_sale_days = 0
    if last_sale:
        last_sale_days = (timezone.now().date() - last_sale.sale_date).days
    
    # تحضير البيانات للرسومات البيانية
    # 1. بيانات المبيعات الشهرية
    sales_by_month = []
    if sales.exists():
        # الحصول على المبيعات الشهرية للسنة الحالية
        current_year = timezone.now().year
        for month in range(1, 13):
            month_sales = sales.filter(
                sale_date__year=current_year,
                sale_date__month=month
            ).aggregate(total=Sum('total_price'))['total'] or 0
            sales_by_month.append(float(month_sales))
    
    context = {
        'customer': customer,
        'sales': sales,
        'payments': payments,
        'sales_count': sales_count,
        'total_sales': total_sales,
        'sales_items_count': sales_items_count,
        'last_sale_days': last_sale_days,
        'sales_by_month': sales_by_month,
    }
    
    # إذا كان الطلب لعرض في المودال
    if request.GET.get('format') == 'modal':
        context = {
            'customer': customer,
            'sales': sales[:5],  # نعرض أحدث 5 مبيعات فقط
            'payments': payments[:5],  # نعرض أحدث 5 دفعات فقط
            'is_modal': True
        }
        return render(request, 'customers/customer_detail_modal.html', context)
    
    return render(request, 'customers/customer_detail.html', context)

@login_required
def customer_edit(request, pk):
    """تعديل بيانات عميل موجود"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            
            # تحديد ما إذا كان طلب AJAX
            is_ajax_request = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                request.POST.get('is_ajax') == '1'
            )
            
            # إرجاع استجابة بناءً على نوع الطلب
            if is_ajax_request:
                return JsonResponse({
                    'success': True,
                    'customer_id': customer.id,
                    'customer_name': customer.name
                })
            
            messages.success(request, f'تم تحديث بيانات العميل {customer.name} بنجاح')
            
            # تحديد إعادة التوجيه بناءً على زر الإرسال
            if 'save_and_add_new' in request.POST:
                return redirect('customer-create')
            else:
                return redirect('customer-detail', pk=customer.pk)
                
        else:
            # التعامل مع حالة وجود أخطاء
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('is_ajax') == '1':
                errors = {field: [str(e) for e in errors] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors})
            
            messages.error(request, 'يرجى تصحيح الأخطاء في النموذج')
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'customer': customer,
        'form': form,
    }
    
    return render(request, 'customers/customer_form.html', context)

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.delete()
        messages.success(request, _('تم حذف العميل بنجاح.'))
        return redirect('customer-list')
    
    context = {
        'customer': customer
    }
    
    return render(request, 'customers/customer_confirm_delete.html', context)

@login_required
def customer_debts(request):
    """عرض صفحة مديونية العملاء"""
    # الحصول على العملاء الذين لديهم مديونيات
    customers = Customer.objects.filter(debt__gt=0).order_by('-debt')
    
    # تصفية إضافية
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    sort_by = request.GET.get('sort_by', '-debt')
    
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) | 
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    if category_id and category_id.isdigit():
        customers = customers.filter(category_id=category_id)
    
    if sort_by:
        customers = customers.order_by(sort_by)
    
    # إحصائيات المديونية
    total_debt = customers.aggregate(total=Sum('debt'))['total'] or 0
    customers_with_debt_count = customers.count()
    exceed_limit_count = customers.filter(credit_limit__gt=0).filter(debt__gt=F('credit_limit')).count()
    
    # احصل على الفئات لفلتر البحث
    categories = CustomerCategory.objects.all()
    
    # تنفيذ الترقيم
    page_size = int(request.GET.get('page_size', 10))
    paginator = Paginator(customers, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'total_debt': total_debt,
        'customers_with_debt_count': customers_with_debt_count,
        'exceed_limit_count': exceed_limit_count,
        'categories': categories,
        'search_query': search_query,
        'category_id': category_id,
        'sort_by': sort_by,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_size': page_size,
    }
    
    return render(request, 'customers/customer_debts.html', context)

@login_required
def record_payment(request, pk):
    """تسجيل دفعة جديدة من العميل"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')
        notes = request.POST.get('notes', '')
        
        # التحقق من صحة البيانات
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, _('يجب أن يكون المبلغ أكبر من صفر'))
                return redirect('customer-debts')
                
            if amount > customer.debt:
                messages.error(request, _('المبلغ المدخل أكبر من المديونية الحالية'))
                return redirect('customer-debts')
                
            # إنشاء الدفعة
            payment = CustomerPayment.objects.create(
                customer=customer,
                amount=amount,
                payment_method=payment_method,
                payment_date=payment_date or timezone.now().date(),
                notes=notes
            )
            
            # تحديث مديونية العميل
            customer.debt -= amount
            customer.save(update_fields=['debt'])
            
            # في حالة النجاح
            messages.success(request, _(f'تم تسجيل دفعة بمبلغ {amount} ج.م من العميل {customer.name} بنجاح'))
            
        except (ValueError, InvalidOperation):
            messages.error(request, _('المبلغ غير صحيح'))
    
    return redirect('customer-debts')

@login_required
def category_list(request):
    """عرض قائمة تصنيفات العملاء مع إمكانية الإضافة والتعديل والحذف"""
    categories = CustomerCategory.objects.all().annotate(
        customer_count=Count('customers')
    )
    
    if request.method == 'POST':
        # التعامل مع تعديل التصنيف
        if 'category_id' in request.POST:
            category_id = request.POST.get('category_id')
            category = get_object_or_404(CustomerCategory, id=category_id)
            
            category.name = request.POST.get('name')
            category.color_code = request.POST.get('color_code', 'primary')
            category.description = request.POST.get('description', '')
            category.save()
            
            messages.success(request, _('تم تحديث التصنيف بنجاح'))
            return redirect('customer-categories')
            
        # التعامل مع حذف التصنيف
        elif 'delete_category' in request.POST:
            category_id = request.POST.get('category_id')
            category = get_object_or_404(CustomerCategory, id=category_id)
            category.delete()
            
            messages.success(request, _('تم حذف التصنيف بنجاح'))
            return redirect('customer-categories')
            
        # التعامل مع إضافة تصنيف جديد
        else:
            form = CustomerCategoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _('تم إضافة التصنيف بنجاح'))
                return redirect('customer-categories')
    else:
        form = CustomerCategoryForm()
        
    context = {
        'categories': categories,
        'form': form
    }
    
    return render(request, 'customers/category_list.html', context)

# إضافة العرض الخاص بحذف التصنيف
@login_required
def category_delete(request, pk):
    category = get_object_or_404(CustomerCategory, pk=pk)
    
    # التأكد من عدم استخدام التصنيف
    if category.customers.exists():
        messages.error(request, _('لا يمكن حذف التصنيف لأنه مرتبط بعملاء'))
        return redirect('customer-categories')
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, _('تم حذف التصنيف بنجاح'))
    
    return redirect('customer-categories')

@login_required
def category_create(request):
    """إضافة تصنيف عملاء جديد"""
    if request.method == 'POST':
        name = request.POST.get('name')
        color_code = request.POST.get('color_code', 'primary')
        description = request.POST.get('description', '')
        
        if not name:
            messages.error(request, _('اسم التصنيف مطلوب'))
            return redirect('category-create')
            
        if CustomerCategory.objects.filter(name=name).exists():
            messages.error(request, _('يوجد تصنيف بهذا الاسم بالفعل'))
            return redirect('category-create')
            
        category = CustomerCategory.objects.create(
            name=name,
            color_code=color_code,
            description=description
        )
        
        messages.success(request, _('تم إضافة التصنيف بنجاح'))
        
        if 'save_and_add_another' in request.POST:
            return redirect('category-create')
        else:
            return redirect('customer-categories')
            
    return render(request, 'customers/customer_category_create.html')

@login_required
def get_customer_data(request, pk):
    """الحصول على بيانات العميل للتحرير في المودال"""
    customer = get_object_or_404(Customer, pk=pk)
    
    data = {
        'success': True,
        'customer': {
            'id': customer.id,
            'name': customer.name,
            'code': customer.code,  # إضافة كود العميل
            'phone': customer.phone,
            'email': customer.email,
            'address': customer.address,
            'status': customer.status,
            'category_id': customer.category_id,
            'credit_limit': float(customer.credit_limit),
            'debt': float(customer.debt),
            'total_sales': float(customer.total_sales),
        }
    }
    
    return JsonResponse(data)

@login_required
def customer_categories(request):
    """عرض وإدارة تصنيفات العملاء"""
    categories = CustomerCategory.objects.all().order_by('name')
    
    # احصائيات التصنيفات
    for category in categories:
        category.customer_count = Customer.objects.filter(category=category).count()
        category.total_sales = Customer.objects.filter(category=category).aggregate(total=Sum('total_sales'))['total'] or 0
        category.total_debt = Customer.objects.filter(category=category).aggregate(total=Sum('debt'))['total'] or 0
    
    context = {
        'categories': categories,
        'total_categories': categories.count(),
    }
    
    return render(request, 'customers/customer_categories.html', context)

@login_required
def customer_category_create(request):
    """إضافة تصنيف عميل جديد (يدعم AJAX و HTTP العادي)"""
    if request.method == 'POST':
        # التعامل مع طلبات AJAX (عندما يكون المحتوى JSON)
        if request.headers.get('Content-Type') == 'application/json':
            import json
            data = json.loads(request.body)
            form = CustomerCategoryForm({
                'name': data.get('name'),
                'description': data.get('description'),
                'color_code': data.get('color_code', 'primary')
            })
            
            if form.is_valid():
                category = form.save()
                return JsonResponse({
                    'success': True,
                    'id': category.id,
                    'name': category.name
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'بيانات غير صالحة',
                    'errors': form.errors
                })
        
        # التعامل مع طلبات HTTP العادية (النموذج)
        else:
            form = CustomerCategoryForm(request.POST)
            if form.is_valid():
                category = form.save()
                messages.success(request, _(f'تم إضافة التصنيف {category.name} بنجاح'))
                return redirect('customer-categories')
            else:
                messages.error(request, _('يرجى تصحيح الأخطاء الموجودة في النموذج.'))
    else:
        form = CustomerCategoryForm()
    
    context = {
        'form': form,
        'title': _('إضافة تصنيف عميل جديد'),
    }
    
    return render(request, 'customers/customer_category_form.html', context)

@login_required
def customer_category_edit(request, pk):
    """تعديل تصنيف عميل"""
    category = get_object_or_404(CustomerCategory, pk=pk)
    if request.method == 'POST':
        form = CustomerCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            
            # إذا كان طلب AJAX، إرجاع استجابة JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'category_id': category.id,
                    'category_name': category.name
                })
            
            messages.success(request, _(f'تم تحديث تصنيف العميل {category.name} بنجاح.'))
            return redirect('customer-categories')
        else:
            # إذا كان طلب AJAX، إرجاع رسائل الخطأ
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {field: errors[0] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors})
            
            messages.error(request, _('يرجى تصحيح الأخطاء الموجودة في النموذج.'))
    else:
        form = CustomerCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': _('تعديل تصنيف العميل'),
    }
    
    return render(request, 'customers/customer_category_form.html', context)

@login_required
def customer_category_delete(request, pk):
    """حذف تصنيف عميل"""
    category = get_object_or_404(CustomerCategory, pk=pk)
    if request.method == 'POST':
        # التحقق من عدم وجود عملاء مرتبطين بهذا التصنيف
        if Customer.objects.filter(category=category).exists():
            messages.error(request, _('لا يمكن حذف التصنيف لأنه مرتبط بعملاء.'))
            return redirect('customer-categories')
        
        name = category.name
        category.delete()
        messages.success(request, _(f'تم حذف تصنيف العميل {name} بنجاح.'))
        return redirect('customer-categories')
    
    context = {
        'category': category,
        'customers_count': Customer.objects.filter(category=category).count(),
    }
    
    return render(request, 'customers/customer_category_confirm_delete.html', context)

# تأكد من إضافة هذه السطور في أعلى الملف إذا لم تكن موجودة
from django.db.models import Q, F, Sum
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Func

# ... existing code ...

@login_required
def check_name_similarity(request):
    """التحقق من تشابه اسم العميل مع العملاء الموجودين"""
    customer_name = request.GET.get('name', '').strip()
    threshold = float(request.GET.get('threshold', '0.8'))
    
    if not customer_name:
        return JsonResponse({'similar_customers': []})
    
    # الحصول على جميع العملاء للمقارنة
    customers = Customer.objects.exclude(name='').values('id', 'name', 'phone')
    similar_customers = []
    
    import difflib
    
    # استخدام مكتبة difflib لحساب التشابه
    for customer in customers:
        # حساب نسبة التشابه
        similarity = difflib.SequenceMatcher(None, customer_name.lower(), customer['name'].lower()).ratio()
        
        # إذا كانت نسبة التشابه أعلى من الحد المطلوب
        if similarity >= threshold:
            customer_data = {
                'id': customer['id'],
                'name': customer['name'],
                'phone': customer['phone'] or '',
                'similarity': round(similarity * 100, 1)  # تحويل إلى نسبة مئوية
            }
            similar_customers.append(customer_data)
    
    # ترتيب العملاء حسب نسبة التشابه (تنازلياً)
    similar_customers.sort(key=lambda x: x['similarity'], reverse=True)
    
    return JsonResponse({'similar_customers': similar_customers})

# ... existing code ...
