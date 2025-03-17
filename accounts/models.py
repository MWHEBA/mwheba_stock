from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import random

class User(AbstractUser):
    phone_number = models.CharField(_("رقم الهاتف"), max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)  # Add this line
    position = models.CharField(_("المسمى الوظيفي"), max_length=100, blank=True, null=True)
    image = models.ImageField(_("الصورة الشخصية"), upload_to='users/', blank=True, null=True)
    last_activity = models.DateTimeField(_("آخر نشاط"), blank=True, null=True)
    color_code = models.CharField(_("رمز اللون"), max_length=10, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.color_code:
            color_options = [
                'primary', 'secondary', 'success', 'danger', 
                'warning', 'info', 'dark'
            ]
            self.color_code = random.choice(color_options)
        super().save(*args, **kwargs)

    def get_initials(self):
        initials = ""
        if self.first_name:
            initials += self.first_name[0]
        if self.last_name:
            initials += self.last_name[0]
        if not initials:
            initials = self.username[0:2]
        return initials.upper()

    def get_color_class(self):
        return self.color_code or 'primary'

    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("المستخدمين")


class ActivityLog(models.Model):
    """Log for user activities in the system"""
    ACTIVITY_CHOICES = (
        ('login', _('تسجيل دخول')),
        ('logout', _('تسجيل خروج')),
        ('create', _('إنشاء')),
        ('update', _('تعديل')),
        ('delete', _('حذف')),
        ('export', _('تصدير')),
        ('import', _('استيراد')),
        ('other', _('أخرى')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("المستخدم"))
    activity_type = models.CharField(_("نوع النشاط"), max_length=20, choices=ACTIVITY_CHOICES, default='other')
    description = models.TextField(_("الوصف"))
    model_name = models.CharField(_("اسم الموديل"), max_length=100, blank=True, null=True)
    object_id = models.PositiveIntegerField(_("معرف الكائن"), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_("عنوان IP"), blank=True, null=True)
    user_agent = models.TextField(_("متصفح المستخدم"), blank=True, null=True)
    timestamp = models.DateTimeField(_("التوقيت"), auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}"

    class Meta:
        verbose_name = _("سجل النشاط")
        verbose_name_plural = _("سجلات النشاط")
        ordering = ['-timestamp']


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', _('معلومات')),
        ('success', _('نجاح')),
        ('warning', _('تحذير')),
        ('danger', _('خطر')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("المستخدم"))
    title = models.CharField(_("العنوان"), max_length=255)
    text = models.TextField(_("النص"))
    notification_type = models.CharField(_("نوع الإشعار"), max_length=20, choices=NOTIFICATION_TYPES, default='info')
    icon = models.CharField(_("الأيقونة"), max_length=50, blank=True, null=True)
    url = models.CharField(_("الرابط"), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    is_read = models.BooleanField(_("مقروء"), default=False)

    def __str__(self):
        return self.title

    @property
    def icon_class(self):
        return {
            'info': 'bg-info',
            'success': 'bg-success',
            'warning': 'bg-warning',
            'danger': 'bg-danger',
        }.get(self.notification_type, 'bg-secondary')

    class Meta:
        verbose_name = _("إشعار")
        verbose_name_plural = _("الإشعارات")
        ordering = ['-created_at']


class SystemSettings(models.Model):
    key = models.CharField(_("المفتاح"), max_length=100, unique=True)
    value = models.TextField(_("القيمة"))
    value_type = models.CharField(_("نوع القيمة"), max_length=20, 
                                 choices=[('str', 'نص'), ('int', 'عدد صحيح'), 
                                          ('float', 'عدد عشري'), ('bool', 'قيمة منطقية'), 
                                          ('json', 'JSON')])
    description = models.TextField(_("الوصف"), blank=True, null=True)
    category = models.CharField(_("الفئة"), max_length=50, default='general')
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                  verbose_name=_("تم التحديث بواسطة"))

    def __str__(self):
        return f"{self.key}: {self.value[:30]}"

    class Meta:
        verbose_name = _("إعداد النظام")
        verbose_name_plural = _("إعدادات النظام")
        ordering = ['category', 'key']
