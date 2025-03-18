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
    
    if export_format == 'excel':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        # استخدام UTF-8-sig لدعم الأحرف العربية في Excel
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
            messages.success(request, _(f'تم إضافة العميل {customer.name} بنجاح'))
            
            # تحديد صفحة التحويل
            if 'save_and_add_another' in request.POST:
                return redirect('customer-create')
            elif 'save_and_add_sale' in request.POST:
                return redirect('sale-create')
            else:
                return redirect('customer-detail', pk=customer.pk)
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
    
    # Calculate statistics
    sales_count = sales.count()
    total_sales = sales.aggregate(total=Sum('total_price'))['total'] or 0
    sales_items_count = sales.aggregate(count=Sum('items__quantity'))['count'] or 0
    
    # Days since last sale
    last_sale = sales.first()
    last_sale_days = 0
    if last_sale:
        last_sale_days = (timezone.now().date() - last_sale.sale_date).days
    
    context = {
        'customer': customer,
        'sales': sales,
        'payments': payments,
        'sales_count': sales_count,
        'total_sales': total_sales,
        'sales_items_count': sales_items_count,
        'last_sale_days': last_sale_days,
    }
    
    return render(request, 'customers/customer_detail.html', context)

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث بيانات العميل بنجاح.'))
            return redirect('customer-detail', pk=customer.pk)
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
    """عرض صفحة مديونيات العملاء والتحليلات الخاصة بها"""
    # الحصول على ترتيب العرض
    sort_param = request.GET.get('sort', 'debt_high')
    
    # العملاء المدينين مع الإحصاءات
    customers_query = Customer.objects.filter(debt__gt=0).annotate(
        pending_sales_count=Count('sales', filter=Q(sales__status__in=['unpaid', 'partially_paid'])),
        # الحصول على تاريخ آخر دفعة من العميل
        last_payment_date=Subquery(
            CustomerPayment.objects.filter(customer=OuterRef('pk'))
            .order_by('-payment_date')
            .values('payment_date')[:1]
        )
    )
    
    # تطبيق الترتيب
    if sort_param == 'debt_high':
        customers_with_debts = customers_query.order_by('-debt')
    elif sort_param == 'debt_low':
        customers_with_debts = customers_query.order_by('debt')
    elif sort_param == 'name':
        customers_with_debts = customers_query.order_by('name')
    elif sort_param == 'overdue':
        # الترتيب حسب تاريخ آخر دفعة (الأقدم أولاً)
        customers_with_debts = customers_query.order_by('last_payment_date')
    else:
        customers_with_debts = customers_query.order_by('-debt')
    
    # حساب إحصاءات المديونية
    debt_stats = customers_query.aggregate(
        total=Sum('debt'),
        avg=Avg('debt'),
        max=Max('debt')
    )
    
    # حساب المديونيات المتأخرة (أكثر من 30 يوم)
    thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
    overdue_debt = customers_query.filter(
        last_payment_date__lt=thirty_days_ago
    ).aggregate(total=Sum('debt'))['total'] or 0
    
    # إعداد بيانات الرسم البياني حسب التصنيف
    category_data = list(customers_query.values('category__name').annotate(total=Sum('debt')).order_by('-total'))
    
    context = {
        'customers_with_debts': customers_with_debts,
        'total_debt': debt_stats['total'] or 0,
        'avg_debt': debt_stats['avg'] or 0,
        'max_debt': debt_stats['max'] or 0,
        'overdue_debt': overdue_debt,
        'today_date': timezone.now().date(),
        # تجهيز بيانات الرسم البياني بصيغة JSON
        'chart_data': {
            'categories': [item['category__name'] or 'بدون تصنيف' for item in category_data],
            'values': [float(item['total']) for item in category_data]
        }
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
def category_create_ajax(request):
    """معالجة طلب إنشاء تصنيف جديد للعملاء عبر AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            color_code = data.get('color_code', 'primary')
            description = data.get('description', '')
            
            # التحقق من وجود الاسم
            if not name:
                return JsonResponse({'success': False, 'error': _('اسم التصنيف مطلوب')})
                
            # التحقق من عدم تكرار الاسم
            if CustomerCategory.objects.filter(name=name).exists():
                return JsonResponse({'success': False, 'error': _('يوجد تصنيف بهذا الاسم بالفعل')})
                
            # إنشاء التصنيف
            category = CustomerCategory.objects.create(
                name=name,
                color_code=color_code,
                description=description
            )
            
            return JsonResponse({
                'success': True, 
                'id': category.id, 
                'name': category.name,
                'color': category.color_code
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': _('بيانات غير صالحة')}, status=400)
    
    return JsonResponse({'success': False, 'error': _('طريقة الطلب غير مدعومة')}, status=405)

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
