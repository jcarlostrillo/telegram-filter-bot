import logging
from infrastructure.telegram_client import client, get_entity_safe
from infrastructure.logger import logger
from domain.offset import read_offsets, save_offsets
from infrastructure.config import load_keywords
from domain.services import send_via_bot
from config.constants import SOURCE_CHANNEL_IDS

async def analyze_and_forward():
    """Processes messages & forwards relevant ones."""
    offsets = read_offsets()
    keywords = load_keywords()

    for channel_id in SOURCE_CHANNEL_IDS:
        entity = await get_entity_safe(channel_id)
        if not entity:
            continue

        offset_id = offsets.get(str(channel_id), 0)
        messages = await client.get_messages(entity, limit=50, min_id=offset_id)
        
        max_offset_id = offset_id
        for message in messages:
            if message.text and any(kw in message.text.lower() for kw in keywords):
                logger.info(f"Forwarding message from {channel_id}: {message.text[:100]}...")
                send_via_bot(message.text)

            max_offset_id = max(max_offset_id, message.id)

        offsets[str(channel_id)] = max_offset_id
        save_offsets(offsets)
