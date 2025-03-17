from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'supplier_code', 'purchase_price', 'sale_price', 'quantity', 'supplier', 'image']
        labels = {
            'name': _('اسم المنتج'),
            'sku': _('كود المنتج'),
            'supplier_code': _('كود المورد'),
            'purchase_price': _('سعر الشراء'),
            'sale_price': _('سعر البيع'),
            'quantity': _('الكمية'),
            'supplier': _('المورد'),
            'image': _('صورة المنتج'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier_code': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        purchase_price = cleaned_data.get('purchase_price')
        sale_price = cleaned_data.get('sale_price')
        
        if purchase_price and sale_price:
            if sale_price < purchase_price:
                self.add_error('sale_price', _('سعر البيع يجب أن يكون أكبر من أو يساوي سعر الشراء'))
        
        return cleaned_data
