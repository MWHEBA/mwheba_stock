from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Supplier

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'suppliers/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_create(request):
    # Placeholder for form handling
    return render(request, 'suppliers/supplier_form.html')

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    return render(request, 'suppliers/supplier_detail.html', {'supplier': supplier})

@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    # Placeholder for form handling
    return render(request, 'suppliers/supplier_form.html', {'supplier': supplier})

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    # Placeholder for delete logic
    return redirect('supplier-list')

@login_required
def supplier_debts(request):
    suppliers = Supplier.objects.filter(debt__gt=0)
    return render(request, 'suppliers/supplier_debts.html', {'suppliers': suppliers})
