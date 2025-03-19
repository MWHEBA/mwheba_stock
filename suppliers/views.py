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
from .models import Supplier, SupplierCategory
from .forms import SupplierForm, SupplierSearchForm, SupplierCategoryForm
from purchases.models import Purchase, Payment

@login_required
def supplier_list(request):
    """عرض قائمة الموردين مع خيارات بحث وتصفية متقدمة"""
    # إنشاء نموذج البحث مع بيانات الطلب
    form = SupplierSearchForm(request.GET)
    
    # الحصول على المعلمات
    search_query = request.GET.get('search', '')
    debt_status = request.GET.get('payment_status', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    sort_by = request.GET.get('sort_by', '-created_at')
    
    # قاعدة بيانات الموردين
    suppliers = Supplier.objects.all()
    
    # تطبيق البحث
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) | 
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    # تصفية حسب التصنيف
    if category_id and category_id.isdigit():
        suppliers = suppliers.filter(category_id=category_id)
    
    # تصفية حسب الحالة
    if status:
        suppliers = suppliers.filter(status=status)
    
    # تصفية حسب حالة السداد
    if debt_status == 'with_debts':
        suppliers = suppliers.filter(balance__gt=0)
    elif debt_status == 'no_debts':
        suppliers = suppliers.filter(balance__lte=0)
    elif debt_status == 'exceed_limit':
        # الموردين الذين تجاوزت مستحقاتهم حد الائتمان
        suppliers = suppliers.filter(credit_limit__gt=0).filter(balance__gt=F('credit_limit'))
    
    # الترتيب
    if sort_by:
        suppliers = suppliers.order_by(sort_by)
    
    # حساب الإحصاءات
    supplier_count = suppliers.count()
    total_purchases = suppliers.aggregate(total=Sum('total_purchases'))['total'] or 0
    total_balance = suppliers.aggregate(total=Sum('balance'))['total'] or 0
    
    # الموردين النشطين خلال الـ 30 يوم الماضية
    thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
    active_suppliers = suppliers.filter(last_purchase_date__gte=thirty_days_ago).count()
    
    # تقسيم الصفحات
    page_size = int(request.GET.get('page_size', 10))
    paginator = Paginator(suppliers, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # الحصول على جميع تصنيفات الموردين لعرضها في الواجهة
    categories = SupplierCategory.objects.all()
    
    context = {
        'suppliers': page_obj,
        'form': form,
        'categories': categories,
        'total_suppliers': supplier_count,
        'active_suppliers': active_suppliers,
        'total_purchases': total_purchases,
        'total_balance': total_balance,
        'search_query': search_query,
        'debt_status': debt_status,
        'category_id': category_id,
        'status': status,
        'sort_by': sort_by,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_size': page_size,
    }
    
    # إذا كان الطلب يخص التصدير
    export_format = request.GET.get('export')
    if export_format:
        return export_suppliers(request, suppliers, export_format)
    
    return render(request, 'suppliers/supplier_list.html', context)

# دالة مساعدة لتصدير بيانات الموردين
def export_suppliers(request, suppliers, export_format):
    """تصدير بيانات الموردين بتنسيقات مختلفة"""
    from django.http import HttpResponse
    import csv
    from datetime import datetime
    
    filename = f"suppliers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if export_format == 'csv':  # تم تغيير الشرط من 'excel' إلى 'csv'
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        # استخدام UTF-8-sig لدعم الأحرف العربية في Excel
        response.write('\ufeff'.encode('utf8'))
        
        writer = csv.writer(response)
        writer.writerow(['الاسم', 'الهاتف', 'البريد الإلكتروني', 'التصنيف', 'المستحقات', 'الحالة'])
        
        for supplier in suppliers:
            writer.writerow([
                supplier.name,
                supplier.phone or '-',
                supplier.email or '-',
                supplier.category.name if supplier.category else '-',
                supplier.balance,
                supplier.get_status_display(),
            ])
        
        return response
    
    elif export_format == 'pdf':
        # TODO: تنفيذ تصدير PDF باستخدام مكتبة مناسبة
        # سنقوم بتنفيذ هذا لاحقاً
        return HttpResponse("سيتم دعم تصدير PDF قريباً")
    
    elif export_format == 'print':
        context = {
            'suppliers': suppliers,
            'today': datetime.now(),
            'title': 'قائمة الموردين'
        }
        return render(request, 'suppliers/print_supplier_list.html', context)
    
    return redirect('supplier-list')

@login_required
def supplier_create(request):
    """إضافة مورد جديد مع التحقق من البيانات"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            
            # إذا كان طلب AJAX، إرجاع استجابة JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('is_ajax') == '1':
                return JsonResponse({
                    'success': True,
                    'supplier_id': supplier.id,
                    'supplier_name': supplier.name
                })
            
            messages.success(request, _(f'تم إضافة المورد {supplier.name} بنجاح'))
            
            # تحديد صفحة التحويل
            if 'save_and_add_another' in request.POST:
                return redirect('supplier-create')
            elif 'save_and_add_purchase' in request.POST:
                return redirect('purchase-create')
            else:
                return redirect('supplier-detail', pk=supplier.pk)
        else:
            # إذا كان طلب AJAX، إرجاع رسائل الخطأ بشكل أكثر تفصيلاً
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('is_ajax') == '1':
                # تحسين استرجاع الأخطاء
                errors_dict = {}
                for field, errors in form.errors.items():
                    errors_dict[field] = [str(error) for error in errors]
                
                # إضافة معلومات تصحيح نصية للتشخيص
                return JsonResponse({
                    'success': False, 
                    'errors': errors_dict,
                    'status': 'form_invalid',
                    'form_data': {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
                })
            
            # في حالة طلب عادي غير AJAX
            messages.error(request, _('يرجى تصحيح الأخطاء في النموذج'))
    else:
        # القيم المبدئية إذا تم تمريرها في الـ URL
        initial_data = {}
        for field in ['name', 'phone', 'email', 'address']:
            if request.GET.get(field):
                initial_data[field] = request.GET.get(field)
                
        form = SupplierForm(initial=initial_data)
    
    # تحضير جميع التصنيفات لعرضها في النموذج
    categories = SupplierCategory.objects.all()
    
    context = {
        'form': form,
        'categories': categories,
        'title': _('إضافة مورد جديد'),
    }
    
    # معالجة طلبات AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.GET.get('action') == 'get_form_html':
            return render(request, 'suppliers/includes/supplier_form_fields.html', context)
        
    return render(request, 'suppliers/supplier_form.html', context)

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    # Get supplier purchases
    purchases = Purchase.objects.filter(supplier=supplier).order_by('-purchase_date')
    
    # Get supplier payments
    payments = Payment.objects.filter(supplier=supplier).order_by('-payment_date')
    
    # حساب إحصائيات المورد
    purchases_count = purchases.count()
    total_purchases = purchases.aggregate(total=Sum('total_amount'))['total'] or 0
    unique_products = Purchase.objects.filter(supplier=supplier).values('items__product').distinct().count()
    
    # Days since last purchase
    last_purchase = purchases.first()
    last_purchase_days = 0
    if last_purchase:
        last_purchase_days = (timezone.now().date() - last_purchase.purchase_date).days
    
    context = {
        'supplier': supplier,
        'purchases': purchases,
        'payments': payments,
        'purchases_count': purchases_count,
        'total_purchases': total_purchases,
        'unique_products': unique_products,
        'last_purchase_days': last_purchase_days,
    }
    
    # إذا كان الطلب لعرض في المودال
    if request.GET.get('format') == 'modal':
        context = {
            'supplier': supplier,
            'purchases': purchases[:5],  # نعرض أحدث 5 مشتريات فقط
            'payments': payments[:5],  # نعرض أحدث 5 دفعات فقط
            'purchases_count': purchases_count,
            'total_purchases': total_purchases,
            'unique_products': unique_products,
            'is_modal': True
        }
        return render(request, 'suppliers/supplier_detail_modal.html', context)
    
    return render(request, 'suppliers/supplier_detail.html', context)

@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث بيانات المورد {supplier.name} بنجاح.')
            return redirect('supplier-detail', pk=supplier.pk)
    else:
        form = SupplierForm(instance=supplier)
    
    context = {
        'form': form,
        'supplier': supplier,
        'is_edit': True,
    }
    return render(request, 'suppliers/supplier_form.html', context)

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, _('تم حذف المورد بنجاح.'))
        return redirect('supplier-list')
    
    context = {
        'supplier': supplier
    }
    
    return render(request, 'suppliers/supplier_confirm_delete.html', context)

@login_required
def record_payment(request, pk):
    """تسجيل دفعة جديدة للمورد"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
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
                return redirect('supplier-list')
                
            if amount > supplier.balance:
                messages.error(request, _('المبلغ المدخل أكبر من المستحقات الحالية'))
                return redirect('supplier-list')
                
            # إنشاء الدفعة
            payment = Payment.objects.create(
                supplier=supplier,
                amount=amount,
                payment_method=payment_method,
                payment_date=payment_date or timezone.now().date(),
                notes=notes
            )
            
            # تحديث مستحقات المورد
            supplier.balance -= amount
            supplier.save(update_fields=['balance'])
            
            # في حالة النجاح
            messages.success(request, _(f'تم تسجيل دفعة بمبلغ {amount} ج.م للمورد {supplier.name} بنجاح'))
            
        except (ValueError, InvalidOperation):
            messages.error(request, _('المبلغ غير صحيح'))
    
    return redirect('supplier-list')

@login_required
def supplier_modal_detail(request, pk):
    """عرض تفاصيل المورد في مودال"""
    supplier = get_object_or_404(Supplier, pk=pk)
    purchases = Purchase.objects.filter(supplier=supplier).order_by('-purchase_date')[:3]
    
    context = {
        'supplier': supplier,
        'purchases': purchases,
        'purchases_count': Purchase.objects.filter(supplier=supplier).count(),
        'unique_products': Purchase.objects.filter(supplier=supplier).values('items__product').distinct().count(),
    }
    
    return render(request, 'suppliers/includes/modals/view_modal.html', context)

@login_required
def supplier_modal_edit(request, pk):
    """عرض نموذج تعديل المورد في مودال"""
    supplier = get_object_or_404(Supplier, pk=pk)
    categories = SupplierCategory.objects.all()
    
    context = {
        'supplier': supplier,
        'categories': categories,
    }
    
    return render(request, 'suppliers/includes/modals/edit_modal.html', context)

@login_required
def supplier_payment_form(request, pk):
    """عرض نموذج تسجيل دفعة للمورد في مودال"""
    supplier = get_object_or_404(Supplier, pk=pk)
    unpaid_purchases = Purchase.objects.filter(supplier=supplier, status__in=['pending', 'partially_paid'])
    
    context = {
        'supplier': supplier,
        'unpaid_purchases': unpaid_purchases,
    }
    
    return render(request, 'suppliers/includes/modals/payment_modal.html', context)

@login_required
def get_supplier_data(request, pk):
    """الحصول على بيانات المورد للتحرير في المودال"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    data = {
        'success': True,
        'supplier': {
            'id': supplier.id,
            'name': supplier.name,
            'code': supplier.code,
            'phone': supplier.phone,
            'email': supplier.email,
            'address': supplier.address,
            'status': supplier.status,
            'category_id': supplier.category_id,
            'credit_limit': float(supplier.credit_limit),
            'balance': float(supplier.balance),
            'total_purchases': float(supplier.total_purchases),
        }
    }
    
    return JsonResponse(data)

@login_required
def supplier_debts(request):
    """عرض صفحة مستحقات الموردين"""
    # الحصول على الموردين الذين لديهم مستحقات
    suppliers = Supplier.objects.filter(balance__gt=0).order_by('-balance')
    
    # تصفية إضافية
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    sort_by = request.GET.get('sort_by', '-balance')
    
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) | 
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    if category_id and category_id.isdigit():
        suppliers = suppliers.filter(category_id=category_id)
    
    if sort_by:
        suppliers = suppliers.order_by(sort_by)
    
    # إحصائيات المستحقات
    total_balance = suppliers.aggregate(total=Sum('balance'))['total'] or 0
    suppliers_with_debts_count = suppliers.count()
    exceed_limit_count = suppliers.filter(credit_limit__gt=0).filter(balance__gt=F('credit_limit')).count()
    
    # احصل على الفئات لفلتر البحث
    categories = SupplierCategory.objects.all()
    
    # تنفيذ الترقيم
    page_size = int(request.GET.get('page_size', 10))
    paginator = Paginator(suppliers, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'suppliers': page_obj,
        'total_balance': total_balance,
        'suppliers_with_debts_count': suppliers_with_debts_count,
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
    
    return render(request, 'suppliers/supplier_debts.html', context)

@login_required
def supplier_categories(request):
    """عرض وإدارة تصنيفات الموردين"""
    categories = SupplierCategory.objects.all().order_by('name')
    
    # احصائيات التصنيفات
    for category in categories:
        category.supplier_count = Supplier.objects.filter(category=category).count()
        category.total_purchases = Supplier.objects.filter(category=category).aggregate(total=Sum('total_purchases'))['total'] or 0
        category.total_balance = Supplier.objects.filter(category=category).aggregate(total=Sum('balance'))['total'] or 0
    
    context = {
        'categories': categories,
        'total_categories': categories.count(),
    }
    
    return render(request, 'suppliers/supplier_categories.html', context)

@login_required
def supplier_category_create(request):
    """إضافة تصنيف مورد جديد"""
    if request.method == 'POST':
        form = SupplierCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            
            # إذا كان طلب AJAX، إرجاع استجابة JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'category_id': category.id,
                    'category_name': category.name
                })
            
            messages.success(request, _(f'تم إضافة التصنيف {category.name} بنجاح'))
            return redirect('supplier-categories')
        else:
            # إذا كان طلب AJAX، إرجاع رسائل الخطأ
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {field: errors[0] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors})
            
            messages.error(request, _('يرجى تصحيح الأخطاء الموجودة في النموذج.'))
    else:
        form = SupplierCategoryForm()
    
    context = {
        'form': form,
        'title': _('إضافة تصنيف مورد جديد'),
    }
    
    return render(request, 'suppliers/supplier_category_form.html', context)

@login_required
def supplier_category_edit(request, pk):
    """تعديل تصنيف مورد"""
    category = get_object_or_404(SupplierCategory, pk=pk)
    if request.method == 'POST':
        form = SupplierCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            
            # إذا كان طلب AJAX، إرجاع استجابة JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'category_id': category.id,
                    'category_name': category.name
                })
            
            messages.success(request, _(f'تم تحديث تصنيف المورد {category.name} بنجاح.'))
            return redirect('supplier-categories')
        else:
            # إذا كان طلب AJAX، إرجاع رسائل الخطأ
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {field: errors[0] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors})
            
            messages.error(request, _('يرجى تصحيح الأخطاء الموجودة في النموذج.'))
    else:
        form = SupplierCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': _('تعديل تصنيف المورد'),
    }
    
    return render(request, 'suppliers/supplier_category_form.html', context)

@login_required
def supplier_category_delete(request, pk):
    """حذف تصنيف مورد"""
    category = get_object_or_404(SupplierCategory, pk=pk)
    if request.method == 'POST':
        # التحقق من عدم وجود موردين مرتبطين بهذا التصنيف
        if Supplier.objects.filter(category=category).exists():
            messages.error(request, _('لا يمكن حذف التصنيف لأنه مرتبط بموردين.'))
            return redirect('supplier-categories')
        
        name = category.name
        category.delete()
        messages.success(request, _(f'تم حذف تصنيف المورد {name} بنجاح.'))
        return redirect('supplier-categories')
    
    context = {
        'category': category,
        'suppliers_count': Supplier.objects.filter(category=category).count(),
    }
    
    return render(request, 'suppliers/supplier_category_confirm_delete.html', context)
