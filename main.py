import asyncio  # 添加 asyncio 导入
import configparser
import datetime
from pathlib import Path

from loguru import logger

from sdk import WxPusherNotifier, WXReadSDK


async def process_curl_path(curl_path, read_num):
    FILE_NAME = Path(curl_path).stem
    pusher = WxPusherNotifier(WXPUSHER_SPT)

    def onStart(msg):
        logger.info(f"{FILE_NAME}---{msg}")

    def onSuccess(msg):
        logger.info(f"{FILE_NAME}---{msg}")

    def onRefresh(msg):
        logger.info(f"{FILE_NAME}---{msg}")

    def onFail(msg):
        logger.error(f"{FILE_NAME}---{msg}")

    def onFinish(msg):
        logger.info(f"{FILE_NAME}---{msg}")
        pusher.push(f"🎉 {FILE_NAME} 阅读脚本已完成！")

    wx = WXReadSDK.from_curl_bash(curl_path)
    await wx.sync_run(
        loop_num=read_num * 2,
        onStart=onStart,
        onSuccess=onSuccess,
        onRefresh=onRefresh,
        onFail=onFail,
        onFinish=onFinish,
    )


def setup_logger():
    today = datetime.date.today()
    log_file = f"logs/{today}.log"
    logger.add(log_file, rotation="1 day", retention="7 days", encoding="utf-8")


async def main():
    tasks = (process_curl_path(curl_path, READ_NUM) for curl_path in CURL_PATH_LIST)
    # 修改为异步运行
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    # config 文件夹下所有.sh
    CURL_PATH_LIST = Path("./config").glob("*.sh")
    CONFIG_PATH = "./config/key.ini"
    READ_NUM = 60

    setup_logger()

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    WXPUSHER_SPT = config.get("WXPUSHER", "SPT")

    asyncio.run(main())
