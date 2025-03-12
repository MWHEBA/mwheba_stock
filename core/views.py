import csv
import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum, Count, F, Q, ExpressionWrapper, DecimalField, Value, Avg
from django.db.models.functions import TruncMonth, TruncDay, Coalesce
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

from inventory.models import (
    Product, Stock, Category, Supplier, Client, PurchaseOrder, Order,
    PurchaseOrderItem, OrderItem, SupplierPayment, ClientPayment,
    CompanyProfile, ExpenseCategory, Expense, FinancialAccount,
    Transaction, UserProfile, StorageLocation
)
from inventory.forms import (
    SupplierForm, ClientForm, ProductForm, CategoryForm, StorageLocationForm,
    PurchaseOrderForm, PurchaseOrderItemFormset, OrderForm, OrderItemFormset,
    SupplierPaymentForm, ClientPaymentForm, CompanyProfileForm, ExpenseCategoryForm,
    ExpenseForm, FinancialAccountForm, TransactionForm, UserProfileForm,
    UserRegistrationForm, DateRangeForm
)

# Stock Report
@login_required
def stock_report(request):
    form = DateRangeForm(request.GET or None)
    
    # Default to last 30 days if no date range provided
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
    
    stock_entries = Stock.objects.filter(
        date_received__gte=start_date,
        date_received__lte=end_date
    ).order_by('-date_received')
    
    total_received = stock_entries.aggregate(total_received=Sum('quantity_received'))['total_received'] or 0
    total_sold = stock_entries.aggregate(total_sold=Sum('quantity_sold'))['total_sold'] or 0
    
    # Group by product for summary
    product_summary = stock_entries.values(
        'product__name'
    ).annotate(
        total_received=Sum('quantity_received'),
        total_sold=Sum('quantity_sold'),
        current_stock=Sum('quantity_received') - Sum('quantity_sold')
    ).order_by('product__name')
    
    context = {
        'form': form,
        'stock_entries': stock_entries,
        'product_summary': product_summary,
        'total_received': total_received,
        'total_sold': total_sold,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'inventory/stock_report.html', context)

# Sales Report
@login_required
def sales_report(request):
    form = DateRangeForm(request.GET or None)
    
    # Default to last 30 days if no date range provided
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
    
    # Get orders in date range
    orders = Order.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    )
    
    # Calculate totals
    total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    total_orders = orders.count()
    
    # Sales by product
    sales_by_product = OrderItem.objects.filter(
        order__order_date__gte=start_date,
        order__order_date__lte=end_date
    ).values(
        'product__name'
    ).annotate(
        quantity_sold=Sum('quantity'),
        total_sales=Sum(F('quantity') * F('price')),
        profit=Sum((F('price') - F('product__cost_price')) * F('quantity'))
    ).order_by('-total_sales')
    
    # Sales by client
    sales_by_client = Order.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    ).values(
        'client__name'
    ).annotate(
        order_count=Count('id'),
        total_sales=Sum('total_amount')
    ).order_by('-total_sales')
    
    # Daily sales for chart
    daily_sales = Order.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    ).annotate(
        day=TruncDay('order_date')
    ).values('day').annotate(
        total=Sum('total_amount')
    ).order_by('day')
    
    # Format for Chart.js
    days = []
    sales_data = []
    for entry in daily_sales:
        days.append(entry['day'].strftime('%Y-%m-%d'))
        sales_data.append(float(entry['total']))
    
    context = {
        'form': form,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'sales_by_product': sales_by_product,
        'sales_by_client': sales_by_client,
        'start_date': start_date,
        'end_date': end_date,
        'days': json.dumps(days),
        'sales_data': json.dumps(sales_data),
    }
    
    return render(request, 'inventory/sales_report.html', context)

