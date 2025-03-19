from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta

@login_required
def dashboard(request):
    """
    عرض لوحة التحكم الرئيسية مع إحصائيات ومؤشرات الأداء الرئيسية
    """
    # Get references to models from other apps if they exist
    try:
        from products.models import Product
        products_count = Product.objects.count()
        low_stock_count = Product.objects.filter(stock_quantity__lte=F('min_stock_level')).count()
    except (ImportError, ModuleNotFoundError):
        products_count = 0
        low_stock_count = 0
    
    try:
        from customers.models import Customer
        customers_count = Customer.objects.count()
        customers_with_debt = Customer.objects.filter(debt__gt=0).count()
    except (ImportError, ModuleNotFoundError):
        customers_count = 0
        customers_with_debt = 0
        
    try:
        from suppliers.models import Supplier
        suppliers_count = Supplier.objects.count()
    except (ImportError, ModuleNotFoundError):
        suppliers_count = 0
    
    try:
        from sales.models import Sale
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        last_month_start = (first_day_of_month - timedelta(days=1)).replace(day=1)
        
        # Sales statistics
        total_sales = Sale.objects.count()
        sales_today = Sale.objects.filter(sale_date=today).count()
        sales_this_month = Sale.objects.filter(sale_date__gte=first_day_of_month).count()
        sales_last_month = Sale.objects.filter(sale_date__gte=last_month_start, sale_date__lt=first_day_of_month).count()
        
        # Revenue statistics
        total_revenue = Sale.objects.aggregate(total=Sum('total_price'))['total'] or 0
        revenue_today = Sale.objects.filter(sale_date=today).aggregate(total=Sum('total_price'))['total'] or 0
        revenue_this_month = Sale.objects.filter(sale_date__gte=first_day_of_month).aggregate(total=Sum('total_price'))['total'] or 0
        revenue_last_month = Sale.objects.filter(sale_date__gte=last_month_start, sale_date__lt=first_day_of_month).aggregate(total=Sum('total_price'))['total'] or 0
    except (ImportError, ModuleNotFoundError):
        total_sales = 0
        sales_today = 0
        sales_this_month = 0
        sales_last_month = 0
        total_revenue = 0
        revenue_today = 0
        revenue_this_month = 0
        revenue_last_month = 0
    
    # Prepare context for the template
    context = {
        'products_count': products_count,
        'low_stock_count': low_stock_count,
        'customers_count': customers_count,
        'customers_with_debt': customers_with_debt,
        'suppliers_count': suppliers_count,
        'total_sales': total_sales,
        'sales_today': sales_today,
        'sales_this_month': sales_this_month,
        'sales_last_month': sales_last_month,
        'total_revenue': total_revenue,
        'revenue_today': revenue_today,
        'revenue_this_month': revenue_this_month,
        'revenue_last_month': revenue_last_month,
    }
    
    return render(request, 'dashboard/index.html', context)
