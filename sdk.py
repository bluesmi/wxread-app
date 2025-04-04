import asyncio
import hashlib
import json
import random
import re
import time
import urllib.parse
from typing import Callable

import requests
from loguru import logger


class WxPusherNotifier:
    def __init__(self, spt):
        self.wxpusher_simple_url = (
            "https://wxpusher.zjiecode.com/api/send/message/{}/{}"
        )
        self.spt = spt  # 添加 spt 参数

    def push(
        self,
        content,
        attempt_times: int = 5,
        onSuccess: Callable = None,
        onRefresh: Callable = None,
        onFail: Callable = None,
    ):
        """WxPusher消息推送（极简方式）"""
        if not onSuccess:  # 定义默认回调函数，避免报错导致程序中断
            onSuccess = logger.debug
        if not onRefresh:  # 定义默认回调函数，避免报错导致程序中断
            onRefresh = logger.info
        if not onFail:  # 定义默认回调函数，避免报错导致程序中断
            onFail = logger.error
        url = self.wxpusher_simple_url.format(self.spt, content)

        for attempt in range(attempt_times):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                onSuccess(f"✅ WxPusher响应: {response.json()['msg']}")
                break
            except requests.exceptions.RequestException as e:
                onFail(f"❌ WxPusher推送失败: {e}")
                if attempt < attempt_times - 1:
                    sleep_time = random.randint(180, 360)
                    onRefresh(f"将在 {sleep_time} 秒后重试...")
                    time.sleep(sleep_time)


