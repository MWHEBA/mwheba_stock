from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Sale(models.Model):
    STATUS_CHOICES = (
        ('paid', _('Paid')),
        ('unpaid', _('Unpaid')),
        ('partially_paid', _('Partially Paid')),
    )
    
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='sales', verbose_name=_('Customer'))
    sale_date = models.DateTimeField(_('Sale Date'), auto_now_add=True)
    total_quantity = models.PositiveIntegerField(_('Total Quantity'), default=0)
    total_price = models.DecimalField(_('Total Price'), max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(_('Discount'), max_digits=10, decimal_places=2, default=0)
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='unpaid')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_sales', verbose_name=_('Created By'))
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated Date'), auto_now=True)
    
    class Meta:
        verbose_name = _('Sale')
        verbose_name_plural = _('Sales')
    
    def __str__(self):
        return f"{_('Invoice')}-{self.id}: {self.customer.name} ({self.sale_date.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        # Calculate total from sale items if not set
        if not self.total_price:
            self.total_price = sum(item.total_price for item in self.items.all())
        
        # Calculate total quantity if not set
        if not self.total_quantity:
            self.total_quantity = sum(item.quantity for item in self.items.all())
            
        # Calculate status based on payments
        if self.id:
            total_paid = sum(payment.amount for payment in self.payments.all())
            if total_paid >= self.total_price:
                self.status = 'paid'
            elif total_paid > 0:
                self.status = 'partially_paid'
            else:
                self.status = 'unpaid'
            
        super().save(*args, **kwargs)
        
        # Update customer debt
        self.customer.update_debt()

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items', verbose_name=_('Sale'))
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='sale_items', verbose_name=_('Product'))
    quantity = models.PositiveIntegerField(_('Quantity'), default=1)
    price = models.DecimalField(_('Unit Price'), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_('Total Price'), max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _('Sale Item')
        verbose_name_plural = _('Sale Items')
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)
        
        # Update sale total
        sale = self.sale
        sale.total_price = sum(item.total_price for item in sale.items.all())
        sale.total_quantity = sum(item.quantity for item in sale.items.all())
        sale.save()
        
        # Update product quantity
        self.product.quantity -= self.quantity
        self.product.save()

class CustomerPayment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments', verbose_name=_('Sale'))
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='payments', verbose_name=_('Customer'))
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(_('Payment Date'), auto_now_add=True)
    notes = models.TextField(_('Notes'), blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_customer_payments', verbose_name=_('Created By'))
    
    class Meta:
        verbose_name = _('Customer Payment')
        verbose_name_plural = _('Customer Payments')
    
    def __str__(self):
        return f"{_('Payment')} {self.id}: {self.customer.name} - {self.amount} EGP"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update sale status
        self.sale.save()  # This will trigger status recalculation
        # Update customer debt after payment
        self.customer.update_debt()
