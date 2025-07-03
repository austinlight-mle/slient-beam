# client_service.py

import win32serviceutil
import win32service
import win32event
import servicemanager
import time

from client_screenshot import capture_screenshots
from client_network import send_screenshot


class ScreenshotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ScreenshotCaptureService"
    _svc_display_name_ = "Screenshot Capture Background Service"
    _svc_description_ = "Continuously captures and sends screenshots in the background."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("ScreenshotService started")
        self.main()

    def main(self):
        host = "127.0.0.1:8081"
        interval = 4

        while self.running:
            try:
                shots = capture_screenshots(max_monitors=2)
                for mon, img_bytes in shots:
                    send_screenshot(host, mon, img_bytes)
            except Exception as e:
                servicemanager.LogErrorMsg(f"Error in screenshot loop: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(ScreenshotService)
