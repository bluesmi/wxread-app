from sdk import WXReadSDK

# 注意添加louguru包
# 设置corn表达式，3:00 每分钟一次。
# 0 * 3 * * *


def handler(event, context):
    CURL_PATH = "./code/curl_config.sh"

    wx = WXReadSDK.from_curl_bash(CURL_PATH)

    # 修改为异步运行
    wx.run_once()
