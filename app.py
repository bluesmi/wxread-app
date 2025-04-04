import asyncio
import os
import tkinter as tk
import tkinter.messagebox
from tkinter import ttk

from loguru import logger

from sdk import WXReadSDK

# 去除默认的日志处理器，避免重复打印日志到控制台的问题
logger.remove()

# 定义全局样式常量
FONT_FAMILY = "Microsoft YaHei Mono"
FONT_SIZE_NORMAL = 12
FONT_SIZE_LARGE = 14
TEXT_COLOR = "black"
BUTTON_BG_NORMAL = "#e0e0e0"
BUTTON_BG_ACTIVE = "#d0d0d0"
CONFIG_FILE = "curl_config.sh"

LEVEL_COLORS = {
    "DEBUG": "blue",
    "INFO": "green",
    "WARNING": "orange",
    "ERROR": "red",
    "CRITICAL": "purple",
}


def center_window_on_screen(window, width_ratio=0.5, height_ratio=0.5):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    width = int(screen_width * width_ratio)
    height = int(screen_height * height_ratio)
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def center_window_on_parent(parent, window, width_ratio=0.4, height_ratio=0.2):
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    width = int(parent_width * width_ratio)
    height = int(parent_height * height_ratio)
    x = parent_x + (parent_width - width) // 2
    y = parent_y + (parent_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


class ReadingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("微信读书")
        # 根据屏幕分辨率按比例设置窗口大小并居中
        center_window_on_screen(self)
        self.configure(bg="#f0f0f0")
        self.create_widgets()
        self.timer_id = None
        self.curl_cmd = self.load_curl_config()
        self.task = None
        # 创建新的事件循环并设置为当前事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # 监听窗口大小变化事件
        self.bind("<Configure>", self.on_window_resize)

    def load_curl_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf8") as file:
                content = file.read().strip()
            if content:  # 检查文件内容是否为空字符串或只包含空格和换行符
                return content
            else:  # 如果文件内容为空，返回默认值或None等，根据实际需求决定
                return None
        return None

    def log_to_text(self, message):
        TIME_COLOR = "gray"
        MESSAGE_COLOR = "black"
        TIME_WIDTH = 20
        LEVEL_WIDTH = 10
        level: str = message.record["level"].name
        # 格式化时间
        time_str: str = message.record["time"].strftime("%Y-%m-%d %H:%M:%S")
        # 格式化时间和级别，使其保持固定宽度
        formatted_time = f"{time_str.ljust(TIME_WIDTH - 1)}"
        formatted_level = f" | {level.ljust(LEVEL_WIDTH - 1)} | "

        # 临时将日志框设置为可编辑状态
        self.log_text.config(state=tk.NORMAL)

        # 插入时间部分
        self.log_text.insert(tk.END, formatted_time, "time")
        self.log_text.tag_config("time", foreground=TIME_COLOR)

        # 插入级别部分
        self.log_text.insert(tk.END, formatted_level, level)
        self.log_text.tag_config(level, foreground=LEVEL_COLORS[level])

        # 插入消息部分
        self.log_text.insert(tk.END, f"{message.record['message']}\n", "message")
        self.log_text.tag_config("message", foreground=MESSAGE_COLOR)

        self.log_text.see(tk.END)  # 滚动到最新的日志消息

        # 将日志框设置为不可编辑状态
        self.log_text.config(state=tk.DISABLED)

    def save_curl_config(self):
        with open(CONFIG_FILE, "w", encoding="utf8") as file:
            file.write(self.curl_cmd)

    def create_widgets(self):
        self.create_button_area()
        self.create_log_area()

    def create_button_area(self):
        # 创建样式
        style = ttk.Style()
        style.configure(
            "TButton",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            padding=10,
            background=BUTTON_BG_NORMAL,
            foreground=TEXT_COLOR,
        )
        style.map("TButton", background=[("active", BUTTON_BG_ACTIVE)])

        # 创建按钮框架
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=20, anchor="center")

        buttons = [
            ("开始", self.start_function),
            ("停止", self.stop_function),
            ("配置curl", self.config_function),
            ("清除日志", self.clear_log),  # 添加清除日志按钮
        ]
        for text, command in buttons:
            button = ttk.Button(button_frame, text=text, command=command)
            button.pack(side=tk.LEFT, padx=5)

    def create_log_area(self):
        # 创建日志区域
        log_label = ttk.Label(
            self,
            text="运行日志",
            font=(FONT_FAMILY, FONT_SIZE_LARGE),
            foreground=TEXT_COLOR,
        )
        log_label.pack(pady=10)

        log_frame = ttk.Frame(self)
        log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame,
            bg="white",
            fg=TEXT_COLOR,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bd=2,
            relief=tk.SOLID,
            state=tk.DISABLED,  # 初始设置为不可编辑状态
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        logger.add(self.log_to_text, format="{time} {level} {message}")

    def get_valid_run_time(self):
        dialog = tk.Toplevel(self)
        # 将弹窗置于应用窗口中间
        center_window_on_parent(self, dialog)
        dialog.title("输入运行时间")

        label = tk.Label(
            dialog,
            text="请输入运行时间（分钟）：",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
        )
        label.pack(pady=5)

        entry = tk.Entry(dialog, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        entry.pack(pady=5)

        # 自动将焦点设置到输入框
        entry.focus_set()

        result = None

        def submit():
            nonlocal result
            try:
                value = int(entry.get())
                if value < 0:
                    tkinter.messagebox.showerror("输入错误", "请输入一个有效的正整数。")
                else:
                    result = value
                    dialog.destroy()
            except ValueError:
                tkinter.messagebox.showerror("输入错误", "请输入一个有效的正整数。")

        # 绑定回车键到提交函数
        entry.bind("<Return>", lambda event: submit())

        button = tk.Button(
            dialog, text="提交", command=submit, font=(FONT_FAMILY, FONT_SIZE_NORMAL)
        )
        button.pack(pady=5)

        dialog.wait_window()
        return result

    async def start_function_async(self):
        if self.curl_cmd is None:
            tkinter.messagebox.showwarning("未配置 Curl 命令", "请先配置 Curl 命令。")
            self.config_function()
            return
        wx = WXReadSDK.from_curl_bash(CONFIG_FILE)
        run_time = self.get_valid_run_time()
        if run_time is None:
            return
        await wx.sync_run(
            loop_num=run_time * 2,
            onStart=logger.info,
            onSuccess=logger.debug,
            onRefresh=logger.info,
            onFail=logger.error,
            onFinish=logger.info,
        )

    def start_function(self):
        if self.task is None or self.task.done():
            self.task = self.loop.create_task(self.start_function_async())

    def stop_function(self):
        if self.task and not self.task.done():
            self.task.cancel()
            logger.info("任务已取消")

    def config_function(self):
        config_window = tk.Toplevel(self)
        # 将配置窗口置于应用窗口中间
        center_window_on_parent(self, config_window, width_ratio=0.7, height_ratio=0.7)
        config_window.title("配置设置")

        # 创建一个框架来包含标签和保存按钮
        label_button_frame = ttk.Frame(config_window)
        label_button_frame.pack(pady=5, padx=20, fill=tk.X)

        # 设置列权重，让第二列占据剩余空间
        label_button_frame.columnconfigure(1, weight=1)

        # curl 输入部分
        curl_label = ttk.Label(
            label_button_frame,
            text="Curl",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            foreground=TEXT_COLOR,
        )
        curl_label.grid(row=0, column=0, padx=5, sticky=tk.W)

        # 保存按钮
        def save_config():
            self.curl_cmd = curl_text.get("1.0", tk.END).strip()
            self.save_curl_config()
            config_window.destroy()

        save_button = ttk.Button(
            label_button_frame,
            text="保存",
            command=save_config,
            style="TButton",
        )
        save_button.grid(row=0, column=2, padx=(0, 20), sticky=tk.E)

        # 使用 tk.Text 组件并将窗口大小变为原来的2倍
        if self.curl_cmd:
            curl_text = tk.Text(
                config_window,
                width=160,
                height=10,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                fg=TEXT_COLOR,
            )
            curl_text.insert(tk.END, self.curl_cmd)
        else:
            curl_text = tk.Text(
                config_window,
                width=160,
                height=10,
                font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                fg=TEXT_COLOR,
            )
        curl_text.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

    def clear_log(self):
        # 清除日志文本框的内容
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def on_window_resize(self, event):
        # 这里可以添加窗口大小改变时的处理逻辑，例如调整组件大小
        pass

    def on_close(self):
        if self.task and not self.task.done():
            self.task.cancel()
        self.loop.stop()
        self.destroy()


if __name__ == "__main__":
    app = ReadingApp()

    def run_loop():
        app.loop.call_soon(app.loop.stop)
        app.loop.run_forever()
        app.after(100, run_loop)

    app.after(100, run_loop)
    app.mainloop()
