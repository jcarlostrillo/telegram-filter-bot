from infrastructure.logger import logger
from infrastructure.telegram_client import send_via_bot

def send_daily_summary(processed, forwarded):
    """Sends a daily summary message via bot."""
    summary = (
        f"📊 Daily Summary:\n"
        f"✅ Messages Processed: {processed}\n"
        f"✅ Messages Forwarded: {forwarded}\n"
        f"🚀 Running smoothly!"
    )
    send_via_bot(summary)
    logger.info("Daily summary sent.")
