from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class SuppliersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'suppliers'
    verbose_name = _('الموردين')
