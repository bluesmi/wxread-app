# 微信读书自动阅读脚本

轻量级微信读书脚本，自动阅读刷时间

## 功能

### python

`python main.py`

1. 阅读支持多账户阅读，阅读书籍从 `config/curl_config.sh` 文件中读取。
2. 多账户阅读需要将所有 `curl` 信息以 `.sh` 保存到 `config` 文件夹中。

### 应用

`python app.py`

1. 保存curl
2. 阅读功能
3. 阅读中止
4. 显示过程日志
5. 清除日志
6. `build.ps1` 命令打包成 exe

## 使用

### python运行

1. 自行创建 `config` 文件夹，将curl信息复制到 `curl_config.sh` 中。
2. 使用 python 运行 `main.py`

### exe 运行

过程中会保存一个 `curl_config.sh` 文件，保存请求信息。

## 使用说明

点击开始按钮，按照提示操作即可

![alt text](images/README/image.png)

![alt text](images/README/image-1.png)

### curl 获取说明

打开想要阅读的书籍，然后按 `f12` 进入开发者模式，选择 `network` 选项，然后点击**下一章**，得到 `reed` 的请求，然后右键，复制 `curl （bash)`，粘贴到配置框中。

![alt text](images/README/PixPin_2025-04-04_19-15-51.gif)

## 致谢

- [findmover/wxread](https://github.com/findmover/wxread) 从这个项目得到的基础 api 设计
