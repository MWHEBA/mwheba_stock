from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Product

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

@login_required
def product_create(request):
    # Placeholder for form handling
    return render(request, 'products/product_form.html')

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Placeholder for form handling
    return render(request, 'products/product_form.html', {'product': product})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Placeholder for delete logic
    return redirect('product-list')

@login_required
def product_categories(request):
    # Placeholder for categories view
    return render(request, 'products/product_categories.html')
