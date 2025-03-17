from django.db import models
from django.utils.translation import gettext_lazy as _

class Customer(models.Model):
    name = models.CharField(_('Name'), max_length=255)
    phone = models.CharField(_('Phone'), max_length=20)
    email = models.EmailField(_('Email'), blank=True)
    address = models.TextField(_('Address'), blank=True)
    debt = models.DecimalField(_('Debt'), max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(_('Created Date'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
    
    def update_debt(self):
        """Update customer debt based on transactions"""
        from sales.models import Sale, CustomerPayment
        total_sales = Sale.objects.filter(customer=self).aggregate(models.Sum('total_price'))['total_price__sum'] or 0
        total_payments = CustomerPayment.objects.filter(customer=self).aggregate(models.Sum('amount'))['amount__sum'] or 0
        self.debt = total_sales - total_payments
        self.save()
