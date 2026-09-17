import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = "7780956236:AAGrLbO4rQ5V94WEU6x00rt55yB0_sulnwA"
ADMIN_ID = 5874144878

CHANNELS = {
    "ishbor": "@Ishbor_Live",
    "ishlar": "@Ishlar_Live"
}

REGIONS = [
    "Toshkent shahri", "Toshkent viloyati", "Farg'ona viloyati",
    "Andijon viloyati", "Namangan viloyati", "Samarqand viloyati",
    "Buxoro viloyati", "Qashqadaryo viloyati", "Surxondaryo viloyati",
    "Jizzax viloyati", "Sirdaryo viloyati", "Navoiy viloyati",
    "Xorazm viloyati", "Qoraqalpog'iston Respublikasi"
]

db = {
    "card_number": "8600 0000 0000 0000",
    "card_owner": "Rahmonov D.",
    "post_price": "20 000 so'm",
    "forced_channels": ["@Ishbor_Live", "@Ishlar_Live"],
    "pending_posts": {}
}

router = Router()

class JobAnketa(StatesGroup):
    photo = State()          
    region = State()         
    company = State()        
    position = State()       
    age = State()            
    requirements = State()   
    salary = State()         
    work_schedule = State()  # <-- Ish kuni va soati uchun yangi qadam
    location = State()       
    phone = State()          
    waiting_for_receipt = State() 

class AdminState(StatesGroup):
    waiting_for_card_number = State()
    waiting_for_card_owner = State()
    waiting_for_price = State()
    waiting_for_channel = State()

# --- MAJBURIY OBUNANI TEKSHIRISH FUNKSIYASI ---
async def check_subscriptions(user_id: int, bot: Bot) -> bool:
    for channel in db["forced_channels"]:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

async def get_sub_keyboard():
    keyboard = []
    for channel in db["forced_channels"]:
        channel_link = f"https://t.me/{channel.replace('@', '')}"
        keyboard.append([InlineKeyboardButton(text=f"📢 {channel} ga obuna bo'lish", url=channel_link)])
    
    keyboard.append([InlineKeyboardButton(text="🔄 Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_user_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Ish e'lonini berish", callback_data="user_post")],
        [InlineKeyboardButton(text="ⓘ Bot haqida", callback_data="user_about")],
        [InlineKeyboardButton(text="📞 Bog'lanish", callback_data="user_support")]
    ])

