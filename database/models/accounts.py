import asyncio
import random

import pytz

from datetime import datetime
from tortoise import Model, fields
from tortoise.expressions import Q


class Accounts(Model):
    email = fields.CharField(max_length=255, unique=True)
    email_password = fields.CharField(max_length=255, null=True)
    account_password = fields.CharField(max_length=255, null=True)

    access_token = fields.CharField(max_length=2048, null=True)
    sui_address = fields.CharField(max_length=255, null=True)
    api_secret = fields.CharField(max_length=255, null=True)
    referral_code = fields.CharField(max_length=255, null=True)

    active_account_proxy = fields.CharField(max_length=255, null=True)
    sleep_until = fields.DatetimeField(null=True)

    class Meta:
        table = "3dos_accounts"

    @classmethod
    async def get_account(cls, email: str):
        return await cls.get_or_none(email=email)

    @classmethod
    async def get_accounts(cls):
        return await cls.all()

    @classmethod
    async def get_accounts_stats(cls, emails: list[str] = None) -> tuple[int, int]:
        query = cls.all()
        if emails:
            query = query.filter(email__in=emails)

        accounts = await query
        now = datetime.now(pytz.UTC)

        accounts_with_expired_sleep = len([
            account for account in accounts
            if (account.sleep_until is None) or (account.sleep_until <= now)
        ])

        accounts_waiting_sleep = len([
            account for account in accounts
            if account.sleep_until and account.sleep_until > now
        ])

        return accounts_with_expired_sleep, accounts_waiting_sleep

    @classmethod
    async def get_random_invite_code(cls) -> str | None:
        accounts_with_code = await cls.filter(~Q(referral_code=None)).values_list("referral_code", flat=True)
        if not accounts_with_code:
            return None
        return random.choice(accounts_with_code)

    async def update_account_proxy(self, proxy: str):
        self.active_account_proxy = proxy
        await self.save()

    @classmethod
    async def get_account_proxy(cls, email: str) -> str:
        account = await cls.get_account(email=email)
        return account.active_account_proxy if account else ""

    @classmethod
    async def create_or_update_account(
            cls,
            email: str,
            email_password: str = None,
            account_password: str = None,
            access_token: str = None,
            api_secret: str = None,
            sui_address: str = None,
            proxy: str = None,
            referral_code: str = None
    ) -> "Accounts":
        account = await cls.get_account(email=email)
        if account is None:
            account = await cls.create(
                email=email,
                email_password=email_password,
                account_password=account_password,
                access_token=access_token,
                api_secret=api_secret,
                sui_address=sui_address,
                active_account_proxy=proxy,
                referral_code=referral_code
            )
        else:
            if email_password:
                account.email_password = email_password
            if account_password:
                account.account_password = account_password
            if access_token:
                account.access_token = access_token
            if api_secret:
                account.api_secret = api_secret
            if sui_address:
                account.sui_address = sui_address
            if proxy:
                account.active_account_proxy = proxy
            if referral_code:
                account.referral_code = referral_code
            await account.save()

        return account

    async def update_account(
            self,
            email_password: str = None,
            account_password: str = None,
            access_token: str = None,
            api_secret: str = None,
            sui_address: str = None,
            proxy: str = None,
            referral_code: str = None
    ) -> "Accounts":
        if email_password:
            self.email_password = email_password
        if account_password:
            self.account_password = account_password
        if access_token:
            self.access_token = access_token
        if api_secret:
            self.api_secret = api_secret
        if sui_address:
            self.sui_address = sui_address
        if proxy:
            self.active_account_proxy = proxy
        if referral_code:
            self.referral_code = referral_code

        await self.save()
        return self

    @classmethod
    async def get_access_token(cls, email: str) -> str | None:
        account = await cls.get_account(email=email)
        return account.access_token if account else None

    @classmethod
    async def get_api_secret(cls, email: str) -> str | None:
        account = await cls.get_account(email=email)
        return account.api_secret if account else None

    @classmethod
    async def delete_account(cls, email: str) -> bool:
        account = await cls.get_account(email=email)
        if account is None:
            return False
        await account.delete()
        return True

    async def set_sleep_until(self, sleep_until: datetime) -> "Accounts":
        if not isinstance(sleep_until, datetime):
            raise ValueError("sleep_until must be a datetime object")

        if sleep_until.tzinfo is None:
            sleep_until = pytz.UTC.localize(sleep_until)
        else:
            sleep_until = sleep_until.astimezone(pytz.UTC)

        self.sleep_until = sleep_until
        await self.save()
        return self

    @classmethod
    async def clear_all_accounts_proxies(cls) -> int:
        accounts = await cls.all()

        async def clear_proxy(account: Accounts):
            account.active_account_proxy = None
            await account.save()

        tasks = [asyncio.create_task(clear_proxy(account)) for account in accounts]
        await asyncio.gather(*tasks)

        return len(accounts)
