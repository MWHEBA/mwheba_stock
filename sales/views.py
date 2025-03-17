from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Sale

@login_required
def sale_list(request):
    sales = Sale.objects.all()
    return render(request, 'sales/sale_list.html', {'sales': sales})

@login_required
def sale_create(request):
    # Placeholder for form handling
    return render(request, 'sales/sale_form.html')

@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/sale_detail.html', {'sale': sale})

@login_required
def sale_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    # Placeholder for form handling
    return render(request, 'sales/sale_form.html', {'sale': sale})

@login_required
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    # Placeholder for delete logic
    return redirect('sale-list')

@login_required
def sale_print(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/sale_print.html', {'sale': sale})

@login_required
def customer_payments(request):
    # Placeholder for payments view
    return render(request, 'sales/customer_payments.html')
