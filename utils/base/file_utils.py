import asyncio
import time
import aiofiles

from pathlib import Path
from aiocsv import AsyncWriter
from loguru import logger

from models import ModuleType, OperationResult



class FileOperations:
    def __init__(self, base_path: str = "./results"):
        self.base_path = Path(base_path)
        self.lock = asyncio.Lock()
        self.module_paths: dict[ModuleType, dict[str, Path]] = {
            "register": {
                "success": self.base_path / "registration" / "registration_success.txt",
                "failed": self.base_path / "registration" / "registration_failed.txt",
            },
            "stats": {
                "base": self.base_path / "stats" / "accounts_stats.csv",
            },
            "accounts": {
                "unverified": self.base_path / "accounts" / "unverified_accounts.txt",
                "banned": self.base_path / "accounts" / "banned_accounts.txt",
                "unregistered": self.base_path / "accounts" / "unregistered_accounts.txt",
                "unlogged": self.base_path / "accounts" / "unlogged_accounts.txt",
            },
            "verify": {
                "success": self.base_path / "re_verify" / "verify_success.txt",
                "failed": self.base_path / "re_verify" / "verify_failed.txt",
            },
            "login": {
                "success": self.base_path / "login" / "login_success.txt",
                "failed": self.base_path / "login" / "login_failed.txt",
            },
        }

    async def setup_files(self):
        self.base_path.mkdir(exist_ok=True)
        for module_name, module_paths in self.module_paths.items():
            for path_key, path in module_paths.items():
                path.parent.mkdir(parents=True, exist_ok=True)

                if module_name == "stats":
                    continue
                else:
                    path.touch(exist_ok=True)

    async def setup_stats(self):
        self.base_path.mkdir(exist_ok=True)

        for module_name, module_paths in self.module_paths.items():
            if module_name == "stats":
                timestamp = int(time.time())

                for path_key, path in module_paths.items():
                    path.parent.mkdir(parents=True, exist_ok=True)

                    if path_key == "base":
                        new_path = path.parent / f"accounts_stats_{timestamp}.csv"
                        self.module_paths[module_name][path_key] = new_path
                        path = new_path

                        async with aiofiles.open(path, "w") as f:
                            writer = AsyncWriter(f)
                            await writer.writerow([
                                "Email",
                                "Email Password",
                                "Account Password",
                                "Referral Code",
                                "API Secret",
                                "Current Tier",
                                "Loyalty Points",
                                "Total Referrals",
                                "SUI Address",
                                "Next Tier",
                            ])

    async def export_result(self, result: OperationResult, module: ModuleType):
        if module not in self.module_paths:
            raise ValueError(f"Unknown module: {module}")

        file_path = self.module_paths[module][
            "success" if result["success"] else "failed"
        ]

        async with self.lock:
            try:
                async with aiofiles.open(file_path, "a") as file:
                    if result["email_password"] and not result["email_password"] and not result["account_password"]:
                        await file.write(f"{result['email']}\n")

                    elif result["email"] and result["email_password"] and not result["account_password"]:
                        await file.write(f"{result['email']}:{result['email_password']}\n")

                    elif result["account_password"] and not result["email_password"] and result["account_password"]:
                        await file.write(f"{result['email']}:{result['account_password']}\n")

                    elif result["email"] and result["email_password"] and result["account_password"]:
                        await file.write(f"{result['email']}:{result['email_password']}:{result['account_password']}\n")

            except IOError as e:
                logger.error(f"Account: {result['email']} | Error writing to file (IOError): {e}")
            except Exception as e:
                logger.error(f"Account: {result['email']} | Error writing to file: {e}")

    async def export_invalid_account(self, email: str, email_password: str = None, account_password: str = None, reason: str = None):
        if reason not in self.module_paths["accounts"]:
            raise ValueError(f"Unknown reason: {reason}")

        file_path = self.module_paths["accounts"][reason]
        async with self.lock:
            try:
                async with aiofiles.open(file_path, "a") as file:
                    if email and not email_password and not account_password:
                        await file.write(f"{email}\n")

                    elif email and email_password and not account_password:
                        await file.write(f"{email}:{email_password}\n")

                    elif email and email_password and account_password:
                        await file.write(f"{email}:{email_password}:{account_password}\n")

            except IOError as e:
                logger.error(f"Account: {email} | Error writing to file (IOError): {e}")
            except Exception as e:
                logger.error(f"Account: {email} | Error writing to file: {e}")

    async def export_stats(self, result: OperationResult):
        file_path = self.module_paths["stats"]["base"]
        async with self.lock:
            try:
                async with aiofiles.open(file_path, mode="a", newline="") as f:
                    writer = AsyncWriter(f)

                    if result["success"]:
                        await writer.writerow(
                            [
                                result["data"]["email"],
                                result["data"]["email_password"],
                                result["data"]["account_password"],
                                result["data"]["referral_code"],
                                result["data"]["api_secret"],
                                result["data"]["tier"]["tier_name"],
                                result["data"]["loyalty_points"],
                                result["data"]["total_referrals"] if result["data"]["total_referrals"] else "0",
                                result["data"]["sui_address"],
                                result["data"]["next_tier"]["tier_name"],
                            ]
                        )

                    else:
                        await writer.writerow(
                            [
                                result["email"],
                                "N/A",
                                "N/A",
                                "N/A",
                                "N/A",
                                "N/A",
                                "N/A",
                                "N/A",
                                "N/A",
                                "N/A",
                            ]
                        )

            except IOError as e:
                logger.error(f"Error writing to file (IOError): {e}")

            except Exception as e:
                logger.error(f"Error writing to file: {e}")
