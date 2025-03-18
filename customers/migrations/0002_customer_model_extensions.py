from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import RegexValidator

class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='اسم التصنيف')),
                ('color_code', models.CharField(default='primary', max_length=20, verbose_name='لون التصنيف')),
                ('description', models.TextField(blank=True, null=True, verbose_name='وصف')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
            ],
            options={
                'verbose_name': 'تصنيف العملاء',
                'verbose_name_plural': 'تصنيفات العملاء',
                'ordering': ['name'],
            },
        ),
        # Add missing fields to Customer model
        migrations.AddField(
            model_name='customer',
            name='code',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='كود العميل'),
        ),
        migrations.AddField(
            model_name='customer',
            name='alternative_phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='رقم هاتف بديل'),
        ),
        migrations.AddField(
            model_name='customer',
            name='status',
            field=models.CharField(choices=[('active', 'نشط'), ('inactive', 'غير نشط'), ('blocked', 'محظور')], default='active', max_length=20, verbose_name='الحالة'),
        ),
        migrations.AddField(
            model_name='customer',
            name='credit_limit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='حد الائتمان'),
        ),
        migrations.AddField(
            model_name='customer',
            name='tax_number',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='الرقم الضريبي'),
        ),
        migrations.AddField(
            model_name='customer',
            name='total_sales',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='إجمالي المبيعات'),
        ),
        migrations.AddField(
            model_name='customer',
            name='points',
            field=models.IntegerField(default=0, verbose_name='نقاط الولاء'),
        ),
        migrations.AddField(
            model_name='customer',
            name='last_purchase_date',
            field=models.DateField(blank=True, null=True, verbose_name='تاريخ آخر شراء'),
        ),
        # Add foreign key to category
        migrations.AddField(
            model_name='customer',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customers', to='customers.customercategory', verbose_name='التصنيف'),
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['name'], name='customer_name_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['phone'], name='customer_phone_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['status'], name='customer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['category'], name='customer_category_idx'),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['debt'], name='customer_debt_idx'),
        ),
    ]
