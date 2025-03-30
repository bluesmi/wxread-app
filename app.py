import os
import tkinter as tk
import tkinter.messagebox
from tkinter import simpledialog, ttk

from loguru import logger

from sdk import WXReadSDK

# 定义全局样式常量
FONT_FAMILY = "Courier New"
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


class ReadingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("微信读书")
        self.geometry("600x400")
        self.configure(bg="#f0f0f0")
        self.create_widgets()
        self.timer_id = None
        self.curl_cmd = self.load_curl_config()

    def load_curl_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as file:
                return file.read().strip()
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

    def save_curl_config(self):
        with open(CONFIG_FILE, "w") as file:
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
        ]
        for text, command in buttons:
            button = ttk.Button(button_frame, text=text, command=command)
            button.pack(side=tk.LEFT, padx=5)

    def create_log_area(self):
        # 创建日志区域
        log_label = ttk.Label(
            self,
            text="日志",
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
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        logger.add(self.log_to_text, format="{time} {level} {message}")

    def get_valid_run_time(self):
        while True:
            run_time = simpledialog.askstring(
                "输入运行时间", "请输入运行时间（分钟）："
            )
            if run_time is None:
                return None
            try:
                run_time = int(run_time)
                if run_time < 0:
                    raise ValueError
                return run_time
            except ValueError:
                tkinter.messagebox.showerror("输入错误", "请输入一个有效的正整数。")

    def start_function(self):
        if self.curl_cmd is None:
            tkinter.messagebox.showwarning("未配置 Curl 命令", "请先配置 Curl 命令。")
            self.config_function()
            return
        wx = WXReadSDK.from_curl_bash(CONFIG_FILE)
        run_time = self.get_valid_run_time()
        if run_time is None:
            return
        wx.run(
            loop_num=run_time,
            onStart=logger.info,
            onSuccess=logger.debug,
            onRefresh=logger.info,
            onFail=logger.error,
            onFinish=logger.info,
        )

    def stop_function(self):
        pass

    def config_function(self):
        config_window = tk.Toplevel(self)
        # 增大窗口大小
        config_window.geometry("600x400")
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


if __name__ == "__main__":
    app = ReadingApp()
    app.mainloop()
