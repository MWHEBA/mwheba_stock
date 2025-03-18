from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Supplier, SupplierCategory

class SupplierForm(forms.ModelForm):
    """نموذج إضافة/تعديل المورد"""
    
    class Meta:
        model = Supplier
        fields = ['name', 'code', 'phone', 'email', 'address', 'category',
                 'tax_number', 'credit_limit', 'is_preferred', 'status',
                 'payment_terms', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم المورد')}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('سيتم توليده تلقائياً')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': _('رقم الهاتف')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': _('example@domain.com')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('العنوان')}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': _('الرقم الضريبي')}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'is_preferred': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('مثال: 30 يوم، دفع فوري، الخ')}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('ملاحظات عن المورد')}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean_code(self):
        """التحقق من صحة الكود وتوليده تلقائياً إذا كان فارغاً"""
        code = self.cleaned_data.get('code')
        # إذا كان الكود فارغاً، سيتم توليده تلقائياً في دالة save في النموذج
        if code and Supplier.objects.exclude(pk=self.instance.pk if self.instance.pk else None).filter(code=code).exists():
            raise forms.ValidationError(_("يوجد مورد آخر بنفس الكود"))
        return code


class SupplierCategoryForm(forms.ModelForm):
    """نموذج إضافة/تعديل تصنيف الموردين"""
    
    class Meta:
        model = SupplierCategory
        fields = ['name', 'description', 'color_code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم التصنيف')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('وصف التصنيف')}),
            'color_code': forms.Select(attrs={'class': 'form-select'}, 
                                      choices=[('primary', 'أزرق'), ('success', 'أخضر'), ('danger', 'أحمر'),
                                              ('warning', 'برتقالي'), ('info', 'سماوي'), ('secondary', 'رمادي')])
        }


class SupplierSearchForm(forms.Form):
    """نموذج البحث المتقدم عن الموردين"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('بحث بالاسم، الهاتف، البريد الإلكتروني...')
        })
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('تصنيف المورد')
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', _("جميع الحالات")),
            ('active', _("نشط")),
            ('inactive', _("غير نشط")),
            ('blocked', _("محظور")),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('حالة المورد')
        })
    )
    
    payment_status = forms.ChoiceField(
        required=False,
        choices=[
            ('', _("جميع الموردين")),
            ('with_debts', _("لهم مستحقات")),
            ('no_debts', _("بدون مستحقات")),
            ('exceed_limit', _("تجاوزوا حد الائتمان")),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('حالة المستحقات')
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('name', _("الاسم (أ-ي)")),
            ('-name', _("الاسم (ي-أ)")),
            ('-created_at', _("الأحدث أولاً")),
            ('created_at', _("الأقدم أولاً")),
            ('-total_purchases', _("الأكثر مشتريات")),
            ('-balance', _("الأعلى مستحقات")),
            ('balance', _("الأقل مستحقات")),
        ],
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('ترتيب حسب')
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إضافة التصنيفات بشكل ديناميكي
        categories = SupplierCategory.objects.all()
        category_choices = [('', _('جميع التصنيفات'))]
        category_choices.extend([(str(cat.id), cat.name) for cat in categories])
        self.fields['category'].choices = category_choices
