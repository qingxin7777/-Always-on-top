# Always-On-Top

Windows 窗口置顶小工具。激活任意窗口，按快捷键即可将其固定在最前面；支持同时置顶多个窗口；再次按下快捷键取消置顶。常驻系统托盘，支持开机自启。

## 功能

- **一键置顶**：激活窗口 → 按 `Ctrl+Alt+T` → 窗口置顶；再按一次取消
- **多窗口**：可同时置顶多个窗口，互不影响
- **自定义快捷键**：右键托盘 → 设置 → 录制任意组合键
- **开机自启**：设置中勾选即可，写入注册表 Run 键
- **插件预留**：`plugins/` 下放 `.py` 文件自动加载，方便以后加新功能

## 安装 & 运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 双击项目目录下的 Always-On-Top.lnk 启动
#    或运行：
pythonw main.py
```

> `pythonw` 启动无控制台黑窗。如需创建快捷方式：
> ```bash
> python -c "from win32com.client import Dispatch; s=Dispatch('WScript.Shell').CreateShortcut('Always-On-Top.lnk'); s.TargetPath='...pythonw.exe'; s.Arguments='main.py'; s.WorkingDirectory='.'; s.Save()"
> ```

## 依赖

- Python 3.12+
- pynput — 全局快捷键
- pystray — 系统托盘
- Pillow — 托盘图标
- pywin32 — 窗口操作

## 目录结构

```
Always-on-top/
├── main.py              # 入口
├── app.py               # 主调度
├── tray_icon.py         # 系统托盘
├── hotkey_listener.py   # 快捷键管理
├── window_manager.py    # 窗口置顶
├── settings_app.py      # 设置面板（独立进程）
├── config.py            # 配置读写
├── plugin_system.py     # 插件加载
├── plugins/             # 插件目录
└── requirements.txt
```

## 自定义插件

在 `plugins/` 下新建 `.py` 文件：

```python
PLUGIN_NAME = "你的功能"
PLUGIN_HOTKEY = "ctrl+shift+x"  # 可选

def callback():
    # 按快捷键时执行
    pass
```

重启后自动生效，可在设置面板中修改快捷键。
