from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery

router = Router(name="payments_module")

@router.message(Command("donate", "pay", "buy"))
async def create_invoice(message: Message):
    """Sends a Telegram Stars or standard digital invoice."""
    prices = [LabeledPrice(label="VIP Supporter", amount=100)]  # 100 Telegram Stars or cents

    await message.answer_invoice(
        title="TeleCore Premium Supporter",
        description="Unlock exclusive features and support open source development.",
        payload="supporter_tier_1",
        currency="XTR",  # Telegram Stars currency code
        prices=prices
    )

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Answers pre-checkout queries to confirm purchase."""
    await pre_checkout_query.answer(ok=True)

@router.message(lambda msg: msg.successful_payment is not None)
async def successful_payment_handler(message: Message):
    """Triggered upon successful user payment."""
    total = message.successful_payment.total_amount
    currency = message.successful_payment.currency
    await message.reply(f"🎉 <b>Thank you!</b> Your payment of <code>{total} {currency}</code> was successful!")
