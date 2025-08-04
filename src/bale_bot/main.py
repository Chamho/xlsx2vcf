# src/bale_bot/main.py
import asyncio
import logging
from balethon import Client
from balethon.objects import Message, Document
from balethon.conditions import private, command, document

from. import config
from. import converter

# تنظیمات لاگ‌گیری برای نمایش بهتر اطلاعات
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# نمونه‌سازی کلاینت ربات با توکن
bot = Client(config.get_bot_token())
ADMIN_ID = config.get_admin_id()


#... (ادامه main.py)

@bot.on_connect()
async def ready(client: Client):
    """
    این تابع هنگام اتصال موفقیت‌آمیز ربات به سرور بله اجرا می‌شود.
    """
    logger.info(f"Bot is connected as @{client.info.username}")
    if ADMIN_ID:
        await client.send_message(ADMIN_ID, "✅ ربات با موفقیت آنلاین شد.")

@bot.on_message(private & command("start"))
async def start_handler(message: Message):
    """
    پاسخ به دستور /start
    """
    welcome_text = (
        "🤖 سلام! به ربات مبدل اکسل به VCF خوش آمدید.\n\n"
        "کافیست یک فایل اکسل (.xlsx) برای من ارسال کنید.\n"
        "فایل شما باید حداقل دو ستون داشته باشد:\n"
        "ستون اول: نام مخاطب\n"
        "ستون دوم: شماره تلفن\n\n"
        "من فایل را پردازش کرده و یک فایل VCF برای ذخیره در مخاطبین گوشی به شما تحویل می‌دهم."
    )
    await message.reply(welcome_text)

@bot.on_message(private & command("help"))
async def help_handler(message: Message):
    """
    پاسخ به دستور /help
    """
    help_text = (
        "راهنما:\n"
        "1. یک فایل اکسل با فرمت `.xlsx` آماده کنید.\n"
        "2. در ستون اول نام‌ها و در ستون دوم شماره تلفن‌ها را وارد کنید.\n"
        "3. فایل را در همین چت برای من ارسال کنید.\n"
        "4. منتظر بمانید تا فایل VCF را برایتان ارسال کنم.\n\n"
        "⚠️ توجه: فرمت‌های دیگر اکسل (مانند.xls) یا فایل‌های دیگر پشتیبانی نمی‌شوند."
    )
    await message.reply(help_text)


    #... (ادامه main.py)

@bot.on_message(private & document)
async def file_handler(message: Message):
    """
    پردازش فایل ارسال شده توسط کاربر
    """
    doc: Document = message.document
    
    # 1. اعتبارسنجی نوع فایل
    if not doc.file_name.endswith((".xlsx")):
        await message.reply("❌ خطا: لطفاً فقط فایل اکسل با فرمت `.xlsx` ارسال کنید.")
        return

    # 2. اطلاع‌رسانی به کاربر
    processing_msg = await message.reply("در حال پردازش فایل شما... لطفاً منتظر بمانید ⏳")

    try:
        # 3. دانلود محتوای فایل در حافظه
        file_content: bytes = await doc.download()

        # 4. فراخوانی موتور تبدیل
        vcf_string = converter.convert_excel_to_vcf(file_content)
        
        # 5. آماده‌سازی فایل VCF برای ارسال
        vcf_bytes = vcf_string.encode('utf-8')
        output_file = ("contacts.vcf", vcf_bytes)
        
        # 6. ارسال فایل نهایی
        await message.reply_document(
            document=output_file,
            caption="✅ فایل VCF شما آماده است. می‌توانید آن را در گوشی خود باز کرده و مخاطبین را ذخیره کنید."
        )

    except ValueError as e:
        # مدیریت خطاهای قابل پیش‌بینی (مانند فایل خالی یا فرمت نادرست)
        await message.reply(f"❌ خطا در پردازش فایل: {e}")
        logger.warning(f"Processing error for user {message.author.id}: {e}")
    except Exception as e:
        # مدیریت خطاهای غیرمنتظره
        await message.reply("❌ یک خطای پیش‌بینی نشده رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.")
        logger.error(f"Unexpected error for user {message.author.id}: {e}", exc_info=True)
        if ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
    finally:
        # حذف پیام "در حال پردازش"
        await processing_msg.delete()


if __name__ == "__main__":
    bot.run()