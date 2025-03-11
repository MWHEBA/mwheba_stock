from django.conf import settings
from .models import Stock

@shared_task
def send_stock_alerts():
    low_stock_products = Stock.objects.filter(quantity_received__lt=5)  # Set your threshold
    
    for stock in low_stock_products:
        send_mail(
            f'Low Stock Alert: {stock.product.name}',
            f'The stock for {stock.product.name} is low. Only {stock.quantity_received} items are left.',
            settings.EMAIL_HOST_USER,
            ['info@mwheba.com'],  # Replace with your admin email
            fail_silently=False,
        )