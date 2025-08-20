import os
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
import asyncio
from config import SESSIONS_DIR, API_ID, API_HASH, SPAM_SIGNATURE, PROXY, USE_PROXY
import re

class AccountManager:
    def __init__(self):
        self.sessions_dir = SESSIONS_DIR
        self.accounts = {}
        self._ensure_sessions_dir()
    
    def _ensure_sessions_dir(self):
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
        print(f"📁 Папка сессий: {self.sessions_dir}")
    
    def get_session_files(self):
        session_files = []
        for file in os.listdir(self.sessions_dir):
            if file.endswith('.session'):
                session_files.append(file)
                print(f"📄 Найден session файл: {file}")
            elif file.endswith('.json'):
                try:
                    with open(os.path.join(self.sessions_dir, file), 'r') as f:
                        data = json.load(f)
                        if 'session_string' in data:
                            session_files.append(file)
                            print(f"📄 Найден JSON session: {file}")
                except:
                    pass
        return session_files
    
    async def connect_account(self, session_name):
        try:
            session_path = os.path.join(self.sessions_dir, session_name)
            print(f"🔗 Подключаем аккаунт: {session_name}")
            
            # Используем прокси если включено
            proxy = PROXY if USE_PROXY else None
            
            if session_name.endswith('.json'):
                with open(session_path, 'r') as f:
                    data = json.load(f)
                    session_string = data.get('session_string')
                    if not session_string:
                        print(f"❌ Нет session_string в {session_name}")
                        return None
                    
                    client = TelegramClient(StringSession(session_string), API_ID, API_HASH, proxy=proxy)
            else:
                client = TelegramClient(session_path, API_ID, API_HASH, proxy=proxy)
            
            await client.connect()
            
            if not await client.is_user_authorized():
                print(f"❌ Аккаунт {session_name} не авторизован!")
                await client.disconnect()
                return None
            
            me = await client.get_me()
            username = me.username or "no_username"
            print(f"✅ Успешно подключен: {me.first_name} (@{username})")
            
            self.accounts[session_name] = {
                'client': client,
                'me': me,
                'is_busy': False,
                'username': username,
                'user_id': me.id
            }
            
            return client
            
        except Exception as e:
            print(f"❌ Ошибка подключения {session_name}: {e}")
            return None
    
    async def process_invite_link(self, client, group_link):
        try:
            if 't.me/' in group_link:
                hash_match = re.search(r't\.me/\+([a-zA-Z0-9_-]+)', group_link)
            else:
                hash_match = re.search(r'\+([a-zA-Z0-9_-]+)', group_link)
            
            if hash_match:
                invite_hash = hash_match.group(1)
                print(f"🔑 Инвайт хэш: {invite_hash}")
                try:
                    result = await client(ImportChatInviteRequest(invite_hash))
                    if hasattr(result, 'chats') and result.chats:
                        return result.chats[0], True
                    return None, True
                except Exception as e:
                    print(f"❌ Ошибка инвайта: {e}")
                    return None, False
            return None, False
        except Exception as e:
            print(f"❌ Ошибка обработки инвайта: {e}")
            return None, False
    
    async def join_group(self, client, group_link):
        try:
            print(f"🔗 Вход в группу: {group_link}")
            
            if '+' in group_link:
                chat, joined = await self.process_invite_link(client, group_link)
                if joined and chat:
                    return chat, True, False
            
            try:
                entity = await client.get_entity(group_link)
                if hasattr(entity, 'title'):
                    try:
                        await client(JoinChannelRequest(entity))
                        print(f"✅ Вошли в группу: {entity.title}")
                        return entity, True, False
                    except Exception as e:
                        print(f"⚠️ Уже в группе: {e}")
                        return entity, True, False
                else:
                    return entity, True, False
            except Exception as e:
                print(f"❌ Ошибка получения entity: {e}")
                return None, False, False
        except Exception as e:
            print(f"❌ Общая ошибка входа: {e}")
            return None, False, False
    
    async def send_message_to_group(self, client, entity, message):
        try:
            full_message = message + SPAM_SIGNATURE
            await client.send_message(entity, full_message)
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False
    
    async def connect_all_accounts(self):
        print("🔍 Ищем session файлы...")
        session_files = self.get_session_files()
        
        if not session_files:
            print("❌ Не найдено session файлов!")
            return
        
        print(f"📁 Найдено {len(session_files)} session файлов")
        
        tasks = []
        for session_file in session_files:
            task = asyncio.create_task(self.connect_account(session_file))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for result in results if result is not None)
        print(f"✅ Успешно подключено: {successful}/{len(session_files)} аккаунтов")
    
    async def disconnect_all(self):
        for session_name, account_info in self.accounts.items():
            try:
                await account_info['client'].disconnect()
                print(f"🔌 Отключен: {session_name}")
            except:
                pass
        self.accounts.clear()
    
    def get_free_accounts(self, limit=None):
        free_accounts = []
        for name, info in self.accounts.items():
            if not info['is_busy']:
                free_accounts.append({
                    'session_name': name,
                    'client': info['client'],
                    'username': info['username'],
                    'user_id': info['user_id']
                })
                if limit and len(free_accounts) >= limit:
                    break
        return free_accounts