# Profit and Loss Report
@login_required
def profit_loss_report(request):
    form = DateRangeForm(request.GET or None)
    
    # Default to last 30 days if no date range provided
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
    
    # Revenue (Sales)
    total_sales = Order.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Cost of Goods Sold
    cogs = OrderItem.objects.filter(
        order__order_date__gte=start_date,
        order__order_date__lte=end_date
    ).aggregate(
        total=Sum(F('product__cost_price') * F('quantity'))
    )['total'] or 0
    
    # Gross Profit
    gross_profit = total_sales - cogs
    
    # Expenses
    expenses = Expense.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    )
    
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Expenses by category
    expenses_by_category = expenses.values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Net Profit
    net_profit = gross_profit - total_expenses
    
    # Monthly profit for chart
    monthly_profit = []
    for i in range(6):
        month_end = end_date.replace(day=1) - timedelta(days=1) if i > 0 else end_date
        month_start = month_end.replace(day=1)
        
        month_sales = Order.objects.filter(
            order_date__gte=month_start,
            order_date__lte=month_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        month_cogs = OrderItem.objects.filter(
            order__order_date__gte=month_start,
            order__order_date__lte=month_end
        ).aggregate(
            total=Sum(F('product__cost_price') * F('quantity'))
        )['total'] or 0
        
        month_expenses = Expense.objects.filter(
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        month_profit = month_sales - month_cogs - month_expenses
        
        monthly_profit.append({
            'month': month_start.strftime('%b %Y'),
            'profit': float(month_profit)
        })
    
    # Reverse to show oldest to newest
    monthly_profit.reverse()
    
    # Format for Chart.js
    profit_months = [item['month'] for item in monthly_profit]
    profit_data = [item['profit'] for item in monthly_profit]
    
    context = {
        'form': form,
        'total_sales': total_sales,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'expenses_by_category': expenses_by_category,
        'net_profit': net_profit,
        'start_date': start_date,
        'end_date': end_date,
        'profit_months': json.dumps(profit_months),
        'profit_data': json.dumps(profit_data),
    }
    
    return render(request, 'inventory/profit_loss_report.html', context)

# Stock Movement Report
@login_required
def stock_movement_report(request):
    form = DateRangeForm(request.GET or None)
    
    # Default to last 7 days if no date range provided
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    
    start_date = last_week
    end_date = today
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
    
    # Query stock movements for the specified date range
    stock_movements = Stock.objects.filter(
        date_received__gte=start_date,
        date_received__lte=end_date
    ).order_by('date_received')
    
    # Group by product and stock type
    movement_summary = stock_movements.values(
        'product__name', 'stock_type'
    ).annotate(
        total_quantity=Sum('quantity_received') + Sum('quantity_sold')
    ).order_by('product__name', 'stock_type')
    
    # Group by location
    location_summary = stock_movements.values(
        'location__name'
    ).annotate(
        received=Sum('quantity_received'),
        sold=Sum('quantity_sold')
    ).order_by('location__name')
    
    context = {
        'form': form,
        'stock_movements': stock_movements,
        'movement_summary': movement_summary,
        'location_summary': location_summary,
        'start_date': start_date,
        'end_date': end_date,
        'date_range': f'{start_date.strftime("%Y-%m-%d")} - {end_date.strftime("%Y-%m-%d")}',
    }
    
    return render(request, 'inventory/stock_movement_report.html', context)

# Export Stock Report as CSV
@login_required
def export_stock_report(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to all data if no date range provided
    stock_entries = Stock.objects.all()
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            stock_entries = stock_entries.filter(
                date_received__gte=start_date,
                date_received__lte=end_date
            )
        except ValueError:
            pass
    
    # Create the response object with the correct content type for CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_report.csv"'
    
    # Set the correct encoding to handle Arabic characters
    response.charset = 'utf-8-sig'  # This ensures UTF-8 with BOM for better compatibility
    
    # Create the CSV writer
    writer = csv.writer(response)
    
    # Write the headers
    writer.writerow(['Product', 'Quantity Received', 'Quantity Sold', 'Date Received', 'Stock Type', 'Location', 'Notes', 'Supplier'])
    
    # Write the data rows
    for entry in stock_entries:
        writer.writerow([
            entry.product.name,
            entry.quantity_received,
            entry.quantity_sold,
            entry.date_received,
            entry.stock_type,
            entry.location.name if entry.location else 'N/A',
            entry.notes or '',
            entry.product.supplier.name if entry.product.supplier else 'N/A'
        ])
    
    return response

# Export Sales Report as CSV
@login_required
def export_sales_report(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to all data if no date range provided
    orders = Order.objects.all()
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            orders = orders.filter(
                order_date__gte=start_date,
                order_date__lte=end_date
            )
        except ValueError:
            pass
    
    # Create the response object
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    response.charset = 'utf-8-sig'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow(['Invoice Number', 'Client', 'Date', 'Status', 'Discount', 'Tax', 'Shipping', 'Total Amount', 'Profit'])
    
    # Write data rows
    for order in orders:
        writer.writerow([
            order.invoice_number,
            order.client.name,
            order.order_date,
            order.status,
            order.discount_amount,
            order.tax_percentage,
            order.shipping_cost,
            order.total_amount,
            order.get_profit()
        ])
    
    return response

# Export Stock Movement Report as CSV
@login_required
def export_stock_movement_report(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to all data if no date range provided
    stock_movements = Stock.objects.all()
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            stock_movements = stock_movements.filter(
                date_received__gte=start_date,
                date_received__lte=end_date
            )
        except ValueError:
            pass
    
    # Create the response object with the correct content type for CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_movement_report.csv"'
    
    # Set the correct encoding to handle Arabic characters
    response.charset = 'utf-8-sig'  # This ensures UTF-8 with BOM for better compatibility
    
    # Create the CSV writer
    writer = csv.writer(response)
    
    # Write the headers
    writer.writerow(['Product', 'Movement Type', 'Quantity', 'Date', 'Location', 'Notes'])
    
    # Write the data rows
    for movement in stock_movements:
        writer.writerow([
            movement.product.name,
            movement.stock_type,
            movement.quantity_received if movement.stock_type == 'received' else movement.quantity_sold,
            movement.date_received,
            movement.location.name if movement.location else 'N/A',
            movement.notes or ''
        ])
    
    return response

# Export Profit/Loss Report as CSV
@login_required
def export_profit_loss_report(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Default to last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    
    # Create the response object
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="profit_loss_report.csv"'
    response.charset = 'utf-8-sig'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow(['Category', 'Amount'])
    
    # Revenue
    total_sales = Order.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # COGS
    cogs = OrderItem.objects.filter(
        order__order_date__gte=start_date,
        order__order_date__lte=end_date
    ).aggregate(
        total=Sum(F('product__cost_price') * F('quantity'))
    )['total'] or 0
    
    # Gross Profit
    gross_profit = total_sales - cogs
    
    # Expenses
    expenses = Expense.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    )
    
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Net Profit
    net_profit = gross_profit - total_expenses
    
    # Write summary data
    writer.writerow(['Revenue', total_sales])
    writer.writerow(['Cost of Goods Sold', cogs])
    writer.writerow(['Gross Profit', gross_profit])
    writer.writerow(['Total Expenses', total_expenses])
    writer.writerow(['Net Profit', net_profit])
    
    # Write expense breakdown
    writer.writerow([])
    writer.writerow(['Expense Breakdown', ''])
    
    expenses_by_category = expenses.values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    for expense in expenses_by_category:
        writer.writerow([expense['category__name'], expense['total']])
    
    return response

# Supplier List View
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('name')
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Add pagination
    paginator = Paginator(suppliers, 10)  # Show 10 suppliers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventory/supplier_list.html', {
        'suppliers': page_obj,
        'search_query': search_query
    })

# Create Supplier View
@login_required
def create_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier created successfully.')
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'inventory/create_supplier.html', {'form': form})

# Client List View
@login_required
def client_list(request):
    clients = Client.objects.all().order_by('name')
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Add pagination
    paginator = Paginator(clients, 10)  # Show 10 clients per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventory/client_list.html', {
        'clients': page_obj,
        'search_query': search_query
    })

# Create Client View
@login_required
def create_client(request):
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
        try:
            # Check if the content type is application/json
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                # Handle form data if not JSON
                data = request.POST.dict()
                
            name = data.get('name')
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'اسم العميل مطلوب'
                }, status=400)
            
            # Check if client already exists
            if Client.objects.filter(name=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'العميل موجود بالفعل'
                }, status=400)
            
            # Create client
            client = Client.objects.create(
                name=name,
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                address=data.get('address', ''),
                type=data.get('type', 'regular'),
                notes=data.get('notes', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء العميل بنجاح',
                'client_id': client.id
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'تنسيق البيانات غير صالح'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في إنشاء العميل: {str(e)}'
            }, status=400)
    
    # Handle regular form submissions
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client created successfully.')
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'inventory/create_client.html', {'form': form})

