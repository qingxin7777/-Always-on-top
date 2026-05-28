import win32gui
import win32con


class WindowManager:

    EXCLUDED_CLASSES = ("Progman", "WorkerW", "Shell_TrayWnd", "Button")

    @staticmethod
    def get_active_window_handle():
        return win32gui.GetForegroundWindow()

    @staticmethod
    def is_valid_window(hwnd):
        if not hwnd:
            return False
        if not win32gui.IsWindow(hwnd):
            return False
        if not win32gui.IsWindowVisible(hwnd):
            return False
        class_name = win32gui.GetClassName(hwnd)
        if class_name in WindowManager.EXCLUDED_CLASSES:
            return False
        return True

    @staticmethod
    def is_always_on_top(hwnd):
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        return bool(ex_style & win32con.WS_EX_TOPMOST)

    @staticmethod
    def toggle_always_on_top(hwnd):
        currently = WindowManager.is_always_on_top(hwnd)
        WindowManager.set_always_on_top(hwnd, not currently)
        return not currently

    @staticmethod
    def set_always_on_top(hwnd, enable):
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if enable:
            new_style = ex_style | win32con.WS_EX_TOPMOST
            insert_after = win32con.HWND_TOPMOST
        else:
            new_style = ex_style & ~win32con.WS_EX_TOPMOST
            insert_after = win32con.HWND_NOTOPMOST

        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)
        win32gui.SetWindowPos(
            hwnd, insert_after,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
        )

    @staticmethod
    def get_window_title(hwnd):
        return win32gui.GetWindowText(hwnd)
