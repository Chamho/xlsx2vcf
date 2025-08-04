# src/bale_bot/converter.py
import openpyxl
from io import BytesIO

def generate_vcard_string(contacts):
    """
    یک لیست از دیکشنری‌های مخاطبین را به یک رشته vCard تبدیل می‌کند.
    """
    vcard_entries =[]
    for contact in contacts:
        name = contact.get('name', '')
        phone = contact.get('phone', '')
        if not name or not phone:
            continue
        
        entry =[]
        vcard_entries.append("\n".join(entry))
    
    return "\n".join(vcard_entries)

def convert_excel_to_vcf(file_content: bytes):
    """
    محتوای باینری یک فایل اکسل را دریافت کرده و یک رشته vCard برمی‌گرداند.
    """
    contacts =[]
    try:
        # فایل اکسل را از محتوای باینری در حافظه باز می‌کند
        workbook = openpyxl.load_workbook(filename=BytesIO(file_content))
        sheet = workbook.active
        
        # از ردیف دوم شروع به خواندن می‌کند تا از هدر صرف‌نظر شود (اختیاری)
        for row in sheet.iter_rows(min_row=1, values_only=True):
            if row and len(row) >= 2:
                name = str(row).strip() if row else ''
                phone = str(row).strip() if row else ''
                
                if name and phone:
                    contacts.append({'name': name, 'phone': phone})

    except Exception as e:
        # در صورت بروز خطا در خواندن فایل، یک استثنا با پیام مناسب ایجاد می‌کند
        raise ValueError(f"خطا در پردازش فایل اکسل: {e}")

    if not contacts:
        raise ValueError("هیچ مخاطب معتبری در فایل اکسل یافت نشد.")

    return generate_vcard_string(contacts)