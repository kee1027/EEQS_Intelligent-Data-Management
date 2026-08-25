# djangotutorial/data/apps.py
import os
import sys
import threading
from django.apps import AppConfig

class DataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "data"

    def ready(self):
        # 只有 runserver 的主工作进程才启动调度器，避免测试/管理命令触发。
        if os.environ.get("RUN_MAIN") != "true":
            return
        if len(sys.argv) < 2 or sys.argv[1] != "runserver":
            return

        from . import scheduler_setup

        print("[Timer] Preparing to trigger scheduler in 10 seconds...")
        threading.Timer(10, scheduler_setup.start).start()

    
