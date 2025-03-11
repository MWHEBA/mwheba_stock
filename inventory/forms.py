from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Supplier, Client, Product, Category, StorageLocation,
    PurchaseOrder, PurchaseOrderItem, Order, OrderItem,
    SupplierPayment, ClientPayment, CompanyProfile, ExpenseCategory,
    Expense, FinancialAccount, Transaction, UserProfile
)

# User Registration Form
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

# User Profile Form
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'phone', 'address']

# Supplier Form
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'tax_number', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

# Client Form
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'tax_number', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

# Category Form
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# Storage Location Form
class StorageLocationForm(forms.ModelForm):
    class Meta:
        model = StorageLocation
        fields = ['name', 'description', 'address']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

# Product Form
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'description', 'price', 'cost_price', 'quantity',
                 'supplier', 'category', 'reorder_level', 'location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# Purchase Order Form
class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'reference_number', 'status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

# Purchase Order Item Form
class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'price']

# Purchase Order Item Formset
PurchaseOrderItemFormset = forms.inlineformset_factory(
    PurchaseOrder, PurchaseOrderItem, form=PurchaseOrderItemForm,
    extra=1, can_delete=True
)

# Order Form
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['client', 'invoice_number', 'status', 'discount_percentage',
                 'tax_percentage', 'shipping_cost', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

# Order Item Form
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']

# Order Item Formset
OrderItemFormset = forms.inlineformset_factory(
    Order, OrderItem, form=OrderItemForm,
    extra=1, can_delete=True
)

# Supplier Payment Form
class SupplierPaymentForm(forms.ModelForm):
    class Meta:
        model = SupplierPayment
        fields = ['supplier', 'purchase_order', 'amount', 'payment_date',
                 'payment_method', 'reference_number', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

# Client Payment Form
class ClientPaymentForm(forms.ModelForm):
    class Meta:
        model = ClientPayment
        fields = ['client', 'order', 'amount', 'payment_date',
                 'payment_method', 'reference_number', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

# Company Profile Form
class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ['name', 'logo', 'address', 'phone', 'email',
                 'website', 'tax_number', 'registration_number']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

# Expense Category Form
class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# Expense Form
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'date', 'description',
                 'reference_number', 'payment_method']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# Financial Account Form
class FinancialAccountForm(forms.ModelForm):
    class Meta:
        model = FinancialAccount
        fields = ['name', 'account_type', 'description', 'balance']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# Transaction Form
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['account', 'transaction_type', 'amount', 'date',
                 'description', 'reference', 'related_account']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# Date Range Form for Reports
class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
