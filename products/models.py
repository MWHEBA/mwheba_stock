from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Product(models.Model):
    STATUS_CHOICES = (
        ('available', _('Available')),
        ('low_stock', _('Low Stock')),
        ('out_of_stock', _('Out of Stock')),
    )
    
    name = models.CharField(_('Name'), max_length=255)
    sku = models.CharField(_('SKU'), max_length=50, unique=True)
    supplier_code = models.CharField(_('Supplier Code'), max_length=50, blank=True)
    purchase_price = models.DecimalField(_('Purchase Price'), max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(_('Sale Price'), max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(_('Quantity'), default=0)
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.SET_NULL, null=True, related_name='products', verbose_name=_('Supplier'))
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='available')
    image = models.ImageField(_('Image'), upload_to='products/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_products', verbose_name=_('Created By'))
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated Date'), auto_now=True)
    
    class Meta:
        verbose_name = _('المنتج')
        verbose_name_plural = _('المنتجات')
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def save(self, *args, **kwargs):
        # Update product status based on quantity
        if self.quantity <= 0:
            self.status = 'out_of_stock'
        elif self.quantity <= 5:  # Arbitrary low stock threshold
            self.status = 'low_stock'
        else:
            self.status = 'available'
            
        # Create purchase price history entry if price changed
        if self.pk:
            old_product = Product.objects.get(pk=self.pk)
            if old_product.purchase_price != self.purchase_price:
                PurchasePriceHistory.objects.create(
                    product=self,
                    purchase_price=self.purchase_price
                )
        else:
            # For new products, will create history after save
            is_new = True
            
        super().save(*args, **kwargs)
        
        # Create initial price history for new products
        if not self.pk and is_new:
            PurchasePriceHistory.objects.create(
                product=self,
                purchase_price=self.purchase_price
            )

class PurchasePriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_history', verbose_name=_('Product'))
    purchase_price = models.DecimalField(_('Purchase Price'), max_digits=10, decimal_places=2)
    date_changed = models.DateTimeField(_('Date of Change'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('سجل سعر الشراء')
        verbose_name_plural = _('سجلات أسعار الشراء')
        ordering = ['-date_changed']
    
    def __str__(self):
        return f"{self.product.name} - {self.purchase_price} - {self.date_changed}"
