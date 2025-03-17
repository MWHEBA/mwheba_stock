from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Customer

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'customers/customer_list.html', {'customers': customers})

@login_required
def customer_create(request):
    # Placeholder for form handling
    return render(request, 'customers/customer_form.html')

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'customers/customer_detail.html', {'customer': customer})

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    # Placeholder for form handling
    return render(request, 'customers/customer_form.html', {'customer': customer})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    # Placeholder for delete logic
    return redirect('customer-list')

@login_required
def customer_debts(request):
    customers = Customer.objects.filter(debt__gt=0)
    return render(request, 'customers/customer_debts.html', {'customers': customers})
