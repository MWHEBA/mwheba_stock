from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.core.validators import RegexValidator

class SupplierCategory(models.Model):
    """تصنيف الموردين (مثل: منتجات غذائية، إلكترونيات، مستوردين، إلخ)"""
    name = models.CharField(_("اسم التصنيف"), max_length=100)
    description = models.TextField(_("وصف"), blank=True, null=True)
    color_code = models.CharField(_("كود اللون"), max_length=20, default='primary', 
                               help_text=_("اسم اللون في Bootstrap مثل: primary, success, danger"))
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("تصنيف المورد")
        verbose_name_plural = _("تصنيفات الموردين")
        ordering = ['name']
        
    def __str__(self):
        return self.name

class Supplier(models.Model):
    """نموذج بيانات الموردين المحسّن"""
    
    # خيارات حالة المورد
    STATUS_CHOICES = (
        ('active', _('نشط')),
        ('inactive', _('غير نشط')),
        ('blocked', _('محظور')),
    )
    
    # مدقق لرقم الهاتف
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message=_("يجب أن يكون رقم الهاتف بتنسيق: '+999999999'. يُسمح بـ 15 رقم.")
    )
    
    # البيانات الأساسية
    name = models.CharField(_("اسم المورد"), max_length=255)
    code = models.CharField(_("كود المورد"), max_length=20, unique=True, blank=True, null=True)
    phone = models.CharField(_("رقم الهاتف"), validators=[phone_regex], max_length=20, blank=True, null=True)
    alternative_phone = models.CharField(_("رقم هاتف بديل"), max_length=20, blank=True, null=True)
    email = models.EmailField(_("البريد الإلكتروني"), blank=True, null=True)
    address = models.CharField(_("العنوان"), max_length=255, blank=True, null=True)
    status = models.CharField(_("الحالة"), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # التصنيف والمعلومات الإضافية
    category = models.ForeignKey(SupplierCategory, verbose_name=_("التصنيف"), on_delete=models.SET_NULL, 
                               related_name='suppliers', blank=True, null=True)
    is_preferred = models.BooleanField(_("مورد مفضل"), default=False)
    credit_limit = models.DecimalField(_("حد الائتمان"), max_digits=10, decimal_places=2, default=0)
    tax_number = models.CharField(_("الرقم الضريبي"), max_length=50, blank=True, null=True)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    payment_terms = models.CharField(_("شروط الدفع"), max_length=255, blank=True, null=True)
    
    # البيانات المالية
    balance = models.DecimalField(_("المستحقات"), max_digits=10, decimal_places=2, default=0)
    total_purchases = models.DecimalField(_("إجمالي المشتريات"), max_digits=12, decimal_places=2, default=0)
    
    # البيانات الزمنية
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    last_purchase_date = models.DateField(_("تاريخ آخر شراء"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("مورد")
        verbose_name_plural = _("الموردين")
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        # إزالة توليد الكود التلقائي من هنا لنسمح بتعديله يدوياً
        # إذا لم يتم تحديد الكود، سيتم توليده تلقائياً في نموذج الإضافة
        if not self.code:
            prefix = "SUPP"
            last_supplier = Supplier.objects.all().order_by('-id').first()
            if last_supplier:
                last_id = last_supplier.id
                self.code = f"{prefix}{last_id + 1:04d}"
            else:
                self.code = f"{prefix}0001"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('supplier-detail', kwargs={'pk': self.pk})
        
    def get_status_display_class(self):
        """تقديم تصنيف Bootstrap CSS المناسب لحالة المورد"""
        status_classes = {
            'active': 'success',
            'inactive': 'warning',
            'blocked': 'danger'
        }
        return status_classes.get(self.status, 'secondary')
    
    def days_since_last_purchase(self):
        """عدد الأيام منذ آخر عملية شراء"""
        if not self.last_purchase_date:
            return None
        return (timezone.now().date() - self.last_purchase_date).days
    
    def update_financial_data(self):
        """تحديث البيانات المالية للمورد"""
        from purchases.models import Purchase, Payment
        
        # حساب إجمالي المشتريات
        purchases_data = Purchase.objects.filter(supplier=self).aggregate(
            total=models.Sum('total_amount'),
            last_date=models.Max('purchase_date')
        )
        
        self.total_purchases = purchases_data.get('total') or 0
        
        # تحديث تاريخ آخر عملية شراء
        if purchases_data.get('last_date'):
            self.last_purchase_date = purchases_data.get('last_date')
        
        # حساب المستحقات (الفواتير الغير مدفوعة)
        unpaid_purchases = Purchase.objects.filter(
            supplier=self, 
            status__in=['pending', 'partially_paid']
        ).aggregate(total=models.Sum('due_amount'))['total'] or 0
        
        self.balance = unpaid_purchases
        self.save()
