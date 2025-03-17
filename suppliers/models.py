from django.db import models
from django.utils.translation import gettext_lazy as _

class Supplier(models.Model):
    name = models.CharField(_('Name'), max_length=255)
    code = models.CharField(_('Supplier Code'), max_length=50, unique=True)
    phone = models.CharField(_('Phone'), max_length=20)
    email = models.EmailField(_('Email'), blank=True)
    address = models.TextField(_('Address'), blank=True)
    debt = models.DecimalField(_('Debt'), max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def update_debt(self):
        """Update supplier debt based on transactions"""
        from purchases.models import Purchase, Payment
        total_purchases = Purchase.objects.filter(supplier=self).aggregate(models.Sum('total_price'))['total_price__sum'] or 0
        total_payments = Payment.objects.filter(supplier=self).aggregate(models.Sum('amount'))['amount__sum'] or 0
        self.debt = total_purchases - total_payments
        self.save()
