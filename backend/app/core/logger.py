import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from app.core.database import SessionLocal
from app.models.system_log import SystemLog

# 确保日志目录存在
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 创建日志记录器
logger = logging.getLogger("blueprint")
logger.setLevel(logging.INFO)

# 日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 轮转文件处理器（每个文件 10MB，保留 5 个文件）
file_handler = RotatingFileHandler(
    f'{LOG_DIR}/app.log',
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_operation(user_id: str, action: str, resource_type: str, resource_id: str = None, description: str = None, ip_address: str = None):
    """记录操作日志（同时写入文件和数据库）"""
    # 记录到日志文件
    logger.info(
        f"OPERATION - user_id={user_id}, action={action}, resource_type={resource_type}, "
        f"resource_id={resource_id}, description={description}, ip={ip_address}"
    )

    # 写入数据库
    try:
        db = SessionLocal()
        log_entry = SystemLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"写入系统日志到数据库失败：{e}")
