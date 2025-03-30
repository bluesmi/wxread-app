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
        payload: dict,
        config_path: str = None,
    ):
        self.cookies: dict = cookies
        self.headers: dict = headers
        self.payload: dict = payload
        self.config_path: str = config_path

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
        logger.info(f"刷新wr_skey: {new_skey}")
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

    @classmethod
    def from_config(cls, config_path: str):
        """从配置中创建实例"""
        config = cls.load_config(config_path)
        headers = config["headers"]
        cookies = config["cookies"]
        payload = config["payload"]
        return cls(headers, cookies, payload, config_path)

    @staticmethod
    def convert(curl_command: str):
        """提取bash接口中的headers与cookies
        支持 -H 'Cookie: xxx' 和 -b 'xxx' 两种方式的cookie提取
        """
        # 提取 headers
        headers_temp = {}
        for match in re.findall(r"-H '([^:]+): ([^']+)'", curl_command):
            headers_temp[match[0]] = match[1]

        # 提取 cookies
        cookies = {}

        # 从 -H 'Cookie: xxx' 提取
        cookie_header = next(
            (v for k, v in headers_temp.items() if k.lower() == "cookie"), ""
        )

        # 从 -b 'xxx' 提取
        cookie_b = re.search(r"-b '([^']+)'", curl_command)
        cookie_string = cookie_b.group(1) if cookie_b else cookie_header

        # 解析 cookie 字符串
        if cookie_string:
            for cookie in cookie_string.split("; "):
                if "=" in cookie:
                    key, value = cookie.split("=", 1)
                    cookies[key.strip()] = value.strip()

        # 移除 headers 中的 Cookie/cookie
        headers = {k: v for k, v in headers_temp.items() if k.lower() != "cookie"}

        return headers, cookies

    @classmethod
    def update_from_curl(cls, bash_path: str, config_path: str):
        """从curl中创建实例"""
        # curl.sh
        wx = cls.from_config(config_path)
        with open(bash_path, "r", encoding="utf-8") as f:
            curl_command = f.read()
        config = cls.convert(curl_command)
        wx.headers.update(config[0])
        wx.cookies.update(config[1])
        wx.save_config()

    @staticmethod
    def load_config(config_path: str) -> dict:
        """加载配置"""
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config

    def save_config(self):
        """保存配置"""
        if not self.config_path:  # 未传入config_path，不保存config文件。
            return
        self.payload.pop("s", None)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    @property
    def config(self):
        """转换为配置"""
        return {
            "headers": self.headers,
            "cookies": self.cookies,
            "payload": self.payload,
        }

    def run(
        self,
        loop_num: int = 5,
        residence_second: int = 60,  # 单位秒,
        onSuccess: Callable = None,
        onRefresh: Callable = None,
        onFail: Callable = None,
        onFinish: Callable = None,
    ):
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
            logger.info(f"⏱️ 尝试第 {index} 次阅读...")
            resData: dict = self.read()
            if "succ" in resData:
                index += 1
                time.sleep(residence_second)
                onSuccess(
                    f"✅ 阅读成功，阅读进度：{(index - 1) * (residence_second / 60)} 分钟"
                )
            else:
                logger.warning("❌ cookie 已过期，尝试刷新...")
                if self.refresh():
                    onRefresh("🔄 重新本次阅读。")
                    # 保存刷新后的config
                    self.save_config()
                    continue
                else:
                    msg = "❌ 无法获取新密钥或者WXREAD_CURL_BASH配置有误，终止运行。"
                    onFail(msg)
        onFinish("🎉 阅读脚本已完成！")
