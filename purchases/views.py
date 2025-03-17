from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Purchase

@login_required
def purchase_list(request):
    purchases = Purchase.objects.all()
    return render(request, 'purchases/purchase_list.html', {'purchases': purchases})

@login_required
def purchase_create(request):
    # Placeholder for form handling
    return render(request, 'purchases/purchase_form.html')

@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    return render(request, 'purchases/purchase_detail.html', {'purchase': purchase})

@login_required
def purchase_edit(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    # Placeholder for form handling
    return render(request, 'purchases/purchase_form.html', {'purchase': purchase})

@login_required
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    # Placeholder for delete logic
    return redirect('purchase-list')

@login_required
def purchase_payments(request):
    # Placeholder for payments view
    return render(request, 'purchases/purchase_payments.html')