def get_regions_keyboard():
    keyboard = []
    for i in range(0, len(REGIONS), 2):
        row = [InlineKeyboardButton(text=REGIONS[i], callback_data=f"reg_{REGIONS[i]}")]
        if i + 1 < len(REGIONS):
            row.append(InlineKeyboardButton(text=REGIONS[i+1], callback_data=f"reg_{REGIONS[i+1]}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 E'lon berish", callback_data="user_post")],
            [InlineKeyboardButton(text="💳 Karta ma'lumotlarini o'zgartirish", callback_data="admin_card")],
            [InlineKeyboardButton(text="💰 E'lon narxini o'zgartirish", callback_data="admin_price")],
            [InlineKeyboardButton(text="➕ Majburiy obuna kanal qo'shish", callback_data="admin_add_channel")],
            [InlineKeyboardButton(text="📋 Kanallarni ko'rish", callback_data="admin_channels")]
        ])
        await message.answer("<b>👑 Admin paneliga xush kelibsiz!</b>", reply_markup=keyboard, parse_mode="HTML")
        return

    is_subscribed = await check_subscriptions(user_id, message.bot)
    if not is_subscribed:
        await message.answer(
            "<b>⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart:</b>\n\n"
            "Obuna bo'lgach, <b>🔄 Tekshirish</b> tugmasini bosing.",
            reply_markup=await get_sub_keyboard(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        "<b>👋 Assalomu alaykum!</b>\n\n"
        "@Ishbor_Live va @Ishlar_Live kanallariga e'lon berish botiga xush kelibsiz. "
        "Kerakli bo'limni tanlang:", 
        reply_markup=get_user_menu(), 
        parse_mode="HTML"
    )

@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_subscribed = await check_subscriptions(user_id, callback.bot)
    
    if not is_subscribed:
        await callback.answer("❌ Siz hali hamma kanalga obuna bo'lmadingiz!", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "<b>✅ Rahmat! Obuna tasdiqlandi.</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=get_user_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    
    is_subscribed = await check_subscriptions(user_id, callback.message.bot)
    if not is_subscribed:
        await callback.message.edit_text(
            "<b>⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart:</b>\n\n"
            "Obuna bo'lgach, <b>🔄 Tekshirish</b> tugmasini bosing.",
            reply_markup=await get_sub_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "<b>🏠 Asosiy menyu:</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=get_user_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "user_post")
async def start_anketa(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not await check_subscriptions(user_id, callback.message.bot):
        await callback.answer("❌ Avval kanallarga obuna bo'lishingiz kerak!", show_alert=True)
        return

    skip_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_photo")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await callback.message.edit_text(
        "📋 <b>Ish e'lonini berish (1/10):</b>\n\n"
        "E'longa mos biron bir rasm (banner) yuboring.\n"
        "<i>Agar rasm bo'lmasa, quyidagi tugmani bosing:</i>",
        reply_markup=skip_kb,
        parse_mode="HTML"
    )
    await state.set_state(JobAnketa.photo)
    await callback.answer()

@router.callback_query(JobAnketa.photo, F.data == "skip_photo")
async def skip_photo_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo_id=None)
    await ask_region(callback.message, state, is_callback=True)
    await callback.answer()

@router.message(JobAnketa.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await ask_region(message, state, is_callback=False)

@router.message(JobAnketa.photo)
async def wrong_photo_format(message: Message):
    skip_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_photo")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await message.answer("⚠️ Iltimos, rasm yuboring yoki 'O'tkazib yuborish' tugmasini bosing:", reply_markup=skip_kb)

async def ask_region(message: Message, state: FSMContext, is_callback: bool):
    text = (
        "📋 <b>Ish e'lonini berish (2/10):</b>\n\n"
        "Ish joyi qaysi viloyatda joylashgan? Quyidagilardan birini tanlang:"
    )
    keyboard = get_regions_keyboard()
    if is_callback:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(JobAnketa.region)

@router.callback_query(JobAnketa.region, F.data.startswith("reg_"))
async def process_region_callback(callback: CallbackQuery, state: FSMContext):
    selected_region = callback.data.split("_", 1)[1]
    await state.update_data(region=selected_region)
    
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await callback.message.edit_text(
        f"📋 <b>Ish e'lonini berish (3/10):</b>\n\n"
        f"Tanlangan viloyat: <b>{selected_region}</b>\n\n"
        f"Kompaniya yoki tashkilot nomini kiriting:\n"
        f"<i>(Masalan: \"Artel\" MChJ yoki \"Ziyo\" o'quv markazi)</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(JobAnketa.company)
    await callback.answer()

@router.message(JobAnketa.company, F.text)
async def process_company(message: Message, state: FSMContext):
    await state.update_data(company=message.text)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await message.answer(
        "📋 <b>Ish e'lonini berish (4/10):</b>\n\n"
        "Qaysi lavozimga ishchi kerak?\n"
        "<i>(Masalan: Sotuvchi, Ofis menejeri, Haydovchi)</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(JobAnketa.position)

@router.message(JobAnketa.position, F.text)
async def process_position(message: Message, state: FSMContext):
    await state.update_data(position=message.text)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await message.answer(
        "📋 <b>Ish e'lonini berish (5/10):</b>\n\n"
        "Nomzodning yoshi necha oralig'ida bo'lishi kerak?\n"
        "<i>(Masalan: 18 - 35 yosh yoki Farqi yo'q)</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(JobAnketa.age)

@router.message(JobAnketa.age, F.text)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await message.answer(
        "📋 <b>Ish e'lonini berish (6/10):</b>\n\n"
        "Nomzodga qo'yiladigan talablar va vazifalar qanday? Qisqacha yozing:",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(JobAnketa.requirements)

@router.message(JobAnketa.requirements, F.text)
async def process_requirements(message: Message, state: FSMContext):
    await state.update_data(requirements=message.text)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await message.answer(
        "📋 <b>Ish e'lonini berish (7/10):</b>\n\n"
        "Ish haqi (Maosh) qancha?\n"
        "<i>(Masalan: 4 - 6 mln so'm yoki Kelishiladi)</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(JobAnketa.salary)

@router.message(JobAnketa.salary, F.text)
async def process_salary(message: Message, state: FSMContext):
    await state.update_data(salary=message.text)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await message.answer(
        "📋 <b>Ish kuni va vaqti (8/10):</b>\n\n"
        "Ish kunlari va ish vaqtini kiriting:\n"
        "<i>(Masalan: Dushanba - Shanba, 09:00 - 18:00 yoki 6/1, 08:00 dan 17:00 gacha)</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(JobAnketa.work_schedule)

@router.message(JobAnketa.work_schedule, F.text)
async def process_work_schedule(message: Message, state: FSMContext):
    await state.update_data(work_schedule=message.text)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await message.answer(
        "📋 <b>Ish e'lonini berish (9/10):</b>\n\n"
        "Aniq manzilni kiriting (tumani, ko'chasi, mo'ljal):\n"
        "<i>(Masalan: Chilonzor tumani, 9-kvartal, Muqimiy ko'chasi)</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(JobAnketa.location)

@router.message(JobAnketa.location, F.text)
async def process_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    await message.answer(
        "📋 <b>Ish e'lonini berish (10/10):</b>\n\n"
        "Bog'lanish uchun telefon raqamingiz va mas'ul shaxs ismi:\n"
        "<i>(Masalan: +998 90 123-45-67, Botir aka)</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML"
    )
    await state.set_state(JobAnketa.phone)

@router.message(JobAnketa.phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(
        phone=message.text,
        user_id=message.from_user.id,
        username=message.from_user.username or "Mavjud emas"
    )
    
    card_text = (
        f"<b>✅ Anketa muvaffaqiyatli to'ldirildi!</b>\n\n"
        f"💳 <b>To'lov miqdori:</b> <code>{db['post_price']}</code>\n\n"
        f"<b>💳 To'lov uchun karta ma'lumotlari:</b>\n"
        f"Karta: <code>{db['card_number']}</code>\n"
        f"F.I.O: <b>{db['card_owner']}</b>\n\n"
        f"<i>To'lovni amalga oshirgach, chek(skrinshot) rasmini shu yerga yuboring.</i>"
    )
    
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")]
    ])
    
    await message.answer(card_text, reply_markup=cancel_kb, parse_mode="HTML")
    await state.set_state(JobAnketa.waiting_for_receipt)

@router.message(JobAnketa.waiting_for_receipt, F.photo)
async def get_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    receipt_file_id = message.photo[-1].file_id
    
    import uuid
    post_id = str(uuid.uuid4())[:8]
    db['pending_posts'][post_id] = data
    db['pending_posts'][post_id]['receipt'] = receipt_file_id
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{post_id}")
        ]
    ])
    
    preview_text = (
        f"🌍 <b>Hudud:</b> {data['region']}\n"
        f"🏢 <b>Kompaniya:</b> {data['company']}\n"
        f"💼 <b>Lavozim:</b> {data['position']}\n"
        f"👤 <b>Yosh chegarasi:</b> {data['age']}\n"
        f"📌 <b>Talablar:</b> {data['requirements']}\n"
        f"💰 <b>Maosh:</b> {data['salary']}\n"
        f"⏰ <b>Ish vaqti:</b> {data['work_schedule']}\n"
        f"📍 <b>Manzil:</b> {data['location']}\n"
        f"📞 <b>Aloqa:</b> {data['phone']}"
    )
    
    caption = (
        f"<b>🔔 Yangi to'lov va anketa! (ID: {post_id})</b>\n"
        f"👤 Foydalanuvchi: @{data['username']} (<code>{data['user_id']}</code>)\n\n"
        f"--- E'LON MATNI ---\n{preview_text}"
    )
    
    await message.bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=receipt_file_id, 
        caption=caption, 
        reply_markup=admin_kb, 
        parse_mode="HTML"
    )
    
    await message.answer("✅ Chekingiz adminga yuborildi! Admin tasdiqlagach, e'loningiz kanalga chiqariladi.", reply_markup=get_user_menu())
    await state.clear()

# --- ADMIN: KARTA MA'LUMOTLARINI TAHRIRLASH ---
@router.callback_query(F.data == "admin_card")
async def change_card_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("<b>1-qadam:</b> Yangi karta raqamini kiriting:\n<i>(Masalan: 8600 1234 5678 9012)</i>", parse_mode="HTML")
    await state.set_state(AdminState.waiting_for_card_number)
    await callback.answer()

@router.message(AdminState.waiting_for_card_number, F.text)
async def process_card_number(message: Message, state: FSMContext):
    await state.update_data(new_card_number=message.text)
    await message.answer("<b>2-qadam:</b> Karta egasining F.I.O. (Ism familiyasi)ni kiriting:\n<i>(Masalan: Rahmonov D.)</i>", parse_mode="HTML")
    await state.set_state(AdminState.waiting_for_card_owner)

@router.message(AdminState.waiting_for_card_owner, F.text)
async def process_card_owner(message: Message, state: FSMContext):
    data = await state.get_data()
    card_number = data.get("new_card_number")
    card_owner = message.text
    
    db['card_number'] = card_number
    db['card_owner'] = card_owner
    
    await message.answer(f"✅ <b>Karta ma'lumotlari muvaffaqiyatli yangilandi!</b>\n\nKarta: <code>{card_number}</code>\nF.I.O: <b>{card_owner}</b>", parse_mode="HTML")
    await state.clear()

# --- ADMIN: E'LON NARXINI O'ZGARTIRISH ---
@router.callback_query(F.data == "admin_price")
async def change_price_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        f"Joriy e'lon narxi: <b>{db['post_price']}</b>\n\n"
        "Yangi e'lon narxini kiriting:\n<i>(Masalan: 25 000 so'm yoki Bepul)</i>",
        parse_mode="HTML"
    )
    await state.set_state(AdminState.waiting_for_price)
    await callback.answer()

@router.message(AdminState.waiting_for_price, F.text)
async def save_price(message: Message, state: FSMContext):
    db['post_price'] = message.text
    await message.answer(f"✅ <b>E'lon narxi muvaffaqiyatli o'zgartirildi:</b> {message.text}", parse_mode="HTML")
    await state.clear()

# --- ADMIN: KANALLAR ---
@router.callback_query(F.data == "admin_add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Kanal usernamesini yuboring (@ bilan):")
    await state.set_state(AdminState.waiting_for_channel)
    await callback.answer()

@router.message(AdminState.waiting_for_channel, F.text)
async def save_channel(message: Message, state: FSMContext):
    channel = message.text.strip()
    if channel not in db['forced_channels']:
        db['forced_channels'].append(channel)
        await message.answer(f"✅ {channel} qo'shildi!")
    else:
        await message.answer("⚠️ Bu kanal allaqachon bor.")
    await state.clear()

@router.callback_query(F.data == "admin_channels")
async def list_channels(callback: CallbackQuery):
    channels_list = "\n".join(db['forced_channels'])
    await callback.message.answer(f"<b>📋 Kanallar:</b>\n\n{channels_list}", parse_mode="HTML")
    await callback.answer()

# --- ADMIN MODERATSIYA ---
@router.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def handle_moderation(callback: CallbackQuery):
    action, post_id = callback.data.split("_")
    
    if post_id not in db['pending_posts']:
        await callback.answer("Bu e'lon allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    
    data = db['pending_posts'][post_id]
    user_id = data['user_id']
    bot = callback.bot
    
    channel_post_text = (
        f"<blockquote>"
        f"🌍 <b>Hudud:</b> {data['region']}\n"
        f"🏢 <b>Kompaniya:</b> {data['company']}\n"
        f"💼 <b>Ish o'rni:</b> {data['position']}\n\n"
        f"👤 <b>Yosh chegarasi:</b> {data['age']}\n"
        f"📌 <b>Talablar:</b> {data['requirements']}\n"
        f"💰 <b>Maosh:</b> {data['salary']}\n"
        f"⏰ <b>Ish vaqti:</b> {data['work_schedule']}\n"
        f"📍 <b>Manzil:</b> {data['location']}\n"
        f"📞 <b>Aloqa:</b> {data['phone']}"
        f"</blockquote>\n\n"
        f"👉 @Ishbor_Live | @Ishlar_Live"
    )
    
    if action == "approve":
        for channel in CHANNELS.values():
            if data['photo_id']:
                await bot.send_photo(chat_id=channel, photo=data['photo_id'], caption=channel_post_text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=channel, text=channel_post_text, parse_mode="HTML")
        
        user_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanallarni ko'rish", url="https://t.me/Ishbor_Live")]
        ])
        
        await bot.send_message(
            chat_id=user_id,
            text="<b>🎉 Sizning to'lovingiz tasdiqlandi va anketa e'loningiz kanallarga joylandi!</b>",
            reply_markup=user_kb,
            parse_mode="HTML"
        )
        
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n<b>✅ HOLAT: Tasdiqlandi</b>", parse_mode="HTML")
        del db['pending_posts'][post_id]
        await callback.answer("E'lon muvaffaqiyatli tasdiqlandi!")
    else:
        await bot.send_message(chat_id=user_id, text="❌ Afsuski, to'lovingiz tasdiqlanmadi.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n<b>❌ HOLAT: Rad etildi</b>", parse_mode="HTML")
        del db['pending_posts'][post_id]
        await callback.answer("E'lon rad etildi.")

@router.callback_query(F.data == "user_about")
async def about_bot(callback: CallbackQuery):
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Orqaga", callback_data="main_menu")]
    ])
    await callback.message.edit_text(
        "<b>ⓘ Bot haqida:</b>\n\nBu bot orqali anketa to'ldirib @Ishbor_Live va @Ishlar_Live kanallariga ish e'lonlarini joylashtirishingiz mumkin.",
        reply_markup=back_kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "user_support")
async def support_info(callback: CallbackQuery):
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Orqaga", callback_data="main_menu")]
    ])
    await callback.message.edit_text("📞 Murojaat uchun: @mekhanizatsiya", reply_markup=back_kb)
    await callback.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
