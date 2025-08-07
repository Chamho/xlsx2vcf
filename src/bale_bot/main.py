import io
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional

from balethon import Client
from balethon.objects import Message, Document

from . import config, converter

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

bot = Client(config.get_bot_token())
ADMIN_ID = config.get_admin_id()

# ---------------------------------------------------------------------------
# Compatibility helpers
# ---------------------------------------------------------------------------

def is_private_chat(chat) -> bool:
    """True اگر چت خصوصی باشد (سازگار با نسخه‌های مختلف Balethon)."""
    chat_type = getattr(chat, "type", chat)
    if hasattr(chat_type, "is_private_chat"):
        try:
            return chat_type.is_private_chat()
        except Exception:
            pass
    return str(chat_type).lower() in {"private", "pv"}


def document_filename(doc: Document) -> Optional[str]:
    """نام فایل ارسالی را برمی‌گرداند (camelCase / snake_case)."""
    for attr in ("file_name", "filename", "name", "fileName"):
        name = getattr(doc, attr, None)
        if isinstance(name, str) and name:
            return name
    return None


def document_mimetype(doc: Document) -> str:
    for attr in ("mime_type", "mimeType", "mime"):
        mt = getattr(doc, attr, "")
        if mt:
            return str(mt)
    return ""


def is_excel(doc: Document) -> bool:
    filename = document_filename(doc)
    if filename and filename.lower().endswith(".xlsx"):
        return True
    mimetype = document_mimetype(doc)
    return mimetype in {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    }


async def get_doc_bytes(doc: Document) -> bytes:
    """دانلود بایت‌های فایل صرف نظر از نسخهٔ SDK."""
    if hasattr(doc, "client") and hasattr(doc.client, "download") and callable(doc.client.download):
        return await doc.client.download(doc.id)
    if hasattr(doc, "download") and callable(doc.download):
        return await doc.download()
    if hasattr(doc, "read") and callable(doc.read):
        return await doc.read()
    if hasattr(doc, "save_to_memory") and callable(doc.save_to_memory):
        buf = io.BytesIO()
        await doc.save_to_memory(buf)
        return buf.getvalue()
    raise AttributeError("Document object exposes no known download method")

# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

@bot.on_connect()
async def ready(client: Client):
    logger.info("Bot connected as @%s", client.info.username)
    if ADMIN_ID:
        await client.send_message(ADMIN_ID, "✅ ربات با موفقیت آنلاین شد.")


@bot.on_message()
async def handle_message(message: Message):
    if not is_private_chat(message.chat):
        logger.debug("Ignored non-PV message (chat type=%s)", getattr(message.chat, "type", "?"))
        return

    if message.text == "/start":
        await start_handler(message)
    elif message.text == "/help":
        await help_handler(message)
    elif message.document:
        await file_handler(message)
    elif message.text:
        await message.reply("❌ لطفاً فقط فایل اکسل `.xlsx` یا دستور /help را ارسال کنید.")


async def start_handler(message: Message):
    await message.reply(
        "🤖 سلام! به ربات مبدل اکسل به VCF خوش آمدید.\n\n"
        "کافیست یک فایل اکسل (`.xlsx`) برای من ارسال کنید.\n"
        "ستون‌های مورد نیاز: Names, Phone, Cat\n"
        "برای هر مقدار متفاوت در Cat یک فایل VCF تولید می‌شود و در یک ZIP تحویل می‌گیرید."
    )


async def help_handler(message: Message):
    await message.reply(
        "راهنما:\n"
        "• فایل اکسل با ستون‌های Names, Phone, Cat ارسال کنید.\n"
        "• فقط فرمت .xlsx پشتیبانی می‌شود."
    )


async def file_handler(message: Message):
    doc: Document = message.document

    if not is_excel(doc):
        await message.reply("❌ فایل ارسالی اکسل نیست. لطفاً .xlsx بفرستید.")
        return

    processing = await message.reply("⏳ در حال پردازش …")

    tmp_path = None
    try:
        # دریافت بایت‌های اکسل
        xlsx_bytes = await get_doc_bytes(doc)
        # تبدیل اکسل به زیپ حاوی VCF
        zip_bytes = converter.convert_excel_to_vcf(xlsx_bytes)

        # نام فایل خروجی بر اساس نام اکسل
        base_name = Path(document_filename(doc) or "contacts").stem
        tmp_path = os.path.join(tempfile.gettempdir(), f"{base_name}.zip")
        with open(tmp_path, "wb") as tmp_file:
            tmp_file.write(zip_bytes)

        await message.reply_document(
            document=tmp_path,
            caption="✅ فایل ZIP آماده است."
        )

    except ValueError as e:
        await message.reply(f"❌ {e}")
        logger.warning("Validation error: %s", e)
    except Exception as e:
        await message.reply("❌ خطای غیرمنتظره. لطفاً دوباره تلاش کنید.")
        logger.exception("Unexpected error: %s", e)
        if ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"Unexpected error: {e}")
    finally:
        # پاک‌سازی فایل موقت
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                logger.warning("Failed to remove temp file %s", tmp_path)
        await processing.delete()


if __name__ == "__main__":
    bot.run()