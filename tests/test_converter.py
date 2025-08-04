# tests/test_converter.py
import pytest
import openpyxl
from io import BytesIO
from src.bale_bot.converter import convert_excel_to_vcf

def create_sample_excel_file():
    """یک فایل اکسل نمونه در حافظه ایجاد می‌کند."""
    output = BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Contacts"

    # داده‌های نمونه
    data = [
        ("نام نمونه ۱", "09123456789"),
        ("نام نمونه ۲", "+989129876543"),
        ("مخاطب بدون شماره", None), # این ردیف باید نادیده گرفته شود
        ("", "09121112233"), # این ردیف هم باید نادیده گرفته شود
    ]

    for row in data:
        sheet.append(row)

    workbook.save(output)
    output.seek(0)
    return output.read()

def test_conversion_logic():
    """
    تست می‌کند که آیا تبدیل به درستی انجام می‌شود یا خیر.
    """
    excel_content = create_sample_excel_file()
    vcf_result = convert_excel_to_vcf(excel_content)

    # بررسی اینکه آیا مخاطبین معتبر در خروجی وجود دارند
    assert "FN:نام نمونه ۱" in vcf_result
    assert "TEL;TYPE=CELL:09123456789" in vcf_result
    assert "FN:نام نمونه ۲" in vcf_result
    assert "TEL;TYPE=CELL:+989129876543" in vcf_result

    # بررسی اینکه مخاطبین نامعتبر در خروجی وجود ندارند
    assert "مخاطب بدون شماره" not in vcf_result
    assert "09121112233" not in vcf_result

    # بررسی ساختار کلی
    assert vcf_result.count("BEGIN:VCARD") == 2
    assert vcf_result.count("END:VCARD") == 2

def test_empty_file_error():
    """
    تست می‌کند که آیا فایل خالی خطای مناسب را برمی‌گرداند.
    """
    output = BytesIO()
    workbook = openpyxl.Workbook()
    workbook.save(output)
    output.seek(0)

    with pytest.raises(ValueError, match="هیچ مخاطب معتبری در فایل اکسل یافت نشد."):
        convert_excel_to_vcf(output.read())
