# 微信读书自动阅读脚本

轻量级微信读书脚本，自动阅读刷时间

## python运行

1. 使用 `uv` 管理项目
2. 运行 `main.py` 即可

## exe 运行

默认是**三体**这本书，如需换书自行阅读 `curl 获取说明` 部分。

过程中会保存一个 `curl_config.sh` 文件，保存请求信息。

## 使用说明

点击开始按钮，按照提示操作即可

![alt text](images/README/image.png)

![alt text](images/README/image-1.png)

## curl 获取说明

打开想要阅读的书籍，然后按 `f12` 进入开发者模式，选择 `network` 选项，然后点击**下一章**，得到 `reed` 的请求，然后右键，复制 `curl （bash)`，粘贴到配置框中。

![alt text](images/README/PixPin_2025-04-04_19-15-51.gif)

## 致谢

- [findmover/wxread](https://github.com/findmover/wxread) 从这个项目得到的基础 api 设计