# Update Client API View
@login_required
@require_POST
def update_client(request, client_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            client = get_object_or_404(Client, id=client_id)
            
            # Check if the content type is application/json
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                # Handle form data if not JSON
                data = request.POST.dict()
            
            # Update client fields
            client.name = data.get('name', client.name)
            client.phone = data.get('phone', client.phone)
            client.email = data.get('email', client.email)
            client.address = data.get('address', client.address)
            client.type = data.get('type', client.type)
            client.notes = data.get('notes', client.notes)
            
            client.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم تحديث العميل بنجاح',
                'client_id': client.id
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'تنسيق البيانات غير صالح'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في تحديث العميل: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Get Client Details API View
@login_required
def get_client_details(request, client_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            client = get_object_or_404(Client, id=client_id)
            
            # Get recent orders
            recent_orders = Order.objects.filter(client=client).order_by('-order_date')[:5]
            orders_data = []
            for order in recent_orders:
                orders_data.append({
                    'date': order.order_date.strftime('%Y-%m-%d'),
                    'invoice_number': order.invoice_number,
                    'amount': float(order.total_amount)
                })
            
            # Calculate statistics
            total_purchases = Order.objects.filter(client=client).aggregate(total=Sum('total_amount'))['total'] or 0
            orders_count = Order.objects.filter(client=client).count()
            last_order = Order.objects.filter(client=client).order_by('-order_date').first()
            
            data = {
                'id': client.id,
                'name': client.name,
                'phone': client.phone or '',
                'email': client.email or '',
                'address': client.address or '',
                'type': client.type or 'regular',
                'notes': client.notes or '',
                'created_at': client.created_at.strftime('%Y-%m-%d') if client.created_at else '',
                'recent_orders': orders_data,
                'total_purchases': float(total_purchases),
                'orders_count': orders_count,
                'last_order': last_order.order_date.strftime('%Y-%m-%d') if last_order else '--'
            }
            
            return JsonResponse({
                'success': True,
                'client': data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في الحصول على تفاصيل العميل: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Delete Client API View
@login_required
@require_POST
def delete_client(request, client_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            client = get_object_or_404(Client, id=client_id)
            
            # Check if client can be deleted (no related orders)
            if Order.objects.filter(client=client).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'لا يمكن حذف العميل لأنه مرتبط بطلبات مبيعات'
                }, status=400)
            
            # Delete client
            client_name = client.name
            client.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'تم حذف العميل "{client_name}" بنجاح'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في حذف العميل: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Dashboard View
@login_required
def dashboard(request):
    # Get current date and date ranges
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    last_month_end = start_of_month - timedelta(days=1)
    
    # Sales statistics
    total_sales_current_month = Order.objects.filter(
        order_date__gte=start_of_month,
        order_date__lte=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_sales_last_month = Order.objects.filter(
        order_date__gte=last_month_start,
        order_date__lte=last_month_end
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    sales_growth = 0
    if total_sales_last_month > 0:
        sales_growth = ((total_sales_current_month - total_sales_last_month) / total_sales_last_month) * 100
    
    # Purchases statistics
    total_purchases_current_month = PurchaseOrderItem.objects.filter(
        purchase_order__date__gte=start_of_month,
        purchase_order__date__lte=today
    ).aggregate(total=Sum(F('quantity') * F('price')))['total'] or 0
    
    # Profit calculation
    total_profit_current_month = OrderItem.objects.filter(
        order__order_date__gte=start_of_month,
        order__order_date__lte=today
    ).aggregate(
        profit=Sum((F('price') - F('product__cost_price')) * F('quantity'))
    )['profit'] or 0
    
    # Low stock products
    low_stock_products = Product.objects.filter(quantity__lte=F('reorder_level'))[:5]
    
    # Top selling products
    top_selling_products = OrderItem.objects.values(
        'product__name'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    # Recent purchase orders
    recent_purchases = PurchaseOrder.objects.order_by('-created_at')[:5]
    
    # Sales by month (for chart)
    six_months_ago = today - timedelta(days=180)
    sales_by_month = Order.objects.filter(
        order_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')
    
    # Format for Chart.js
    months = []
    sales_data = []
    for entry in sales_by_month:
        months.append(entry['month'].strftime('%b %Y'))
        sales_data.append(float(entry['total']))
    
    # Expenses by category (for chart)
    expenses_by_category = Expense.objects.filter(
        date__gte=start_of_month
    ).values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Format for Chart.js
    expense_categories = []
    expense_data = []
    for entry in expenses_by_category:
        expense_categories.append(entry['category__name'])
        expense_data.append(float(entry['total']))
    
    context = {
        'total_sales_current_month': total_sales_current_month,
        'sales_growth': sales_growth,
        'total_purchases_current_month': total_purchases_current_month,
        'total_profit_current_month': total_profit_current_month,
        'low_stock_products': low_stock_products,
        'top_selling_products': top_selling_products,
        'recent_orders': recent_orders,
        'recent_purchases': recent_purchases,
        'months': json.dumps(months),
        'sales_data': json.dumps(sales_data),
        'expense_categories': json.dumps(expense_categories),
        'expense_data': json.dumps(expense_data),
    }
    
    return render(request, 'inventory/dashboard.html', context)

# Home View
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

# Product List View
@login_required
def product_list(request):
    products = Product.objects.all().order_by('name')
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Get categories, suppliers, and locations for the form
    categories = Category.objects.all().order_by('name')
    suppliers = Supplier.objects.all().order_by('name')
    locations = StorageLocation.objects.all().order_by('name')
    
    return render(request, 'inventory/product_list.html', {
        'products': products,
        'categories': categories,
        'suppliers': suppliers,
        'locations': locations,
        'search_query': search_query
    })

# Create Product API View
@login_required
@require_POST
def create_product(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            
            # Create product
            product = Product.objects.create(
                name=data.get('name'),
                sku=data.get('sku'),
                description=data.get('description', ''),
                price=data.get('price'),
                cost_price=data.get('cost_price'),
                quantity=data.get('quantity', 0),
                reorder_level=data.get('reorder_level', 10),
                category_id=data.get('category_id'),
                supplier_id=data.get('supplier_id'),
                location_id=data.get('location_id')
            )
            
            # Create stock record for initial quantity
            if product.quantity > 0:
                Stock.objects.create(
                    product=product,
                    quantity_received=product.quantity,
                    quantity_sold=0,
                    date_received=timezone.now().date(),
                    stock_type='received',
                    notes="Initial stock"
                )
            
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء المنتج بنجاح',
                'product_id': product.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في إنشاء المنتج: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Update Product API View
@login_required
@require_POST
def update_product(request, product_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            product = get_object_or_404(Product, id=product_id)
            data = json.loads(request.body)
            
            # Check if quantity changed
            old_quantity = product.quantity
            new_quantity = int(data.get('quantity', 0))
            quantity_changed = old_quantity != new_quantity
            
            # Update product fields
            product.name = data.get('name', product.name)
            product.sku = data.get('sku', product.sku)
            product.description = data.get('description', product.description)
            product.price = data.get('price', product.price)
            product.cost_price = data.get('cost_price', product.cost_price)
            product.quantity = new_quantity
            product.reorder_level = data.get('reorder_level', product.reorder_level)
            
            # Update relationships
            if data.get('category_id'):
                product.category_id = data.get('category_id')
            if data.get('supplier_id'):
                product.supplier_id = data.get('supplier_id')
            if data.get('location_id'):
                product.location_id = data.get('location_id')
            
            product.save()
            
            # Create stock record if quantity changed
            if quantity_changed:
                quantity_diff = new_quantity - old_quantity
                if quantity_diff > 0:
                    Stock.objects.create(
                        product=product,
                        quantity_received=quantity_diff,
                        quantity_sold=0,
                        date_received=timezone.now().date(),
                        stock_type='received',
                        notes="Manual adjustment"
                    )
                elif quantity_diff < 0:
                    Stock.objects.create(
                        product=product,
                        quantity_received=0,
                        quantity_sold=abs(quantity_diff),
                        date_received=timezone.now().date(),
                        stock_type='sold',
                        notes="Manual adjustment"
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'تم تحديث المنتج بنجاح',
                'product_id': product.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في تحديث المنتج: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Get Product Details API View
@login_required
def get_product_details(request, product_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Get stock movements
            stock_movements = Stock.objects.filter(product=product).order_by('-date_received')[:10]
            movements = []
            for movement in stock_movements:
                movements.append({
                    'date': movement.date_received.strftime('%Y-%m-%d'),
                    'type': movement.stock_type,
                    'quantity': movement.quantity_received if movement.stock_type == 'received' else movement.quantity_sold,
                    'notes': movement.notes or ''
                })
            
            # Get recent sales
            recent_sales = OrderItem.objects.filter(product=product).order_by('-order__order_date')[:10]
            sales = []
            for sale in recent_sales:
                sales.append({
                    'date': sale.order.order_date.strftime('%Y-%m-%d'),
                    'client': sale.order.client.name,
                    'quantity': sale.quantity,
                    'total': float(sale.get_total())
                })
            
            data = {
                'id': product.id,
                'name': product.name,
                'sku': product.sku or '',
                'description': product.description or '',
                'price': float(product.price),
                'cost_price': float(product.cost_price),
                'quantity': product.quantity,
                'reorder_level': product.reorder_level,
                'category': product.category.name if product.category else None,
                'category_id': product.category.id if product.category else None,
                'supplier': product.supplier.name if product.supplier else None,
                'supplier_id': product.supplier.id if product.supplier else None,
                'location': product.location.name if product.location else None,
                'location_id': product.location.id if product.location else None,
                'stock_movements': movements,
                'recent_sales': sales
            }
            
            return JsonResponse({
                'success': True,
                'product': data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في الحصول على تفاصيل المنتج: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Delete Product API View
@login_required
@require_POST
def delete_product(request, product_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Check if product can be deleted (no related orders or purchase orders)
            if OrderItem.objects.filter(product=product).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'لا يمكن حذف المنتج لأنه مرتبط بطلبات مبيعات'
                }, status=400)
            
            if PurchaseOrderItem.objects.filter(product=product).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'لا يمكن حذف المنتج لأنه مرتبط بطلبات شراء'
                }, status=400)
            
            # Delete stock records
            Stock.objects.filter(product=product).delete()
            
            # Delete product
            product_name = product.name
            product.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'تم حذف المنتج "{product_name}" بنجاح'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في حذف المنتج: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Order List View
@login_required
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(invoice_number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    # Add pagination
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get clients for the form
    clients = Client.objects.all()
    products = Product.objects.all()
    
    return render(request, 'inventory/order_list.html', {
        'orders': page_obj,
        'search_query': search_query,
        'clients': clients,
        'products': products
    })

# Create Order View (AJAX)
# Temporarily remove login_required and require_POST decorators for testing
# @login_required
# @require_POST
from django.views.decorators.csrf import csrf_exempt  # Add this import

@csrf_exempt  # Temporarily disable CSRF protection for testing
def create_order(request):
    # Log all request details for debugging
    print("Request method:", request.method)
    print("Request headers:", request.headers)
    print("Request content type:", request.content_type)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Log raw request body
            print("Raw request body:", request.body.decode('utf-8'))
            
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                print("JSON decode error:", str(e))
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid JSON: {str(e)}'
                }, status=400)
            
            # Log parsed data
            print("Parsed data:", data)
            
            try:
                try:
                    # Create order instance without saving it
                    try:
                        # Convert numeric fields to appropriate types
                        client_id = data.get('client_id')
                        if isinstance(client_id, str):
                            client_id = int(client_id)
                            
                        discount_percentage = data.get('discount_percentage', 0)
                        if isinstance(discount_percentage, str):
                            discount_percentage = float(discount_percentage)
                            
                        tax_percentage = data.get('tax_percentage', 0)
                        if isinstance(tax_percentage, str):
                            tax_percentage = float(tax_percentage)
                            
                        shipping_cost = data.get('shipping_cost', 0)
                        if isinstance(shipping_cost, str):
                            shipping_cost = float(shipping_cost)
                            
                        order = Order(
                            client_id=client_id,
                            status=data.get('status', 'draft'),
                            discount_percentage=discount_percentage,
                            tax_percentage=tax_percentage,
                            shipping_cost=shipping_cost,
                            notes=data.get('notes', ''),
                            created_by=request.user if request.user.is_authenticated else None
                        )
                        
                        # Handle discount_amount if provided
                        if 'discount_amount' in data:
                            discount_amount = data.get('discount_amount', 0)
                            if isinstance(discount_amount, str):
                                discount_amount = float(discount_amount)
                            order.discount_amount = discount_amount
                    except (ValueError, TypeError) as e:
                        return JsonResponse({
                            'success': False,
                            'message': f'Error converting data types: {str(e)}'
                        }, status=400)
                    
                    # Handle order_date if provided
                    if 'order_date' in data:
                        try:
                            order_date_str = data.get('order_date')
                            print(f"Received order_date: {order_date_str}, type: {type(order_date_str)}")
                            
                            # Try to parse the date string
                            from datetime import datetime
                            try:
                                order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date()
                                order.order_date = order_date
                                print(f"Parsed order_date: {order_date}")
                            except ValueError as e:
                                print(f"Error parsing order_date: {str(e)}")
                                # If there's an error, the auto_now_add will handle it
                                pass
                        except Exception as e:
                            print(f"Error setting order_date: {str(e)}")
                            # If there's an error, the auto_now_add will handle it
                            pass
                    
                    # Log the data for debugging
                    print(f"Creating order with data: {data}")
                    print(f"Client ID: {order.client_id}, type: {type(order.client_id)}")
                    print(f"Tax percentage: {order.tax_percentage}, type: {type(order.tax_percentage)}")
                    print(f"Discount percentage: {order.discount_percentage}, type: {type(order.discount_percentage)}")
                    print(f"Discount amount: {order.discount_amount}, type: {type(order.discount_amount)}")
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'message': f'Error creating order object: {str(e)}'
                    }, status=400)
                
                # Manually set the invoice number
                order.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{Order.objects.count() + 1}"
                
                # Set total_amount to 0 initially
                order.total_amount = 0
                
                # Save the order without calculating totals
                order.save(calculate_total=False)
                
                # Create order items
                items = data.get('items', [])
                print(f"Items array: {items}, type: {type(items)}")
                
                # Log each item for debugging
                for i, item in enumerate(items):
                    print(f"Item {i} details: {item}")
                
                if not items or not isinstance(items, list) or len(items) == 0:
                    return JsonResponse({
                        'success': False,
                        'message': 'No items provided or invalid items format'
                    }, status=400)
                
                try:
                    # Check if items array is empty after filtering out invalid items
                    valid_items = []
                    
                    for i, item in enumerate(items):
                        print(f"Processing item {i}: {item}, type: {type(item)}")
                        
                        if not isinstance(item, dict):
                            print(f"Warning: Item {i} is not a dictionary: {item}")
                            continue
                        
                        product_id = item.get('product_id')
                        quantity = item.get('quantity')
                        price = item.get('price')
                        
                        print(f"Creating order item: product_id={product_id}, type={type(product_id)}, quantity={quantity}, type={type(quantity)}, price={price}, type={type(price)}")
                        
                        if product_id is None:
                            print(f"Warning: Missing product_id in item {i}")
                            continue
                            
                        if quantity is None:
                            print(f"Warning: Missing quantity in item {i}")
                            continue
                            
                        if price is None:
                            print(f"Warning: Missing price in item {i}")
                            continue
                        
                        # Convert string to int/float if needed
                        try:
                            if isinstance(product_id, str):
                                product_id = int(product_id)
                                
                            if isinstance(quantity, str):
                                quantity = int(quantity)
                            elif isinstance(quantity, float):
                                quantity = int(quantity)
                            
                            if isinstance(price, str):
                                price = float(price)
                                
                        except (ValueError, TypeError) as e:
                            print(f"Warning: Error converting data types in item {i}: {str(e)}")
                            continue
                        
                        # Skip items with zero quantity
                        if quantity <= 0:
                            print(f"Warning: Skipping item {i} with zero or negative quantity")
                            continue
                        
                        # Verify product exists
                        try:
                            product = Product.objects.get(id=product_id)
                            valid_items.append({
                                'product_id': product_id,
                                'quantity': quantity,
                                'price': price,
                                'product': product
                            })
                        except Product.DoesNotExist:
                            print(f"Warning: Product with ID {product_id} does not exist")
                            continue
                    
                    # Check if we have any valid items
                    if not valid_items:
                        return JsonResponse({
                            'success': False,
                            'message': 'No valid items found in the order'
                        }, status=400)
                    
                    # Create order items for valid items
                    for item_data in valid_items:
                        OrderItem.objects.create(
                            order=order,
                            product_id=item_data['product_id'],
                            quantity=item_data['quantity'],
                            price=item_data['price']
                        )
                        print(f"Created order item: product_id={item_data['product_id']}, quantity={item_data['quantity']}, price={item_data['price']}")
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'message': f'Error creating order items: {str(e)}'
                    }, status=400)
                
                # Now that items are created, calculate the total
                subtotal = OrderItem.objects.filter(order=order).aggregate(
                    subtotal=Sum(F('quantity') * F('price')))['subtotal'] or 0
                
                # Calculate discount
                if order.discount_percentage > 0:
                    # Convert to float for calculation to avoid Decimal/float mismatch
                    subtotal_float = float(subtotal)
                    discount_percentage_float = float(order.discount_percentage)
                    order.discount_amount = subtotal_float * (discount_percentage_float / 100)
                
                # Calculate tax
                # Convert to float for calculation to avoid Decimal/float mismatch
                subtotal_float = float(subtotal)
                discount_amount_float = float(order.discount_amount)
                tax_percentage_float = float(order.tax_percentage)
                tax_amount = (subtotal_float - discount_amount_float) * (tax_percentage_float / 100)
                
                # Calculate total
                shipping_cost_float = float(order.shipping_cost)
                order.total_amount = subtotal_float - discount_amount_float + tax_amount + shipping_cost_float
                
                # Save the order again with the calculated total
                order.save(calculate_total=False)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error creating order: {str(e)}'
                }, status=400)
            
            # Update product quantities using the valid_items list
            try:
                for item_data in valid_items:
                    product = item_data['product']
                    quantity = item_data['quantity']
                    
                    print(f"Updating product quantity: product_id={product.id}, quantity={quantity}, type={type(quantity)}")
                    
                    # Check if there's enough stock
                    if product.quantity < quantity:
                        return JsonResponse({
                            'success': False,
                            'message': f'Not enough stock for product "{product.name}". Available: {product.quantity}, Requested: {quantity}'
                        }, status=400)
                    
                    product.quantity -= quantity
                    product.save()
                    
                    # Create stock record
                    Stock.objects.create(
                        product=product,
                        quantity_sold=quantity,
                        quantity_received=0,
                        date_received=timezone.now().date(),
                        stock_type='sold',
                        notes=f"Sold in order #{order.invoice_number}"
                    )
                    
                    print(f"Updated product quantity for {product.name}: new quantity = {product.quantity}")
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error updating product quantities: {str(e)}'
                }, status=400)
            
            # Calculate total manually
            subtotal = OrderItem.objects.filter(order=order).aggregate(
                subtotal=Sum(F('quantity') * F('price')))['subtotal'] or 0
            
            # Calculate discount
            if order.discount_percentage > 0:
                discount_amount = float(subtotal) * (float(order.discount_percentage) / 100)
                order.discount_amount = discount_amount
            
            # Calculate tax
            tax_amount = (float(subtotal) - float(order.discount_amount)) * (float(order.tax_percentage) / 100)
            
            # Calculate total
            shipping_cost = float(order.shipping_cost) if order.shipping_cost else 0
            total_amount = float(subtotal) - float(order.discount_amount) + tax_amount + shipping_cost
            
            # Update the total amount
            order.total_amount = total_amount
            order.save(calculate_total=False)  # Don't recalculate to avoid double calculation
            
            return JsonResponse({
                'success': True,
                'message': 'Order created successfully',
                'order_id': order.id,
                'invoice_number': order.invoice_number
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating order: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# Update Order View (AJAX)
@login_required
@require_POST
def update_order(request, order_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            order = get_object_or_404(Order, id=order_id)
            data = json.loads(request.body)
            
            # Update order fields
            order.client_id = data.get('client_id', order.client_id)
            order.status = data.get('status', order.status)
            order.discount_percentage = data.get('discount_percentage', order.discount_percentage)
            order.tax_percentage = data.get('tax_percentage', order.tax_percentage)
            order.shipping_cost = data.get('shipping_cost', order.shipping_cost)
            order.notes = data.get('notes', order.notes)
            
            # Handle order items
            if 'items' in data:
                # First, restore quantities for existing items
                for item in order.orderitem_set.all():
                    product = item.product
                    product.quantity += item.quantity
                    product.save()
                
                # Delete existing items
                order.orderitem_set.all().delete()
                
                # Create new items
                items = data.get('items', [])
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product_id=item.get('product_id'),
                        quantity=item.get('quantity'),
                        price=item.get('price')
                    )
                
                # Update product quantities
                for item in items:
                    product = Product.objects.get(id=item.get('product_id'))
                    product.quantity -= item.get('quantity')
                    product.save()
            
            # Calculate total manually
            subtotal = OrderItem.objects.filter(order=order).aggregate(
                subtotal=Sum(F('quantity') * F('price')))['subtotal'] or 0
            
            # Calculate discount
            if order.discount_percentage > 0:
                discount_amount = float(subtotal) * (float(order.discount_percentage) / 100)
                order.discount_amount = discount_amount
            
            # Calculate tax
            tax_amount = (float(subtotal) - float(order.discount_amount)) * (float(order.tax_percentage) / 100)
            
            # Calculate total
            shipping_cost = float(order.shipping_cost) if order.shipping_cost else 0
            total_amount = float(subtotal) - float(order.discount_amount) + tax_amount + shipping_cost
            
            # Update the total amount
            order.total_amount = total_amount
            
            # Log the calculated values for debugging
            print(f"Order {order.id} calculation (update_order):")
            print(f"Subtotal: {subtotal}")
            print(f"Discount: {order.discount_amount}")
            print(f"Tax: {tax_amount}")
            print(f"Shipping: {shipping_cost}")
            print(f"Total: {total_amount}")
            
            # Save the order with the updated total
            order.save(calculate_total=False)  # Don't recalculate to avoid double calculation
            
            return JsonResponse({
                'success': True,
                'message': 'Order updated successfully',
                'order_id': order.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating order: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# Get Order Details (AJAX)
@login_required
def get_order_details(request, order_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            order = get_object_or_404(Order, id=order_id)
            items = []
            
            for item in order.orderitem_set.all():
                items.append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'total': float(item.get_total())
                })
            
            data = {
                'id': order.id,
                'invoice_number': order.invoice_number,
                'client_id': order.client.id,
                'client_name': order.client.name,
                'order_date': order.order_date.strftime('%Y-%m-%d'),
                'status': order.status,
                'discount_percentage': float(order.discount_percentage),
                'discount_amount': float(order.discount_amount),
                'tax_percentage': float(order.tax_percentage),
                'shipping_cost': float(order.shipping_cost),
                'total_amount': float(order.total_amount),
                'notes': order.notes,
                'items': items
            }
            
            return JsonResponse({
                'success': True,
                'order': data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error getting order details: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# Delete Order (AJAX)
@login_required
@require_POST
def delete_order(request, order_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            order = get_object_or_404(Order, id=order_id)
            
            # Restore product quantities
            for item in order.orderitem_set.all():
                product = item.product
                product.quantity += item.quantity
                product.save()
            
            # Delete order
            order.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Order deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting order: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# Purchase Order List View
@login_required
def purchase_order_list(request):
    purchase_orders = PurchaseOrder.objects.all().order_by('-created_at')
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        purchase_orders = purchase_orders.filter(
            Q(reference_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    # Add pagination
    paginator = Paginator(purchase_orders, 10)  # Show 10 purchase orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get suppliers for the form
    suppliers = Supplier.objects.all()
    products = Product.objects.all()
    
    return render(request, 'inventory/purchase_order_list.html', {
        'purchase_orders': page_obj,
        'search_query': search_query,
        'suppliers': suppliers,
        'products': products
    })

# Create Purchase Order View (AJAX)
@login_required
@require_POST
def create_purchase_order(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            
            try:
                # Create purchase order instance without saving it
                purchase_order = PurchaseOrder(
                    supplier_id=data.get('supplier_id'),
                    reference_number=data.get('reference_number'),
                    status=data.get('status', 'draft'),
                    notes=data.get('notes', ''),
                    created_by=request.user if request.user.is_authenticated else None
                )
                
                # Manually set the reference number if not provided
                if not purchase_order.reference_number:
                    purchase_order.reference_number = f"PO-{timezone.now().strftime('%Y%m%d')}-{PurchaseOrder.objects.count() + 1}"
                
                # Save the purchase order without calculating totals
                purchase_order.save(calculate_total=False)
                
                # Create purchase order items
                items = data.get('items', [])
                for item in items:
                    PurchaseOrderItem.objects.create(
                        purchase_order=purchase_order,
                        product_id=item.get('product_id'),
                        quantity=item.get('quantity'),
                        price=item.get('price')
                    )
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error creating purchase order: {str(e)}'
                }, status=400)
            
            # If status is 'received', update product quantities
            if purchase_order.status == 'received':
                for item in items:
                    product = Product.objects.get(id=item.get('product_id'))
                    product.quantity += item.get('quantity')
                    product.save()
                    
                    # Create stock record
                    Stock.objects.create(
                        product=product,
                        quantity_received=item.get('quantity'),
                        quantity_sold=0,
                        date_received=timezone.now().date(),
                        stock_type='received',
                        notes=f"Received in purchase order #{purchase_order.reference_number}"
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'Purchase order created successfully',
                'purchase_order_id': purchase_order.id,
                'reference_number': purchase_order.reference_number
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating purchase order: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# Update Purchase Order View (AJAX)
@login_required
@require_POST
def update_purchase_order(request, purchase_order_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
            data = json.loads(request.body)
            
            # Check if status is changing from non-received to received
            status_changing_to_received = purchase_order.status != 'received' and data.get('status') == 'received'
            
            # Update purchase order fields
            purchase_order.supplier_id = data.get('supplier_id', purchase_order.supplier_id)
            purchase_order.reference_number = data.get('reference_number', purchase_order.reference_number)
            purchase_order.status = data.get('status', purchase_order.status)
            purchase_order.notes = data.get('notes', purchase_order.notes)
            
            # Handle purchase order items
            if 'items' in data:
                # If status was 'received', restore quantities
                if purchase_order.status == 'received':
                    for item in purchase_order.purchaseorderitem_set.all():
                        product = item.product
                        product.quantity -= item.quantity
                        product.save()
                
                # Delete existing items
                purchase_order.purchaseorderitem_set.all().delete()
                
                # Create new items
                items = data.get('items', [])
                for item in items:
                    PurchaseOrderItem.objects.create(
                        purchase_order=purchase_order,
                        product_id=item.get('product_id'),
                        quantity=item.get('quantity'),
                        price=item.get('price')
                    )
                
                # If status is now 'received', update product quantities
                if purchase_order.status == 'received' or status_changing_to_received:
                    for item in items:
                        product = Product.objects.get(id=item.get('product_id'))
                        product.quantity += item.get('quantity')
                        product.save()
                        
                        # Create stock record
                        Stock.objects.create(
                            product=product,
                            quantity_received=item.get('quantity'),
                            quantity_sold=0,
                            date_received=timezone.now().date(),
                            stock_type='received',
                            notes=f"Received in purchase order #{purchase_order.reference_number}"
                        )
            
            purchase_order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Purchase order updated successfully',
                'purchase_order_id': purchase_order.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating purchase order: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# Get Purchase Order Details (AJAX)
@login_required
def get_purchase_order_details(request, purchase_order_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
            items = []
            
            for item in purchase_order.purchaseorderitem_set.all():
                items.append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'total': float(item.get_total())
                })
            
            data = {
                'id': purchase_order.id,
                'reference_number': purchase_order.reference_number,
                'supplier_id': purchase_order.supplier.id,
                'supplier_name': purchase_order.supplier.name,
                'date': purchase_order.date.strftime('%Y-%m-%d'),
                'status': purchase_order.status,
                'notes': purchase_order.notes,
                'items': items,
                'total': float(purchase_order.get_total())
            }
            
            return JsonResponse({
                'success': True,
                'purchase_order': data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error getting purchase order details: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# Delete Purchase Order (AJAX)
@login_required
@require_POST
def delete_purchase_order(request, purchase_order_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
            
            # If status was 'received', restore quantities
            if purchase_order.status == 'received':
                for item in purchase_order.purchaseorderitem_set.all():
                    product = item.product
                    product.quantity -= item.quantity
                    product.save()
            
            # Delete purchase order
            purchase_order.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Purchase order deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting purchase order: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

# Create Category API View
@login_required
@require_POST
def create_category(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'اسم التصنيف مطلوب'
                }, status=400)
            
            # Check if category already exists
            if Category.objects.filter(name=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'التصنيف موجود بالفعل'
                }, status=400)
            
            # Create category
            category = Category.objects.create(name=name)
            
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء التصنيف بنجاح',
                'category_id': category.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في إنشاء التصنيف: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Create Supplier API View
@login_required
@require_POST
def create_supplier(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'اسم المورد مطلوب'
                }, status=400)
            
            # Check if supplier already exists
            if Supplier.objects.filter(name=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'المورد موجود بالفعل'
                }, status=400)
            
            # Create supplier
            supplier = Supplier.objects.create(
                name=name,
                contact_person=data.get('contact_person', ''),
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                address=data.get('address', ''),
                notes=data.get('notes', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء المورد بنجاح',
                'supplier_id': supplier.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في إنشاء المورد: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Update Supplier API View
@login_required
@require_POST
def update_supplier(request, supplier_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            supplier = get_object_or_404(Supplier, id=supplier_id)
            data = json.loads(request.body)
            
            # Update supplier fields
            supplier.name = data.get('name', supplier.name)
            supplier.contact_person = data.get('contact_person', supplier.contact_person)
            supplier.phone = data.get('phone', supplier.phone)
            supplier.email = data.get('email', supplier.email)
            supplier.address = data.get('address', supplier.address)
            supplier.notes = data.get('notes', supplier.notes)
            
            supplier.save()
            
            return JsonResponse({
                'success': True,
                'message': 'تم تحديث المورد بنجاح',
                'supplier_id': supplier.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في تحديث المورد: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Get Supplier Details API View
@login_required
def get_supplier_details(request, supplier_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            supplier = get_object_or_404(Supplier, id=supplier_id)
            
            data = {
                'id': supplier.id,
                'name': supplier.name,
                'contact_person': supplier.contact_person or '',
                'phone': supplier.phone or '',
                'email': supplier.email or '',
                'address': supplier.address or '',
                'notes': supplier.notes or ''
            }
            
            return JsonResponse({
                'success': True,
                'supplier': data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في الحصول على تفاصيل المورد: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Delete Supplier API View
@login_required
@require_POST
def delete_supplier(request, supplier_id):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            supplier = get_object_or_404(Supplier, id=supplier_id)
            
            # Check if supplier can be deleted (no related products)
            if Product.objects.filter(supplier=supplier).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'لا يمكن حذف المورد لأنه مرتبط بمنتجات'
                }, status=400)
            
            # Delete supplier
            supplier_name = supplier.name
            supplier.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'تم حذف المورد "{supplier_name}" بنجاح'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في حذف المورد: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# Create Location API View
@login_required
@require_POST
def create_location(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'اسم مكان التخزين مطلوب'
                }, status=400)
            
            # Check if location already exists
            if StorageLocation.objects.filter(name=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'مكان التخزين موجود بالفعل'
                }, status=400)
            
            # Create location
            location = StorageLocation.objects.create(name=name)
            
            return JsonResponse({
                'success': True,
                'message': 'تم إنشاء مكان التخزين بنجاح',
                'location_id': location.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطأ في إنشاء مكان التخزين: {str(e)}'
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'طلب غير صالح'}, status=400)

# API endpoint to get order details
@csrf_exempt
def order_details_api(request, order_id):
    """API endpoint to get order details"""
    if request.method == 'GET':
        try:
            order = Order.objects.get(id=order_id)
            
            # Get order items
            items = []
            for item in order.orderitem_set.all():
                items.append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'total': float(item.quantity * item.price)
                })
            
            # Calculate subtotal
            subtotal = sum(item['total'] for item in items) if items else 0
            
            # Calculate tax amount
            discount_amount = float(order.discount_amount) if order.discount_amount else 0
            tax_percentage = float(order.tax_percentage) if order.tax_percentage else 0
            tax_amount = (subtotal - discount_amount) * (tax_percentage / 100)
            
            # Calculate total amount
            shipping_cost = float(order.shipping_cost) if order.shipping_cost else 0
            total_amount = subtotal - discount_amount + tax_amount + shipping_cost
            
            # Prepare response data
            data = {
                'success': True,
                'order': {
                    'id': order.id,
                    'invoice_number': order.invoice_number or f'INV-{order.id}',
                    'client_id': order.client.id,
                    'client_name': order.client.name,
                    'client_phone': order.client.phone or '',
                    'client_address': order.client.address or '',
                    'order_date': order.order_date.strftime('%Y-%m-%d'),
                    'status': order.status or 'draft',
                    'notes': order.notes or '',
                    'subtotal': subtotal,
                    'tax_percentage': tax_percentage,
                    'tax_amount': tax_amount,
                    'discount_percentage': float(order.discount_percentage) if order.discount_percentage else 0,
                    'discount_amount': discount_amount,
                    'shipping_cost': float(order.shipping_cost) if order.shipping_cost else 0,
                    'total_amount': total_amount,  # Use our calculated total amount
                    'items': items
                }
            }
            
            return JsonResponse(data)
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

# API endpoint to delete an order
@csrf_exempt
def order_delete_api(request, order_id):
    """API endpoint to delete an order"""
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            
            # Delete the order
            order.delete()
            
            return JsonResponse({'success': True, 'message': 'Order deleted successfully'})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

# API endpoint to update an order
@csrf_exempt  # Use csrf_exempt for testing, but in production you should use proper CSRF protection
def update_order_api(request, order_id):
    """API endpoint to update an order"""
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            data = json.loads(request.body)
            
            # Update order fields
            if 'client_id' in data:
                order.client_id = data.get('client_id')
            if 'order_date' in data:
                order.order_date = datetime.strptime(data.get('order_date'), '%Y-%m-%d').date()
            if 'status' in data:
                order.status = data.get('status')
            if 'notes' in data:
                order.notes = data.get('notes')
            if 'tax_percentage' in data:
                order.tax_percentage = data.get('tax_percentage')
            if 'discount_percentage' in data:
                order.discount_percentage = data.get('discount_percentage')
            if 'discount_amount' in data:
                order.discount_amount = data.get('discount_amount')
            if 'shipping_cost' in data:
                order.shipping_cost = data.get('shipping_cost')
            
            # Save order without calculating total
            order.save(calculate_total=False)
            
            # Handle order items
            if 'items' in data:
                # First, restore quantities for existing items
                for item in order.orderitem_set.all():
                    product = item.product
                    product.quantity += item.quantity
                    product.save()
                
                # Delete existing items
                order.orderitem_set.all().delete()
                
                # Create new items
                items = data.get('items', [])
                for item in items:
                    product_id = item.get('product_id')
                    quantity = item.get('quantity')
                    price = item.get('price')
                    
                    # Skip invalid items
                    if not product_id or not quantity or not price:
                        continue
                    
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product_id=product_id,
                        quantity=quantity,
                        price=price
                    )
                    
                    # Update product quantity
                    product = Product.objects.get(id=product_id)
                    product.quantity -= quantity
                    product.save()
            
            # Calculate total manually
            subtotal = OrderItem.objects.filter(order=order).aggregate(
                subtotal=Sum(F('quantity') * F('price')))['subtotal'] or 0
            
            # Calculate discount
            if order.discount_percentage > 0:
                discount_amount = float(subtotal) * (float(order.discount_percentage) / 100)
                order.discount_amount = discount_amount
            
            # Calculate tax
            tax_amount = (float(subtotal) - float(order.discount_amount)) * (float(order.tax_percentage) / 100)
            
            # Calculate total
            shipping_cost = float(order.shipping_cost) if order.shipping_cost else 0
            total_amount = float(subtotal) - float(order.discount_amount) + tax_amount + shipping_cost
            
            # Update the total amount
            order.total_amount = total_amount
            
            # Log the calculated values for debugging
            print(f"Order {order.id} calculation:")
            print(f"Subtotal: {subtotal}")
            print(f"Discount: {order.discount_amount}")
            print(f"Tax: {tax_amount}")
            print(f"Shipping: {shipping_cost}")
            print(f"Total: {total_amount}")
            
            # Save the order with the updated total
            order.save(calculate_total=False)  # Don't recalculate to avoid double calculation
            
            return JsonResponse({
                'success': True,
                'message': 'Order updated successfully',
                'order_id': order.id
            })
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)