from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def pagination_url(context, page_number):
    """بناء عنوان URL للترقيم مع الحفاظ على معلمات البحث"""
    request = context['request']
    params = request.GET.copy()
    params['page'] = page_number
    return f"?{params.urlencode()}"
