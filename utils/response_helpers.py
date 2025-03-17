def paginate_response(response_data, page_size=100):
    """
    تقسيم البيانات إلى صفحات للتعامل مع ردود كبيرة الحجم
    """
    total_items = len(response_data)
    total_pages = (total_items + page_size - 1) // page_size  # حساب عدد الصفحات اللازمة
    
    paginated_data = []
    for i in range(0, total_pages):
        start_idx = i * page_size
        end_idx = min(start_idx + page_size, total_items)
        page_data = {
            'page': i + 1,
            'total_pages': total_pages,
            'data': response_data[start_idx:end_idx]
        }
        paginated_data.append(page_data)
    
    return paginated_data
