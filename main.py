import asyncio
import time
from telethon import TelegramClient, events, Button
from account_manager import AccountManager
from database import db
from config import *

class SpamBot:
    def __init__(self):
        self.bot = TelegramClient('bot_session', API_ID, API_HASH)
        self.account_manager = AccountManager()
        self.active_tasks = []
        self.waiting_for_spam = None
        self.waiting_for_broadcast = False
        self.waiting_for_user_id = None
    
    async def start(self):
        await self.account_manager.connect_all_accounts()
        await self.bot.start(bot_token=BOT_TOKEN)
        self.register_handlers()
        await self.run_forever()
    
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await self.handle_start(event)
        
        @self.bot.on(events.CallbackQuery)
        async def callback_handler(event):
            await self.handle_callback(event)
        
        @self.bot.on(events.NewMessage)
        async def message_handler(event):
            await self.handle_message(event)
    
    async def handle_start(self, event):
        user_id = event.sender_id
        username = event.sender.username or "пользователь"
        
        if not db.get_user(user_id):
            parts = event.text.split()
            referral_code = parts[1] if len(parts) > 1 else None
            referred_by = None
            
            if referral_code and referral_code.startswith('ref'):
                ref_cursor = db.conn.cursor()
                ref_cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referral_code,))
                ref_result = ref_cursor.fetchone()
                if ref_result:
                    referred_by = ref_result[0]
                    db.add_referral(referred_by, user_id)
            
            db.create_user(user_id, username, f"ref{user_id}", referred_by)
        
        buttons = [
            [Button.inline("💰 Баланс", b"balance"),
             Button.inline("🎫 Подписки", b"subscriptions")],
            [Button.inline("👥 Реферальная система", b"referral"),
             Button.inline("⚡ Начать спам", b"start_spam")],
            [Button.inline("🆘 Помощь", b"help")]
        ]
        
        if user_id == ADMIN_ID:
            buttons.append([Button.inline("👑 Админ панель", b"admin_panel")])
        
        await event.reply(
            f"👋 Добро пожаловать, {username}!\n"
            f"🤖 @{BOT_USERNAME} - мощный инструмент для спама\n\n"
            "Выберите действие:",
            buttons=buttons
        )
    
    async def handle_callback(self, event):
        user_id = event.sender_id
        data = event.data.decode()
        
        if data == "balance":
            balance = db.get_balance(user_id)
            await event.edit(
                f"💰 Ваш баланс: {balance} монет\n\n"
                f"💎 Обычная подписка: {REGULAR_SUB_PRICE} монет\n"
                f"🚀 Премиум подписка: {PREMIUM_SUB_PRICE} монет",
                buttons=[[Button.inline("🔙 Назад", b"back")]]
            )
        
        elif data == "subscriptions":
            sub_type = db.get_subscription(user_id)
            balance = db.get_balance(user_id)
            
            if sub_type == 'none':
                status = "❌ Нет активной подписки"
            elif sub_type == 'regular':
                status = "✅ Обычная подписка активна"
            else:
                status = "🚀 ПРЕМИУМ подписка активна"
            
            buttons = []
            if balance >= REGULAR_SUB_PRICE and sub_type != 'regular':
                buttons.append([Button.inline(f"💎 Купить обычную ({REGULAR_SUB_PRICE} монет)", b"buy_regular")])
            if balance >= PREMIUM_SUB_PRICE and sub_type != 'premium':
                buttons.append([Button.inline(f"🚀 Купить премиум ({PREMIUM_SUB_PRICE} монет)", b"buy_premium")])
            buttons.append([Button.inline("🔙 Назад", b"back")])
            
            await event.edit(
                f"{status}\n💰 Баланс: {balance} монет\n\n"
                "💎 Обычная подписка:\n"
                f"- Спам: {SPAM_DURATION_REGULAR} сек\n"
                f"- CD: {CD_REGULAR//60} мин\n"
                f"- Цена: {REGULAR_SUB_PRICE} монет\n\n"
                "🚀 Премиум подписка:\n"
                f"- Спам: {SPAM_DURATION_PREMIUM} сек\n"
                f"- CD: {CD_PREMIUM//60} мин\n"
                f"- Скорость: {1/DELAY_PREMIUM:.1f} сообщ/сек\n"
                f"- Цена: {PREMIUM_SUB_PRICE} монет",
                buttons=buttons
            )
        
        elif data == "referral":
            total_ref, claimed_ref = db.get_referral_stats(user_id)
            user = db.get_user(user_id)
            ref_code = user[5] if user else f"ref{user_id}"
            ref_link = f"https://t.me/{BOT_USERNAME}?start={ref_code}"
            
            await event.edit(
                f"👥 Реферальная система\n\n"
                f"🔗 Ваша ссылка: {ref_link}\n"
                f"👥 Приглашено: {total_ref} человек\n"
                f"💰 Заработано: {total_ref * REFERRAL_REWARD} монет\n\n"
                f"💎 За каждого приглашенного получаете {REFERRAL_REWARD} монет!",
                buttons=[[Button.inline("🔙 Назад", b"back")]]
            )
        
        elif data == "start_spam":
            await self.handle_spam_start(event)
        
        elif data == "help":
            await event.edit(
                "🆘 Помощь\n\n"
                "🤖 Как использовать бота:\n"
                "1. Купите подписку у @pencurel\n"
                "2. Нажмите 'Начать спам'\n"
                "3. Отправьте ссылку на группу и сообщение\n"
                "4. Бот начнет автоматический спам!\n\n"
                "💎 Обычная: 10 сек спама, CD 30 мин\n"
                "🚀 Премиум: 15 сек спама, CD 10 мин, высокая скорость",
                buttons=[[Button.inline("🔙 Назад", b"back")]]
            )
        
        elif data == "admin_panel" and user_id == ADMIN_ID:
            await self.show_admin_panel(event)
        
        elif data == "back":
            await self.show_main_menu(event)
        
        elif data.startswith("buy_"):
            await self.handle_purchase(event, data)
        
        elif data == "admin_broadcast" and user_id == ADMIN_ID:
            await event.edit("📢 Введите сообщение для рассылки:")
            self.waiting_for_broadcast = True
        
        elif data == "admin_stats" and user_id == ADMIN_ID:
            users = db.get_all_users()
            regular_count = premium_count = total_balance = 0
            for user in users:
                if user[3] == 'regular': regular_count += 1
                elif user[3] == 'premium': premium_count += 1
                total_balance += user[2]
            
            await event.edit(
                f"📊 Статистика бота\n\n"
                f"👥 Всего пользователей: {len(users)}\n"
                f"💎 Обычных подписок: {regular_count}\n"
                f"🚀 Премиум подписок: {premium_count}\n"
                f"💰 Общий баланс: {total_balance} монет\n"
                f"🤖 Активных сессий: {len(self.account_manager.accounts)}",
                buttons=[[Button.inline("🔙 Назад", b"admin_back")]]
            )
        
        elif data == "admin_give_sub" and user_id == ADMIN_ID:
            await self.show_give_subscription_menu(event)
        
        elif data.startswith("give_sub_") and user_id == ADMIN_ID:
            await self.handle_give_subscription(event, data)
        
        elif data == "admin_back" and user_id == ADMIN_ID:
            await self.show_admin_panel(event)
    
    async def handle_message(self, event):
        if self.waiting_for_spam and event.sender_id == self.waiting_for_spam:
            await self.process_spam_request(event)
        elif self.waiting_for_broadcast and event.sender_id == ADMIN_ID:
            await self.process_broadcast(event)
        elif self.waiting_for_user_id and event.sender_id == ADMIN_ID:
            await self.process_user_id_input(event)
    
    async def handle_spam_start(self, event):
        user_id = event.sender_id
        sub_type = db.get_subscription(user_id)
        
        if sub_type == 'none':
            await event.edit("❌ У вас нет активной подписки!", buttons=[[Button.inline("🔙 Назад", b"back")]])
            return
        
        last_spam = db.get_cooldown(user_id)
        if last_spam:
            cd_time = CD_PREMIUM if sub_type == 'premium' else CD_REGULAR
            time_left = cd_time - (time.time() - last_spam.timestamp())
            if time_left > 0:
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                await event.edit(f"⏳ CD: {minutes}мин {seconds}сек осталось", buttons=[[Button.inline("🔙 Назад", b"back")]])
                return
        
        await event.edit("🔗 Отправьте ссылку на группу и сообщение в формате:\n\n<code>ссылка_на_группу ваше_сообщение</code>")
        self.waiting_for_spam = user_id
    
    async def handle_purchase(self, event, data):
        user_id = event.sender_id
        balance = db.get_balance(user_id)
        
        if "regular" in data:
            if balance >= REGULAR_SUB_PRICE:
                db.update_balance(user_id, -REGULAR_SUB_PRICE)
                db.set_subscription(user_id, 'regular')
                await event.edit("✅ Обычная подписка активирована на 7 дней!", buttons=[[Button.inline("🔙 Назад", b"back")]])
            else:
                await event.edit("❌ Недостаточно монет!", buttons=[[Button.inline("🔙 Назад", b"back")]])
        
        elif "premium" in data:
            if balance >= PREMIUM_SUB_PRICE:
                db.update_balance(user_id, -PREMIUM_SUB_PRICE)
                db.set_subscription(user_id, 'premium')
                await event.edit("🚀 ПРЕМИУМ подписка активирована на 7 дней!", buttons=[[Button.inline("🔙 Назад", b"back")]])
            else:
                await event.edit("❌ Недостаточно монет!", buttons=[[Button.inline("🔙 Назад", b"back")]])
    
    async def show_main_menu(self, event):
        user_id = event.sender_id
        username = (await event.get_sender()).username or "пользователь"
        
        buttons = [
            [Button.inline("💰 Баланс", b"balance"),
             Button.inline("🎫 Подписки", b"subscriptions")],
            [Button.inline("👥 Реферальная система", b"referral"),
             Button.inline("⚡ Начать спам", b"start_spam")],
            [Button.inline("🆘 Помощь", b"help")]
        ]
        
        if user_id == ADMIN_ID:
            buttons.append([Button.inline("👑 Админ панель", b"admin_panel")])
        
        await event.edit(
            f"👋 Добро пожаловать, {username}!\n"
            f"🤖 @{BOT_USERNAME} - мощный инструмент для спама\n\n"
            "Выберите действие:",
            buttons=buttons
        )
    
    async def show_admin_panel(self, event):
        buttons = [
            [Button.inline("📢 Сделать рассылку", b"admin_broadcast")],
            [Button.inline("📊 Статистика бота", b"admin_stats")],
            [Button.inline("💎 Выдать подписку", b"admin_give_sub")],
            [Button.inline("🔙 Назад", b"back")]
        ]
        await event.edit("👑 Админ панель", buttons=buttons)
    
    async def show_give_subscription_menu(self, event):
        buttons = [
            [Button.inline("💎 Выдать обычную подписку", b"give_sub_regular")],
            [Button.inline("🚀 Выдать премиум подписку", b"give_sub_premium")],
            [Button.inline("❌ Снять подписку", b"give_sub_none")],
            [Button.inline("🔙 Назад", b"admin_back")]
        ]
        await event.edit("💎 Выберите тип подписки для выдачи:", buttons=buttons)
    
    async def handle_give_subscription(self, event, data):
        sub_type = data.replace("give_sub_", "")
        
        if sub_type == "none":
            await event.edit("❌ Введите ID пользователя для снятия подписки:")
            self.waiting_for_user_id = {"action": "remove_sub"}
        else:
            await event.edit(f"💎 Введите ID пользователя для выдачи {sub_type} подписки:")
            self.waiting_for_user_id = {"action": "give_sub", "sub_type": sub_type}
    
    async def process_user_id_input(self, event):
        try:
            user_id_input = event.text.strip()
            
            if not user_id_input.isdigit():
                await event.reply("❌ ID пользователя должен быть числом!")
                return
            
            target_user_id = int(user_id_input)
            action_info = self.waiting_for_user_id
            
            if action_info["action"] == "give_sub":
                sub_type = action_info["sub_type"]
                db.set_subscription(target_user_id, sub_type)
                
                target_user = db.get_user(target_user_id)
                username = target_user[1] if target_user and target_user[1] else f"ID{target_user_id}"
                
                await event.reply(f"✅ Пользователю @{username} выдана {sub_type} подписка на 7 дней!")
                
            elif action_info["action"] == "remove_sub":
                db.set_subscription(target_user_id, 'none')
                
                target_user = db.get_user(target_user_id)
                username = target_user[1] if target_user and target_user[1] else f"ID{target_user_id}"
                
                await event.reply(f"✅ У пользователя @{username} снята подписка!")
            
            try:
                sub_text = "премиум" if action_info.get("sub_type") == "premium" else "обычную" if action_info.get("sub_type") == "regular" else "снята"
                await self.bot.send_message(
                    target_user_id,
                    f"🎉 Администратор выдал вам {sub_text} подписку!\n"
                    f"🤖 Теперь вы можете использовать @{BOT_USERNAME}"
                )
            except:
                pass
                
        except Exception as e:
            await event.reply(f"❌ Ошибка: {e}")
        finally:
            self.waiting_for_user_id = None
    
    async def process_spam_request(self, event):
        try:
            user_id = event.sender_id
            args = event.text.split(' ', 1)
            if len(args) < 2:
                await event.reply("❌ Неверный формат! Нужно: ссылка сообщение")
                return
            
            group_link, message = args[0], args[1]
            sub_type = db.get_subscription(user_id)
            
            db.set_cooldown(user_id)
            
            duration = SPAM_DURATION_PREMIUM if sub_type == 'premium' else SPAM_DURATION_REGULAR
            delay = DELAY_PREMIUM if sub_type == 'premium' else DELAY_REGULAR
            
            task = asyncio.create_task(self.start_spam(group_link, message, duration, delay))
            self.active_tasks.append(task)
            
            await event.reply(f"🚀 Спам запущен на {duration} секунд!")
            self.waiting_for_spam = None
            
        except Exception as e:
            await event.reply(f"❌ Ошибка: {e}")
            self.waiting_for_spam = None
    
    async def process_broadcast(self, event):
        message_text = event.text
        users = db.get_all_users()
        sent = failed = 0
        
        for user in users:
            try:
                await event.client.send_message(user[0], message_text)
                sent += 1
            except:
                failed += 1
            await asyncio.sleep(0.1)
        
        db.add_broadcast(ADMIN_ID, message_text, sent, failed)
        await event.reply(f"📢 Рассылка завершена!\n✅ Отправлено: {sent}\n❌ Не отправлено: {failed}")
        self.waiting_for_broadcast = False
    
    async def start_spam(self, group_link, message, duration, delay):
        try:
            start_time = time.time()
            success_count = 0
            
            while time.time() - start_time < duration:
                free_accounts = self.account_manager.get_free_accounts(MAX_CONCURRENT_ACCOUNTS)
                if not free_accounts:
                    await asyncio.sleep(0.1)
                    continue
                
                tasks = []
                for account in free_accounts[:BATCH_SIZE]:
                    task = asyncio.create_task(self.process_account(account, group_link, message))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                success_count += sum(1 for r in results if isinstance(r, dict) and r.get('sent'))
                
                await asyncio.sleep(delay)
            
            print(f"✅ Спам завершен. Успешных отправок: {success_count}")
            
        except Exception as e:
            print(f"❌ Ошибка спама: {e}")
    
    async def process_account(self, account, group_link, message):
        try:
            self.account_manager.accounts[account['session_name']]['is_busy'] = True
            client = account['client']
            
            entity, joined, banned = await self.account_manager.join_group(client, group_link)
            if not joined:
                return {'sent': False}
            
            sent = await self.account_manager.send_message_to_group(client, entity, message)
            return {'sent': sent}
            
        except:
            return {'sent': False}
        finally:
            self.account_manager.accounts[account['session_name']]['is_busy'] = False
    
    async def run_forever(self):
        await self.bot.run_until_disconnected()

async def main():
    bot = SpamBot()
    await bot.start()

if __name__ == '__main__':
    asyncio.run(main())