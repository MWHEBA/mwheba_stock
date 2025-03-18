from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.conf import settings
from products.models import Product
from customers.models import Customer
from suppliers.models import Supplier
from sales.models import Sale
from .models import ActivityLog, User
from .forms import UserProfileForm
import json

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': _('اسم المستخدم')})
        form.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': _('كلمة المرور')})
        return form

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('dashboard')  # Default redirect to dashboard
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('تسجيل الدخول')
        return context

class CustomLogoutView(LogoutView):
    next_page = 'login'

@login_required
def dashboard(request):
    # Sample data (in a real application this would come from database)
    # Make sure all data meant for iteration is a list or other iterable
    
    # Sales statistics
    total_sales = 0  # This could be an integer in the actual code
    total_revenue = 0.0
    
    # Product statistics
    total_products = 0
    out_of_stock = 0
    
    # Customer statistics
    total_customers = 0
    new_customers = 0
    
    # Charts data - make sure these are lists, not integers
    weekly_labels = json.dumps(['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'])
    weekly_sales = json.dumps([5, 7, 8, 12, 10, 9, 11])
    weekly_revenue = json.dumps([1500, 2100, 2400, 3600, 3000, 2700, 3300])
    
    monthly_labels = json.dumps(['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'])
    monthly_sales = json.dumps([42, 38, 47, 52, 48, 55])
    monthly_revenue = json.dumps([12600, 11400, 14100, 15600, 14400, 16500])
    
    yearly_labels = json.dumps(['2020', '2021', '2022', '2023', '2024', '2025'])
    yearly_sales = json.dumps([325, 410, 490, 520, 580, 320])
    yearly_revenue = json.dumps([97500, 123000, 147000, 156000, 174000, 96000])
    
    # Recent sales - make sure this is a list
    recent_sales = []  # In real app, this would be a queryset of sales objects
    
    # Low stock products - make sure this is a list
    low_stock_products = []  # In real app, this would be a queryset of product objects
    
    # Top selling products - make sure this is a list
    top_selling_products = []  # In real app, this would be a queryset of product objects
    
    # Notifications - make sure this is a list
    notifications = []  # In real app, this would be a queryset of notification objects
    notifications_count = 0
    
    context = {
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'total_customers': total_customers,
        'new_customers': new_customers,
        'weekly_labels': weekly_labels,
        'weekly_sales': weekly_sales,
        'weekly_revenue': weekly_revenue,
        'monthly_labels': monthly_labels,
        'monthly_sales': monthly_sales,
        'monthly_revenue': monthly_revenue,
        'yearly_labels': yearly_labels,
        'yearly_sales': yearly_sales,
        'yearly_revenue': yearly_revenue,
        'recent_sales': recent_sales,
        'low_stock_products': low_stock_products,
        'top_selling_products': top_selling_products,
        'notifications': notifications,
        'notifications_count': notifications_count,
    }
    
    return render(request, 'dashboard/index.html', context)

@login_required
def profile(request):
    user = request.user
    activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')[:20]
    
    context = {
        'user': user,
        'activities': activities
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def activity_log(request):
    activity_list = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(activity_list, 20)  # Show 20 activities per page
    
    try:
        activities = paginator.page(page)
    except PageNotAnInteger:
        activities = paginator.page(1)
    except EmptyPage:
        activities = paginator.page(paginator.num_pages)
    
    context = {
        'activities': activities
    }
    
    return render(request, 'accounts/activity_log.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث بياناتك الشخصية بنجاح'))
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

@login_required
def profile_picture_update(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        user = request.user
        user.profile_picture = request.FILES['profile_picture']
        user.save()
        messages.success(request, _('تم تحديث الصورة الشخصية بنجاح'))
    
    return redirect('profile')
