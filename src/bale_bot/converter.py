# src/bale_bot/converter.py
import pandas as pd
import vobject
from io import BytesIO
import zipfile

def convert_excel_to_vcf(file_content: bytes) -> bytes:
    """
    دریافت بایت‌های XLSX و بازگشت بایت‌های ZIP شامل یک VCF برای هر گروه Cat.
    """
    try:
        df = pd.read_excel(BytesIO(file_content))
    except Exception as e:
        raise ValueError(f"خطا در خواندن فایل Excel: {e}")

    if 'Cat' not in df.columns:
        raise ValueError("فایل ورودی باید ستون 'Cat' را داشته باشد.")
    if 'Names' not in df.columns or 'Phone' not in df.columns:
        raise ValueError("فایل باید ستون‌های 'Names' و 'Phone' را نیز داشته باشد.")

    output_io = BytesIO()
    with zipfile.ZipFile(output_io, 'w', zipfile.ZIP_DEFLATED) as zf:
        groups = df.groupby('Cat')
        for group_name, group_df in groups:
            vcf_entries = []
            for _, row in group_df.iterrows():
                try:
                    vcard = vobject.vCard()
                    vcard.add('fn').value = str(row['Names'])
                    tel = vcard.add('tel')
                    tel.value = '0' + str(row['Phone'])
                    tel.type_param = 'CELL'
                    vcf_entries.append(vcard.serialize())
                except Exception:
                    # رد کردن ردیف‌هایی با داده نامعتبر
                    continue

            if not vcf_entries:
                continue

            vcf_content = "\n".join(vcf_entries)
            filename = f"contacts_{group_name}.vcf"
            zf.writestr(filename, vcf_content.encode('utf-8'))

    output_io.seek(0)
    zip_bytes = output_io.read()
    if not zip_bytes:
        raise ValueError("هیچ مخاطب معتبری یافت نشد.")
    return zip_bytes
