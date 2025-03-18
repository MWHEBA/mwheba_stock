# أدوات مساعدة لوحدة المستخدمين

def format_phone_number(phone_number):
    """
    تنسيق رقم الهاتف
    
    Args:
        phone_number: رقم الهاتف المراد تنسيقه
    
    Returns:
        رقم الهاتف بعد التنسيق
    """
    if not phone_number:
        return phone_number
    
    # إزالة المسافات والأحرف الخاصة
    digits = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # إضافة كود الدولة (مصر) إذا لم يكن موجودًا
    if digits and not digits.startswith('+'):
        if digits.startswith('0'):
            digits = '+2' + digits[1:]
        else:
            digits = '+2' + digits
    
    return digits

def generate_customer_code(customer_name):
    """
    توليد كود فريد للعميل
    
    Args:
        customer_name: اسم العميل
    
    Returns:
        كود فريد للعميل
    """
    import random
    from datetime import datetime
    
    # أخذ الحرف الأول من كل كلمة في اسم العميل (أول كلمتين)
    name_parts = customer_name.split()[:2]
    prefix = ''.join([part[0].upper() if part else '' for part in name_parts])
    
    # إضافة التاريخ الحالي
    date_suffix = datetime.now().strftime('%y%m%d')
    
    # إضافة أرقام عشوائية
    random_suffix = random.randint(100, 999)
    
    return f"C{prefix}{date_suffix}{random_suffix}"
