from django.db import models
from django.utils import timezone
from django.apps import apps
from django.contrib.auth.models import User
from django.db.models import Sum, F, ExpressionWrapper, DecimalField as ModelDecimalField
from django.db.models.signals import post_save
from django.dispatch import receiver

# Company Profile model
class CompanyProfile(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return self.name

# Category model
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

# Storage Location model
class StorageLocation(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

# Supplier model
class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_total_purchases(self):
        # More efficient calculation using a single query
        from django.db.models import Sum, F
        
        return PurchaseOrderItem.objects.filter(
            purchase_order__supplier=self
        ).annotate(
            item_total=F('quantity') * F('price')
        ).aggregate(total=Sum('item_total'))['total'] or 0
    
    def get_outstanding_balance(self):
        # Calculate in a single method to avoid multiple database queries
        from django.db.models import Sum, F
        
        total_purchases = self.get_total_purchases()
        
        total_payments = SupplierPayment.objects.filter(supplier=self).aggregate(
            total=Sum('amount'))['total'] or 0
            
        return total_purchases - total_payments

# Product model
class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    reorder_level = models.PositiveIntegerField(default=10)
    location = models.ForeignKey(StorageLocation, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_profit_margin(self):
        if self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price) * 100
        return 0
    
    def is_low_stock(self):
        return self.quantity <= self.reorder_level
    
    def get_total_sales(self):
        return OrderItem.objects.filter(product=self).aggregate(
            total=Sum(F('quantity') * F('price')))['total'] or 0
    
    def get_total_profit(self):
        return OrderItem.objects.filter(product=self).aggregate(
            total=Sum((F('price') - F('product__cost_price')) * F('quantity')))['total'] or 0

# Stock model
class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_received = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    date_received = models.DateField()
    stock_type = models.CharField(max_length=20, choices=[('received', 'Received'), ('sold', 'Sold')], default='received')
    timestamp = models.DateTimeField(default=timezone.now)
    location = models.ForeignKey(StorageLocation, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.product.name} - {self.date_received}'

# Purchase Order model
class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    reference_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PO-{self.id} - {self.supplier.name} on {self.date}"
    
    def get_total(self):
        try:
            return self.purchaseorderitem_set.aggregate(
                total=Sum(F('quantity') * F('price')))['total'] or 0
        except Exception as e:
            print(f"Error calculating purchase order total: {str(e)}")
            return 0
    
    def calculate_total(self):
        # Only calculate if we have a primary key
        if self.pk:
            try:
                # Get the total from all items
                total = self.get_total()
                return total
            except Exception as e:
                print(f"Error in calculate_total: {str(e)}")
                return 0
        return 0
    
    def save(self, *args, **kwargs):
        # Check if we should skip calculating the total
        calculate_total = kwargs.pop('calculate_total', True)
        
        if not self.reference_number:
            self.reference_number = f"PO-{timezone.now().strftime('%Y%m%d')}-{PurchaseOrder.objects.count() + 1}"
        
        # First save to get a primary key if this is a new instance
        is_new = self.pk is None
        if is_new:
            # For new instances, don't calculate total yet
            super().save(*args, **kwargs)
        
        # Now we can safely access related items
        if not is_new:
            # For existing instances, save normally
            super().save(*args, **kwargs)
    
    def change_status(self, new_status):
        """
        Change the status of the purchase order and handle inventory updates
        """
        old_status = self.status
        self.status = new_status
        self.save()
        
        # If changing to received, update inventory
        if old_status != 'received' and new_status == 'received':
            self.update_inventory()
    
    def update_inventory(self):
        """
        Update inventory based on purchase order items
        """
        for item in self.purchaseorderitem_set.all():
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
                notes=f"Received in purchase order #{self.reference_number}"
            )

# Purchase Order Item model
class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"
    
    def get_total(self):
        return self.quantity * self.price
    
    def save(self, *args, **kwargs):
        # Check if this is a new item or an update
        is_new = self.pk is None
        
        # If updating, handle inventory changes
        if not is_new:
            try:
                old_item = PurchaseOrderItem.objects.get(pk=self.pk)
                old_product = old_item.product
                old_quantity = old_item.quantity
                
                # If the product changed or quantity changed, and status is received
                if (old_product != self.product or old_quantity != self.quantity) and self.purchase_order.status == 'received':
                    # Revert old product quantity
                    old_product.quantity -= old_quantity
                    old_product.save()
                    
                    # Update new product quantity
                    self.product.quantity += self.quantity
                    self.product.save()
            except PurchaseOrderItem.DoesNotExist:
                pass
        # For new items, update inventory if status is received
        elif self.purchase_order.status == 'received':
            self.product.quantity += self.quantity
            self.product.save()
            
            # Create stock record
            Stock.objects.create(
                product=self.product,
                quantity_received=self.quantity,
                quantity_sold=0,
                date_received=timezone.now().date(),
                stock_type='received',
                notes=f"Received in purchase order #{self.purchase_order.reference_number if self.purchase_order.reference_number else 'New PO'}"
            )
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # If status is received, revert inventory changes
        if self.purchase_order.status == 'received':
            self.product.quantity -= self.quantity
            self.product.save()
        
        super().delete(*args, **kwargs)

# Supplier Payment model
class SupplierPayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment to {self.supplier.name} - {self.amount}"

# Client model
class Client(models.Model):
    TYPE_CHOICES = [
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('wholesale', 'Wholesale'),
    ]
    
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='regular')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_total_orders(self):
        # More efficient calculation using a single query with caching
        from django.db.models import Sum
        
        # Use select_related to reduce database queries
        return Order.objects.filter(client=self).aggregate(
            total=Sum('total_amount'))['total'] or 0
    
    def get_outstanding_balance(self):
        # Calculate in a single method to avoid multiple database queries
        from django.db.models import Sum, F
        
        # Get total orders amount
        total_orders = self.get_total_orders()
        
        # Get total payments
        total_payments = ClientPayment.objects.filter(client=self).aggregate(
            total=Sum('amount'))['total'] or 0
            
        # Return the difference
        return total_orders - total_payments

