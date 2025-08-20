import asyncio
from account_manager import AccountManager

async def main():
    manager = AccountManager()
    await manager.connect_all_accounts()
    print("✅ Аккаунты подключены:", list(manager.accounts.keys()))
    await manager.disconnect_all()

asyncio.run(main())
