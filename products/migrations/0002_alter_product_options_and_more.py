# Generated by Django 4.2.20 on 2025-03-18 05:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'verbose_name': 'المنتج', 'verbose_name_plural': 'المنتجات'},
        ),
        migrations.AlterModelOptions(
            name='purchasepricehistory',
            options={'ordering': ['-date_changed'], 'verbose_name': 'سجل سعر الشراء', 'verbose_name_plural': 'سجلات أسعار الشراء'},
        ),
    ]
