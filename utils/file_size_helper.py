def get_readable_file_size(size_in_bytes):
    """
    تحويل حجم الملف بالبايت إلى تنسيق قابل للقراءة
    مثال: 1024 -> "1 كيلوبايت"
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} بايت"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} كيلوبايت"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} ميجابايت"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} جيجابايت"
