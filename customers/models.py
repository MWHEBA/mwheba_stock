from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.core.validators import RegexValidator

class CustomerCategory(models.Model):
    """تصنيف العملاء (مثل: VIP، شركات، أفراد، إلخ)"""
    name = models.CharField(_("اسم التصنيف"), max_length=100)
    color_code = models.CharField(_("لون التصنيف"), max_length=20, default="primary")
    description = models.TextField(_("وصف"), blank=True, null=True)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)

    class Meta:
        verbose_name = _("تصنيف العملاء")
        verbose_name_plural = _("تصنيفات العملاء")
        ordering = ['name']

    def __str__(self):
        return self.name
        
    def customer_count(self):
        return self.customers.count()

class Customer(models.Model):
    """نموذج بيانات العملاء المحسّن"""
    
    # خيارات حالة العميل
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
    name = models.CharField(_("اسم العميل"), max_length=255)
    code = models.CharField(_("كود العميل"), max_length=20, unique=True, blank=True, null=True)
    phone = models.CharField(_("رقم الهاتف"), validators=[phone_regex], max_length=20, blank=True, null=True)
    alternative_phone = models.CharField(_("رقم هاتف بديل"), max_length=20, blank=True, null=True)
    email = models.EmailField(_("البريد الإلكتروني"), blank=True, null=True)
    address = models.CharField(_("العنوان"), max_length=255, blank=True, null=True)
    status = models.CharField(_("الحالة"), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # التصنيف والمعلومات الإضافية
    category = models.ForeignKey(CustomerCategory, verbose_name=_("التصنيف"), on_delete=models.SET_NULL, 
                               related_name='customers', blank=True, null=True)
    credit_limit = models.DecimalField(_("حد الائتمان"), max_digits=10, decimal_places=2, default=0)
    tax_number = models.CharField(_("الرقم الضريبي"), max_length=50, blank=True, null=True)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    
    # البيانات المالية
    debt = models.DecimalField(_("المديونية"), max_digits=10, decimal_places=2, default=0)
    total_sales = models.DecimalField(_("إجمالي المبيعات"), max_digits=12, decimal_places=2, default=0)
    points = models.IntegerField(_("نقاط الولاء"), default=0)
    
    # البيانات الزمنية
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    last_purchase_date = models.DateField(_("تاريخ آخر شراء"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("عميل")
        verbose_name_plural = _("العملاء")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['phone']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['debt']),
        ]
        
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        # إنشاء كود العميل تلقائيًا إذا لم يكن موجودًا
        if not self.code:
            # استخدم الاختصار الأول من الاسم + التاريخ + رقم عشوائي
            import random
            from datetime import datetime
            name_prefix = ''.join(word[0].upper() for word in self.name.split()[:2])
            date_suffix = datetime.now().strftime('%y%m%d')
            random_suffix = random.randint(100, 999)
            self.code = f"C{name_prefix}{date_suffix}{random_suffix}"
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('customer-detail', kwargs={'pk': self.pk})
    
    def get_status_display_class(self):
        """تقديم تصنيف Bootstrap CSS المناسب لحالة العميل"""
        return {
            'active': 'success',
            'inactive': 'warning',
            'blocked': 'danger',
        }.get(self.status, 'secondary')
    
    def days_since_last_purchase(self):
        """عدد الأيام منذ آخر عملية شراء"""
        if self.last_purchase_date:
            return (timezone.now().date() - self.last_purchase_date).days
        return None
    
    def update_financial_data(self):
        """تحديث البيانات المالية للعميل"""
        from sales.models import Sale, CustomerPayment
        
        # حساب إجمالي المبيعات
        sales_data = Sale.objects.filter(customer=self).aggregate(
            total=models.Sum('total_price'),
            last_date=models.Max('sale_date')
        )
        
        self.total_sales = sales_data.get('total') or 0
        
        # تحديث تاريخ آخر عملية شراء
        if sales_data.get('last_date'):
            self.last_purchase_date = sales_data.get('last_date')
        
        # حساب المديونية (الفواتير الغير مدفوعة)
        unpaid_sales = Sale.objects.filter(
            customer=self, 
            status__in=['unpaid', 'partially_paid']
        ).aggregate(total=models.Sum('remaining_amount'))
        
        self.debt = unpaid_sales.get('total') or 0
        
        # تحديث النقاط (مثال: نقطة لكل 100 ج.م)
        self.points = int(self.total_sales / 100)
        
        # حفظ التغييرات
        self.save(update_fields=['total_sales', 'last_purchase_date', 'debt', 'points'])
        
        return self.debt
    
    def is_vip(self):
        """تحديد ما إذا كان العميل VIP بناءً على التصنيف أو المبيعات"""
        if self.category and self.category.name.lower() == 'vip':
            return True
        return self.total_sales > 10000  # مثال: أكثر من 10000 ج.م
    
    def get_credit_status(self):
        """حالة الائتمان للعميل"""
        if self.credit_limit == 0:
            return 'no_credit'  # لا يوجد حد ائتماني
        
        if self.debt > self.credit_limit:
            return 'exceeded'  # تجاوز الحد
            
        percentage = (self.debt / self.credit_limit) * 100
        
        if percentage >= 80:
            return 'critical'  # اقترب من الحد
        elif percentage >= 50:
            return 'warning'  # تحذير
            
        return 'good'  # جيد
