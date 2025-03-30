import configparser

from loguru import logger

from sdk import WxPusherNotifier, WXReadSDK

if __name__ == "__main__":
    CONFIG_PATH = "./config.json"
    # curl_path = "./curl.sh"
    # if curl_path:
    #     WXReadSDK.update_from_curl(curl_path, CONFIG_PATH)
    # wx.cookies_to_csv("./cookies.csv")
    READ_NUM = 30
    RESIDENCE_TIME = 60  # 单位秒

    config = configparser.ConfigParser()
    config.read("config.ini")
    WXPUSHER_SPT = config.get("WXPUSHER", "SPT")

    pusher = WxPusherNotifier(WXPUSHER_SPT)
    wx = WXReadSDK.from_config(CONFIG_PATH)

    def onFail(msg):
        logger.error(msg)
        raise Exception(msg)

    def onFinish(msg):
        logger.info(msg)
        pusher.push(msg)

    wx.run(
        loop_num=READ_NUM,
        residence_second=RESIDENCE_TIME,
        onFail=onFail,
        onFinish=onFinish,
    )
