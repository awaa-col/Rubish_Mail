"""
日志轮转模块

功能:
    - 定时清理旧日志文件
    - 限制日志文件大小
    - 保留最近N天的日志

输入: 日志目录路径、保留天数、最大文件大小
输出: 清理后的日志目录
"""
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import os


logger = logging.getLogger(__name__)


class LogRotation:
    """日志轮转管理器"""
    
    def __init__(
        self,
        log_dir: str = "logs",
        keep_days: int = 7,
        max_size_mb: int = 100,
        check_interval: int = 3600
    ):
        """
        初始化日志轮转管理器
        
        输入:
            log_dir: 日志目录
            keep_days: 保留最近几天的日志
            max_size_mb: 单个日志文件最大大小(MB)
            check_interval: 检查间隔(秒),默认1小时
        """
        self.log_dir = Path(log_dir)
        self.keep_days = keep_days
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.check_interval = check_interval
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    def start(self):
        """启动日志轮转任务"""
        if self._running:
            logger.warning("日志轮转任务已在运行")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._rotation_loop())
        logger.info(
            f"✓ 启动日志轮转: 保留{self.keep_days}天, "
            f"最大{self.max_size_bytes / 1024 / 1024}MB, "
            f"检查间隔{self.check_interval}秒"
        )
    
    def stop(self):
        """停止日志轮转任务"""
        if self._task:
            self._running = False
            self._task.cancel()
            logger.info("✓ 停止日志轮转")
    
    async def _rotation_loop(self):
        """日志轮转循环"""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                await self.rotate()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"日志轮转出错: {e}", exc_info=True)
    
    async def rotate(self):
        """
        执行日志轮转
        
        - 删除超过保留天数的日志
        - 分割超过大小限制的日志
        """
        try:
            if not self.log_dir.exists():
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.keep_days)
            deleted_count = 0
            rotated_count = 0
            
            # 遍历日志文件
            for log_file in self.log_dir.glob("*.log*"):
                # 检查文件修改时间
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                # 删除过期日志
                if mtime < cutoff_date:
                    try:
                        log_file.unlink()
                        deleted_count += 1
                        logger.info(f"🗑️ 删除过期日志: {log_file.name}")
                    except Exception as e:
                        logger.error(f"删除日志失败 {log_file}: {e}")
                    continue
                
                # 检查文件大小(仅对.log文件,不包括.log.1等已轮转的)
                if log_file.suffix == ".log":
                    file_size = log_file.stat().st_size
                    
                    if file_size > self.max_size_bytes:
                        # 轮转日志
                        try:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            new_name = f"{log_file.stem}.{timestamp}.log"
                            new_path = log_file.parent / new_name
                            
                            log_file.rename(new_path)
                            rotated_count += 1
                            logger.info(
                                f"🔄 轮转日志: {log_file.name} -> {new_name} "
                                f"({file_size / 1024 / 1024:.2f}MB)"
                            )
                        except Exception as e:
                            logger.error(f"轮转日志失败 {log_file}: {e}")
            
            if deleted_count > 0 or rotated_count > 0:
                logger.info(
                    f"✓ 日志轮转完成: 删除{deleted_count}个, 轮转{rotated_count}个"
                )
        
        except Exception as e:
            logger.error(f"日志轮转失败: {e}", exc_info=True)


# 全局日志轮转实例
_log_rotation: Optional[LogRotation] = None


def get_log_rotation() -> LogRotation:
    """
    获取全局日志轮转实例
    
    输出:
        LogRotation实例
    """
    global _log_rotation
    if _log_rotation is None:
        _log_rotation = LogRotation()
    return _log_rotation