class WXReadSDK:
    """微信读书SDK"""

    def __init__(
        self,
        headers: dict,
        cookies: dict,
        payload: dict = None,
    ):
        self.cookies: dict = cookies
        self.headers: dict = headers
        book = {
            "appId": "wb182564874663h152492176",
            "b": "ce032b305a9bc1ce0b0dd2a",
            "c": "7cb321502467cbbc409e62d",
            "ci": 70,
            "co": 0,
            "sm": "[插图]第三部广播纪元7年，程心艾AA说",
            "pr": 74,
            "rt": 30,
            "ps": "b1d32a307a4c3259g016b67",
            "pc": "080327b07a4c3259g018787",
        }
        self.payload: dict = payload or book

    @staticmethod
    def encode_data(data):
        """数据编码"""
        return "&".join(
            f"{k}={urllib.parse.quote(str(data[k]), safe='')}"
            for k in sorted(data.keys())
        )

    @staticmethod
    def cal_hash(input_string):
        """计算哈希值"""
        _7032f5 = 0x15051505
        _cc1055 = _7032f5
        length = len(input_string)
        _19094e = length - 1

        while _19094e > 0:
            _7032f5 = 0x7FFFFFFF & (
                _7032f5 ^ ord(input_string[_19094e]) << (length - _19094e) % 30
            )
            _cc1055 = 0x7FFFFFFF & (
                _cc1055 ^ ord(input_string[_19094e - 1]) << _19094e % 30
            )
            _19094e -= 2

        return hex(_7032f5 + _cc1055)[2:].lower()

    @staticmethod
    def get_wr_skey(headers, cookies):
        """刷新cookie密钥"""
        RENEW_URL = "https://weread.qq.com/web/login/renewal"
        COOKIE_DATA = {"rq": "%2Fweb%2Fbook%2Fread"}
        response = requests.post(
            RENEW_URL,
            headers=headers,
            cookies=cookies,
            data=json.dumps(COOKIE_DATA, separators=(",", ":")),
        )
        for cookie in response.headers.get("Set-Cookie", "").split(";"):
            if "wr_skey" in cookie:
                return cookie.split("=")[-1][:8]
        return None

    def refresh(self):
        """
        刷新cookie密钥

        本函数通过发送POST请求到指定的URL来刷新用户的cookie密钥，
        以确保用户登录状态的有效性。在刷新成功后，函数会更新self.cookies中的wr_skey值。

        returns:
        - 如果刷新成功，返回True；
        - 如果刷新失败，返回False。
        """
        new_skey = self.get_wr_skey(self.headers, self.cookies)
        logger.info(f"刷新wr_skey: {self.cookies['wr_skey']}")
        if new_skey:  # 刷新成功，更新cookie中的wr_skey值
            self.cookies.update(wr_skey=new_skey)
            logger.info(f"刷新wr_skey成功: {self.cookies['wr_skey']}")
            return True
        return False

    def _prepare(self):
        KEY = "3c5c8717f3daf09iop3423zafeqoi"
        ct = int(time.time())
        ts = int(time.time() * 1000)
        rn = random.randint(0, 1000)
        sg = hashlib.sha256(f"{ts}{rn}{KEY}".encode()).hexdigest()
        self.payload.update(ct=ct, ts=ts, rn=rn, sg=sg)

    def read(self) -> dict:
        """阅读接口"""
        READ_URL = "https://weread.qq.com/web/book/read"
        self._prepare()
        s = self.cal_hash(self.encode_data(self.payload))
        response = requests.post(
            READ_URL,
            headers=self.headers,
            cookies=self.cookies,
            data=json.dumps({**self.payload, "s": s}, separators=(",", ":")),
        )
        resData = response.json()
        return resData

    @staticmethod
    def parse_curl(curl_cmd):
        """
        解析 curl 命令，提取 headers、cookies 和 payload 并转换为字典。
        :param curl_cmd: curl 命令字符串
        :return: headers 字典、cookies 字典、payload 字典
        """
        headers = {}
        cookies = {}
        payload = {}

        # 提取 headers
        header_pattern = r"-H \'(.*?): (.*?)\'"
        header_matches = re.findall(header_pattern, curl_cmd)
        for key, value in header_matches:
            headers[key] = value

        # 提取 cookies
        cookie_pattern = r"-b \'(.*?)\'"
        cookie_match = re.search(cookie_pattern, curl_cmd)
        if cookie_match:
            cookie_str = cookie_match.group(1)
            cookie_pairs = cookie_str.split("; ")
            for pair in cookie_pairs:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    cookies[key] = value

        # 提取 payload
        payload_pattern = r"--data-raw \'(.*?)\'"
        payload_match = re.search(payload_pattern, curl_cmd)
        if payload_match:
            payload_str = payload_match.group(1)
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                raise ValueError("Could not parse payload as JSON.")
        payload.pop("s", None)  # 移除s字段
        return {"headers": headers, "cookies": cookies, "payload": payload}

    @classmethod
    def from_curl_bash(cls, bash_path: str):
        """从curl中创建实例"""
        with open(bash_path, "r", encoding="utf8") as f:
            curl_command = f.read()
        config = cls.parse_curl(curl_command)
        return cls(**config)  # type: ignore

    async def sync_run(
        self,
        loop_num: int = 5,
        residence_second: int = 30,  # 单位秒,
        onStart: Callable = None,
        onSuccess: Callable = None,
        onRefresh: Callable = None,
        onFail: Callable = None,
        onFinish: Callable = None,
    ):
        if not onStart:  # 定义默认回调函数，避免报错导致程序中断
            onStart = logger.info
        if not onSuccess:  # 定义默认回调函数，避免报错导致程序中断
            onSuccess = logger.debug
        if not onRefresh:  # 定义默认回调函数，避免报错导致程序中断
            onRefresh = logger.info
        if not onFail:  # 定义默认回调函数，避免报错导致程序中断
            onFail = logger.error
        if not onFinish:  # 定义默认回调函数，避免报错导致程序中断
            onFinish = logger.info

        index = 1
        while index <= loop_num:
            onStart(f"⏱️ 尝试第 {index}/{loop_num} 次阅读...")
            resData: dict = self.read()
            if "succ" in resData:
                index += 1
                await asyncio.sleep(residence_second)
                onSuccess(
                    f"✅ 阅读成功，阅读进度：{(index - 1) * (residence_second / 60)} 分钟"
                )
            else:
                logger.warning("❌ cookie 已过期，尝试刷新...")
                if self.refresh():
                    onRefresh("🔄 重新本次阅读。")
                    # 保存刷新后的config
                    continue
                else:
                    msg = "❌ 无法获取新密钥或者WXREAD_CURL_BASH配置有误，终止运行。"
                    onFail(msg)
        onFinish(f"🎉 阅读脚本已完成！成功阅读 {loop_num*(residence_second / 60)} 分钟")
