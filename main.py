import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, PAYMENT_TOKEN, PRODUCTS

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    # Создаём кнопки с товарами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{product['title']} — {product['price']} ₽",
            callback_data=f"buy_{product_id}"
        )]
        for product_id, product in PRODUCTS.items()
    ])

    await message.answer(
        "🛍 Добро пожаловать в магазин!\n\n"
        "Выберите товар:",
        reply_markup=keyboard
    )


# Обработка нажатия на кнопку товара
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback_query):
    product_id = callback_query.data.split("_")[1]
    product = PRODUCTS[product_id]

    # Создаём инвойс (счёт на оплату)
    await bot.send_invoice(
        chat_id=callback_query.from_user.id,
        title=product["title"],
        description=product["description"],
        payload=product_id,  # это вернётся нам после оплаты
        provider_token=PAYMENT_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(label=product["title"], amount=product["price"] * 100)  # в копейках!
        ]
    )

    await callback_query.answer()


# Pre-checkout — проверка перед оплатой (обязательно!)
@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Здесь можно проверить наличие товара, валидность и т.д.
    # Мы просто подтверждаем
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# Successful payment — оплата прошла
@dp.message(F.content_type == "successful_payment")
async def process_successful_payment(message: Message):
    product_id = message.successful_payment.invoice_payload
    product = PRODUCTS[product_id]

    # Выдаём товар
    await message.answer(
        f"✅ Оплата прошла успешно!\n\n"
        f"Вы купили: {product['title']}\n"
        f"Сумма: {product['price']} ₽\n\n"
        f"Ваш товар:\n"
        f"📎 {product['file']}\n\n"
        f"Спасибо за покупку! 🎉"
    )

    # Здесь можно отправить файл:
    # await message.answer_document(FSInputFile(product['file']))


async def main():
    print("Бот с оплатой запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())