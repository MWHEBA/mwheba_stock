from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Purchase(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('canceled', _('Canceled')),
    )
    
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, related_name='purchases', verbose_name=_('Supplier'))
    order_date = models.DateTimeField(_('Order Date'), auto_now_add=True)
    total_quantity = models.PositiveIntegerField(_('Total Quantity'), default=0)
    total_price = models.DecimalField(_('Total Price'), max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(_('Discount'), max_digits=10, decimal_places=2, default=0)
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_purchases', verbose_name=_('Created By'))
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated Date'), auto_now=True)
    
    class Meta:
        verbose_name = _('Purchase')
        verbose_name_plural = _('Purchases')
    
    def __str__(self):
        return f"{_('PO')}-{self.id}: {self.supplier.name} ({self.order_date.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        # Calculate total from purchase items if not set
        if not self.total_price:
            self.total_price = sum(item.total_price for item in self.items.all())
        
        # Calculate total quantity if not set
        if not self.total_quantity:
            self.total_quantity = sum(item.quantity for item in self.items.all())
            
        super().save(*args, **kwargs)
        
        # Update supplier debt
        if self.status == 'completed':
            self.supplier.update_debt()

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items', verbose_name=_('Purchase'))
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='purchase_items', verbose_name=_('Product'))
    quantity = models.PositiveIntegerField(_('Quantity'), default=1)
    price = models.DecimalField(_('Unit Price'), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_('Total Price'), max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _('Purchase Item')
        verbose_name_plural = _('Purchase Items')
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)
        
        # Update purchase total
        purchase = self.purchase
        purchase.total_price = sum(item.total_price for item in purchase.items.all())
        purchase.total_quantity = sum(item.quantity for item in purchase.items.all())
        purchase.save()
        
        # Update product quantity if purchase is completed
        if self.purchase.status == 'completed':
            self.product.quantity += self.quantity
            self.product.save()

class Payment(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='payments', verbose_name=_('Purchase'))
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, related_name='payments', verbose_name=_('Supplier'))
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(_('Payment Date'), auto_now_add=True)
    notes = models.TextField(_('Notes'), blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_supplier_payments', verbose_name=_('Created By'))
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
    
    def __str__(self):
        return f"{_('Payment')} {self.id}: {self.supplier.name} - {self.amount} EGP"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update supplier debt after payment
        self.supplier.update_debt()
