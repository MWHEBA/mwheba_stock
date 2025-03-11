from django.contrib import admin
from django.db.models import Sum, F
from django.utils import timezone
from .models import (
    Product, Stock, Category, Supplier, Client, StorageLocation,
    PurchaseOrder, PurchaseOrderItem, Order, OrderItem,
    SupplierPayment, ClientPayment, CompanyProfile, ExpenseCategory,
    Expense, FinancialAccount, Transaction, UserProfile
)

# Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'cost_price', 'quantity', 'supplier', 'is_low_stock')
    list_filter = ('category', 'supplier', 'location')
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('quantity', 'reorder_level', 'location')
        }),
        ('Supplier', {
            'fields': ('supplier',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Stock Admin
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_received', 'quantity_sold', 'date_received', 'stock_type', 'location', 'timestamp')
    list_filter = ('stock_type', 'date_received', 'location')
    search_fields = ('product__name', 'notes')
    date_hierarchy = 'date_received'

# Supplier Admin
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'get_total_purchases', 'get_outstanding_balance')
    search_fields = ('name', 'contact_person', 'email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_person', 'phone', 'email', 'address', 'tax_number')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

# Client Admin
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'get_total_orders', 'get_outstanding_balance')
    search_fields = ('name', 'contact_person', 'email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_person', 'phone', 'email', 'address', 'tax_number')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

# Purchase Order Item Inline
class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    # Only show inline items for existing purchase orders
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Check if we're in an add view (no parent instance yet)
        if not hasattr(self, 'parent_instance') or not self.parent_instance or not self.parent_instance.pk:
            return qs.none()  # Return empty queryset for new purchase orders
        return qs

# Purchase Order Admin
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'supplier', 'date', 'status', 'get_total', 'created_by')
    list_filter = ('status', 'date', 'supplier')
    search_fields = ('reference_number', 'supplier__name', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PurchaseOrderItemInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('supplier', 'reference_number', 'status', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to handle saving the purchase order
        """
        if not change:  # If this is a new purchase order
            # Save with calculate_total=False
            obj.save(calculate_total=False)
        else:
            # For existing purchase orders, save normally
            obj.save()
    
    def save_formset(self, request, form, formset, change):
        """
        Override save_formset to handle saving inline items
        """
        instances = formset.save(commit=False)
        
        # Save new instances
        for instance in instances:
            instance.save()
            
        # Delete marked for deletion
        for obj in formset.deleted_objects:
            obj.delete()
            
        # Call formset's save_m2m
        formset.save_m2m()
        
        # Update product quantities if status is 'received'
        if form.instance.status == 'received':
            for item in instances:
                if isinstance(item, PurchaseOrderItem):
                    product = item.product
                    product.quantity += item.quantity
                    product.save()
                    
                    # Create stock record
                    Stock.objects.create(
                        product=product,
                        quantity_received=item.quantity,
                        quantity_sold=0,
                        date_received=timezone.now().date(),
                        stock_type='received',
                        notes=f"Received in purchase order #{form.instance.reference_number}"
                    )
# Order Item Inline
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    # Only show inline items for existing orders
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Check if we're in an add view (no parent instance yet)
        if not hasattr(self, 'parent_instance') or not self.parent_instance or not self.parent_instance.pk:
            return qs.none()  # Return empty queryset for new orders
        return qs
        return qs

# Order Admin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'order_date', 'status', 'total_amount', 'get_profit', 'created_by')
    list_filter = ('status', 'order_date', 'client')
    search_fields = ('invoice_number', 'client__name', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'total_amount')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('client', 'invoice_number', 'status', 'notes')
        }),
        ('Pricing', {
            'fields': ('discount_percentage', 'discount_amount', 'tax_percentage', 'shipping_cost', 'total_amount')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to handle saving the order without calculating totals
        """
        if not change:  # If this is a new order
            # Save without calculating totals
            obj.save(calculate_total=False)
        else:
            # For existing orders, save normally
            obj.save()
    
    def save_formset(self, request, form, formset, change):
        """
        Override save_formset to handle saving inline items and recalculating totals
        """
        instances = formset.save(commit=False)
        
        # Save new instances
        for instance in instances:
            instance.save()
            
        # Delete marked for deletion
        for obj in formset.deleted_objects:
            obj.delete()
            
        # Call formset's save_m2m
        formset.save_m2m()
        
        # Recalculate totals for the order if this is the OrderItemInline formset
        if instances and isinstance(instances[0], OrderItem):
            order = form.instance
            
            # Manually calculate totals
            subtotal = OrderItem.objects.filter(order=order).aggregate(
                subtotal=Sum(F('quantity') * F('price')))['subtotal'] or 0
            
            # Calculate discount
            if order.discount_percentage > 0:
                order.discount_amount = subtotal * (order.discount_percentage / 100)
            
            # Calculate tax
            tax_amount = (subtotal - order.discount_amount) * (order.tax_percentage / 100)
            
            # Calculate total
            order.total_amount = subtotal - order.discount_amount + tax_amount + order.shipping_cost
            
            # Save the order without recalculating totals
            order.save(calculate_total=False)

# Supplier Payment Admin
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'purchase_order', 'amount', 'payment_date', 'payment_method', 'created_by')
    list_filter = ('payment_method', 'payment_date', 'supplier')
    search_fields = ('supplier__name', 'reference_number', 'notes')
    date_hierarchy = 'payment_date'

# Client Payment Admin
class ClientPaymentAdmin(admin.ModelAdmin):
    list_display = ('client', 'order', 'amount', 'payment_date', 'payment_method', 'created_by')
    list_filter = ('payment_method', 'payment_date', 'client')
    search_fields = ('client__name', 'reference_number', 'notes')
    date_hierarchy = 'payment_date'

# Expense Admin
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'payment_method', 'created_by')
    list_filter = ('category', 'payment_method', 'date')
    search_fields = ('description', 'reference_number')
    date_hierarchy = 'date'

# Transaction Admin
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'transaction_type', 'amount', 'date', 'reference', 'created_by')
    list_filter = ('transaction_type', 'account', 'date')
    search_fields = ('description', 'reference')
    date_hierarchy = 'date'

# User Profile Admin
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'phone')

# Register all models with their custom admin classes
admin.site.register(Product, ProductAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(Category)
admin.site.register(StorageLocation)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(SupplierPayment, SupplierPaymentAdmin)
admin.site.register(ClientPayment, ClientPaymentAdmin)
admin.site.register(CompanyProfile)
admin.site.register(ExpenseCategory)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(FinancialAccount)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
