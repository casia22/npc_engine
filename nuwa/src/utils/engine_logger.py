import logging
import time
from pathlib import Path

class EngineLogger:
    def __init__(self, project_root_path=None):
        """放在项目入口，日志初始化
           设置项目整体logging的格式和处理器
        """
        self.PROJECT_ROOT_PATH = Path(project_root_path) if project_root_path else Path.cwd()

    def set_up(self):
        # 时间(兼容windows文件名)
        time_format = "%Y-%m-%d-%H-%M-%S"
        time_str = time.strftime(time_format, time.localtime())

        # 日志格式
        LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        # 文件处理器
        log_file_path = self.PROJECT_ROOT_PATH / "logs"
        log_file_path.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file_path / f'engine_{time_str}.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

        # 配置根logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    def get_logger(self, name):
        return logging.getLogger(name)
