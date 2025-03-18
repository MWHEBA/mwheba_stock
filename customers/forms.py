from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Customer, CustomerCategory

class CustomerCategoryForm(forms.ModelForm):
    """نموذج إضافة/تعديل تصنيف العملاء"""
    
    class Meta:
        model = CustomerCategory
        fields = ['name', 'description', 'color_code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('اسم التصنيف')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('وصف التصنيف')}),
            'color_code': forms.Select(attrs={'class': 'form-select'}, 
                                      choices=[('primary', 'أزرق'), ('success', 'أخضر'), ('danger', 'أحمر'),
                                              ('warning', 'برتقالي'), ('info', 'سماوي'), ('secondary', 'رمادي')])
        }

class CustomerForm(forms.ModelForm):
    """نموذج إضافة وتعديل العملاء مع واجهة متقدمة"""
    
    # إضافة حقل الكود للنموذج وجعله قابلاً للتحرير
    code = forms.CharField(
        label=_('كود العميل'),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'سيتم توليده تلقائياً إذا تركته فارغاً'}),
        help_text=_('يمكنك تخصيص كود العميل أو تركه فارغاً ليتم توليده تلقائياً')
    )
    
    class Meta:
        model = Customer
        fields = ['code', 'name', 'phone', 'alternative_phone', 'email', 'address', 'category', 
                 'status', 'credit_limit', 'tax_number', 'notes']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': _('اسم العميل'), 
                'class': 'form-control', 
                'data-bs-toggle': 'tooltip',
                'title': _('أدخل اسم العميل بالكامل')
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': _('رقم الهاتف'), 
                'class': 'form-control phone-input',
                'dir': 'ltr'
            }),
            'alternative_phone': forms.TextInput(attrs={
                'placeholder': _('رقم هاتف بديل'), 
                'class': 'form-control phone-input',
                'dir': 'ltr'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': _('البريد الإلكتروني'),
                'class': 'form-control',
                'dir': 'ltr'
            }),
            'address': forms.TextInput(attrs={
                'placeholder': _('العنوان'),
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select category-select',
                'data-bs-toggle': 'tooltip',
                'title': _('اختر تصنيف العميل')
            }),
            'status': forms.Select(attrs={
                'class': 'form-select status-select'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'data-bs-toggle': 'tooltip',
                'title': _('حد الائتمان المسموح به للعميل (0 = غير محدود)')
            }),
            'tax_number': forms.TextInput(attrs={
                'placeholder': _('الرقم الضريبي إن وجد'),
                'class': 'form-control',
                'dir': 'ltr'
            }),
            'notes': forms.Textarea(attrs={
                'placeholder': _('ملاحظات إضافية'),
                'class': 'form-control',
                'rows': 3
            }),
        }
        
        labels = {
            'name': _('اسم العميل'),
            'phone': _('رقم الهاتف'),
            'alternative_phone': _('رقم هاتف بديل'),
            'email': _('البريد الإلكتروني'),
            'address': _('العنوان'),
            'category': _('التصنيف'),
            'status': _('الحالة'),
            'credit_limit': _('حد الائتمان'),
            'tax_number': _('الرقم الضريبي'),
            'notes': _('ملاحظات'),
        }
        
    def clean_phone(self):
        """تنسيق رقم الهاتف وإزالة الأحرف الغير مطلوبة"""
        phone = self.cleaned_data['phone']
        if phone:
            # إزالة المسافات والأقواس والشرطات
            phone = ''.join(c for c in phone if c.isdigit() or c == '+')
            
            # إضافة كود الدولة إذا لم يكن موجودًا (مصر كمثال)
            if phone and not phone.startswith('+'):
                if phone.startswith('0'):
                    phone = '+2' + phone
                else:
                    phone = '+2' + phone
        return phone
    
    def clean_code(self):
        """التحقق من عدم تكرار الكود"""
        code = self.cleaned_data.get('code')
        if code:
            # التحقق فقط إذا تم تغيير الكود أو إذا كانت عملية إنشاء جديدة
            instance = getattr(self, 'instance', None)
            if instance and instance.pk:
                if Customer.objects.filter(code=code).exclude(pk=instance.pk).exists():
                    raise forms.ValidationError(_('هذا الكود مستخدم بالفعل، يرجى اختيار كود آخر'))
            else:
                if Customer.objects.filter(code=code).exists():
                    raise forms.ValidationError(_('هذا الكود مستخدم بالفعل، يرجى اختيار كود آخر'))
        return code
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # جعل حقل التصنيف يعرض "إنشاء تصنيف جديد" إذا لم تكن هناك تصنيفات
        if not CustomerCategory.objects.exists():
            self.fields['category'].empty_label = _("+ أضف تصنيف جديد")
        else:
            self.fields['category'].empty_label = _("بدون تصنيف")
        
        # جعل بعض الحقول غير مطلوبة
        for field in ['email', 'address', 'category', 'alternative_phone', 'tax_number', 'notes']:
            self.fields[field].required = False

class CustomerSearchForm(forms.Form):
    """نموذج البحث المتقدم عن العملاء"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('بحث بالاسم أو رقم الهاتف أو البريد أو الكود...'),
            'class': 'form-control',
            'aria-label': _('بحث عن عميل')
        })
    )
    
    category = forms.ModelChoiceField(
        required=False,
        queryset=CustomerCategory.objects.all(),
        empty_label=_("جميع التصنيفات"),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('تصنيف العميل')
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', _("جميع الحالات"))] + list(Customer.STATUS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('حالة العميل')
        })
    )
    
    debt_status = forms.ChoiceField(
        required=False,
        choices=[
            ('', _("جميع العملاء")),
            ('with_debts', _("عليهم مديونية")),
            ('no_debts', _("بدون مديونية")),
            ('exceed_limit', _("تجاوزوا حد الائتمان")),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('حالة المديونية')
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('name', _("الاسم (أ-ي)")),
            ('-name', _("الاسم (ي-أ)")),
            ('created_at', _("الأقدم أولاً")),
            ('-created_at', _("الأحدث أولاً")),
            ('-total_sales', _("الأكثر مبيعات")),
            ('-debt', _("الأعلى مديونية")),
            ('debt', _("الأقل مديونية")),
        ],
        initial='-created_at',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'aria-label': _('ترتيب حسب')
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إضافة خاصية التثبيت العلوي إلى حقول التصفية
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'data-bs-toggle': 'tooltip', 'title': field.label})