# Order (Sales) model
class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order-{self.id} for {self.client.name} on {self.order_date}"
    
    def calculate_total(self):
        # Only calculate from order items if the instance has a primary key
        if self.pk:
            try:
                # Calculate subtotal from order items
                subtotal = self.orderitem_set.aggregate(
                    subtotal=Sum(F('quantity') * F('price')))['subtotal'] or 0
                
                # Calculate discount
                if self.discount_percentage > 0:
                    self.discount_amount = subtotal * (self.discount_percentage / 100)
                
                # Calculate total
                self.total_amount = subtotal - self.discount_amount + self.shipping_cost
            except Exception as e:
                # Log the error but don't crash
                print(f"Error calculating total: {str(e)}")
                # For errors, just use the current value
                pass
        else:
            # For new instances, just set a default value
            self.total_amount = 0
            
        return self.total_amount
    
    def save(self, *args, **kwargs):
        # Check if we should skip calculating the total
        calculate_total = kwargs.pop('calculate_total', True)
        
        if not self.invoice_number:
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{Order.objects.count() + 1}"
        
        # First save to get a primary key if this is a new instance
        is_new = self.pk is None
        if is_new:
            # For new instances, don't calculate total yet
            super().save(*args, **kwargs)
            
        # Now calculate total if requested and not a new instance
        if calculate_total and (not is_new or self.pk):
            self.calculate_total()
            # Save again with the calculated total
            if is_new:
                # We already saved once, so we need to save again
                super().save(*args, **kwargs)
        
        if not is_new:
            # For existing instances, save normally
            super().save(*args, **kwargs)
    
    def get_profit(self):
        return self.orderitem_set.aggregate(
            profit=Sum((F('price') - F('product__cost_price')) * F('quantity')))['profit'] or 0

# Order Item model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"
    
    def get_total(self):
        return self.quantity * self.price
    
    def get_profit(self):
        return (self.price - self.product.cost_price) * self.quantity
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Check if we have enough inventory
        if self.product and self.quantity and self.product.quantity is not None and self.quantity > self.product.quantity:
            raise ValidationError(f"Not enough inventory for {self.product.name}. Only {self.product.quantity} available.")
    
    def save(self, *args, **kwargs):
        # Skip validation and inventory updates if product is not set
        # This is needed for the admin interface when creating a new order
        if not hasattr(self, 'product') or self.product is None:
            return super().save(*args, **kwargs)
            
        # Validate before saving
        self.clean()
        
        # Check if this is a new item or an update
        is_new = self.pk is None
        
        # If updating, restore the old quantity to the product
        if not is_new:
            try:
                old_item = OrderItem.objects.get(pk=self.pk)
                old_product = old_item.product
                old_quantity = old_item.quantity
                
                # If the product changed or quantity changed, update inventory
                if old_product != self.product or old_quantity != self.quantity:
                    # Restore old product quantity
                    old_product.quantity += old_quantity
                    old_product.save()
                    
                    # Deduct new product quantity
                    self.product.quantity -= self.quantity
                    self.product.save()
            except OrderItem.DoesNotExist:
                pass
        else:
            # For new items, just deduct the quantity
            self.product.quantity -= self.quantity
            self.product.save()
            
            # Create stock record for the sale
            Stock.objects.create(
                product=self.product,
                quantity_received=0,
                quantity_sold=self.quantity,
                date_received=timezone.now().date(),
                stock_type='sold',
                notes=f"Sold in order #{self.order.invoice_number if self.order.invoice_number else 'New Order'}"
            )
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Restore product quantity when deleting an order item
        self.product.quantity += self.quantity
        self.product.save()
        
        super().delete(*args, **kwargs)

# Client Payment model
class ClientPayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment from {self.client.name} - {self.amount}"

# Expense Category model
class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Expense Categories"

# Expense model
class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=ClientPayment.PAYMENT_METHOD_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.category.name} - {self.amount} on {self.date}"

# Financial Account model
class FinancialAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.name} ({self.account_type})"

# Transaction model
class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]
    
    account = models.ForeignKey(FinancialAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True, null=True)
    related_account = models.ForeignKey(FinancialAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='related_transactions')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} on {self.date}"

# User Profile model
class UserProfile(models.Model):
    USER_ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('sales', 'Sales Staff'),
        ('inventory', 'Inventory Staff'),
        ('accounting', 'Accounting Staff'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLE_CHOICES, default='sales')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Create UserProfile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
