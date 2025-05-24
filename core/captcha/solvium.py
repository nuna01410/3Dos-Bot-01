import asyncio
import httpx

from typing import Any

from better_proxy import Proxy


class SolviumCaptchaSolver:
    def __init__(
        self,
        api_key: str,
        max_attempts: int,
        proxy: str = None,
        base_url: str = "https://captcha.solvium.io/api/v1",
    ):
        self.api_key = api_key
        self.max_attempts = max_attempts
        self.base_url = base_url.rstrip("/")

        if proxy:
            self.client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
                proxies={"http://": proxy, "https://": proxy},
            )
        else:
            self.client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )


    async def create_recaptcha_task(self, site_key: str, page_url: str, action: str, proxy: str) -> tuple[bool, Any] | tuple[bool, str]:
        url = f"{self.base_url}/task/recaptcha-v3"
        proxy = Proxy.from_str(proxy)
        proxy = f"http://{proxy.login}:{proxy.password}@{proxy.host}:{proxy.port}"
        params = {"url": page_url, "sitekey": site_key, "action": action, "ref": "jammer", "proxy": proxy}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            result = response.json()

            if result.get("message") == "Task created" and "task_id" in result:
                return True, result["task_id"]

            return False, f"Error while creating task: {result}"

        except httpx.HTTPStatusError as err:
            return False, f"HTTP error while creating task: {err}"

        except httpx.TimeoutException:
            return False, "Timeout error while creating task"

        except Exception as e:
            return False, f"Unexpected error while creating task: {e}"

    async def get_task_result(self, task_id: str) -> tuple[bool, Any] | tuple[bool, str]:
        for _ in range(self.max_attempts):
            try:
                response = await self.client.get(f"{self.base_url}/task/status/{task_id}")
                response.raise_for_status()
                result = response.json()

                if (
                    result.get("status") == "completed"
                    and result.get("result")
                    and result["result"].get("solution")
                ):
                    solution = result["result"]["solution"]
                    return True, solution

                elif result.get("status") in ["running", "pending"]:
                    await asyncio.sleep(0.5)
                    continue

                else:
                    error = result["result"]["error"]
                    return False, f"Error while getting ReCaptcha result: {error}"

            except httpx.HTTPStatusError as err:
                return False, f"HTTP error occurred while solving ReCaptcha: {err}"

            except httpx.TimeoutException:
                return False, "Timeout error occurred while solving ReCaptcha"

            except Exception as e:
                return False, f"Unexpected error occurred while solving ReCaptcha: {e}"

        return False, "Max attempts exhausted"

    async def solve_recaptcha(
        self, site_key: str, page_url: str, action: str, proxy: str
    ) -> tuple[Any, Any] | tuple[bool, Any] | tuple[bool, str]:
        try:
            success, result = await self.create_recaptcha_task(site_key, page_url, action, proxy)
            if not success:
                return success, result

            return await self.get_task_result(result)

        except Exception as e:
            return False, f"Error occurred while solving ReCaptcha: {e}"
