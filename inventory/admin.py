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
    autocomplete_fields = ['category', 'supplier', 'location']  # Enable autocomplete for related fields
    search_fields = ['name', 'sku', 'description']  # Enable search for autocomplete
    
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
    autocomplete_fields = ['product']  # Enable autocomplete for product field
    
    # Don't validate the formset until the form is submitted
    validate_min = False
    
    # Don't require any fields in the formset
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.validate_min = False
        return formset
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Override to customize the product dropdown
        """
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.filter(quantity__gt=0)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Order Admin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'order_date', 'status', 'total_amount', 'get_profit', 'created_by')
    list_filter = ('status', 'order_date', 'client')
    search_fields = ('invoice_number', 'client__name', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'total_amount')
    inlines = [OrderItemInline]
    autocomplete_fields = ['client']  # Enable autocomplete for client field
    
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
        if not obj.created_by:
            obj.created_by = request.user
            
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
        # Check if the formset is valid
        if not formset.is_valid():
            return
            
        instances = formset.save(commit=False)
        
        # Save new instances
        for instance in instances:
            # Skip empty forms
            if not instance.product_id or not instance.quantity:
                continue
                
            instance.save()
            
        # Delete marked for deletion
        for obj in formset.deleted_objects:
            obj.delete()
            
        # Call formset's save_m2m
        formset.save_m2m()
        
        # Recalculate totals for the order
        order = form.instance
        
        # Manually calculate totals
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

# Category Admin
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'description')

# StorageLocation Admin
class StorageLocationAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'description', 'address')

# Register all models with their custom admin classes
admin.site.register(Product, ProductAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(StorageLocation, StorageLocationAdmin)
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
