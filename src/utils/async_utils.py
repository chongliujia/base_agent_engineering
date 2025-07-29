#!/usr/bin/env python3
"""
异步工具函数 - 统一管理事件循环，避免冲突
"""

import asyncio
import functools
import threading
from typing import Any, Callable, Coroutine, Optional
import sys
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor


class AsyncLoopManager:
    """异步事件循环管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._loop = None
            self._thread = None
            self._executor = ThreadPoolExecutor(max_workers=4)
            self._initialized = True
    
    def get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """获取或创建事件循环"""
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_running_loop()
            return loop
        except RuntimeError:
            # 没有运行中的事件循环，创建新的
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                return loop
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop
    
    def run_async(self, coro: Coroutine) -> Any:
        """安全地运行异步函数"""
        try:
            # 检查是否已经在事件循环中
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，使用 create_task
            if loop.is_running():
                # 创建任务并等待完成
                task = loop.create_task(coro)
                return task
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # 没有运行中的事件循环，使用 asyncio.run
            return asyncio.run(coro)
    
    def run_sync(self, coro: Coroutine) -> Any:
        """同步运行异步函数（阻塞）"""
        try:
            # 检查是否已经在事件循环中
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，不能使用 run_until_complete
            raise RuntimeError("Cannot use run_sync inside an async context. Use await instead.")
        except RuntimeError as e:
            if "no running event loop" in str(e).lower():
                # 没有运行中的事件循环，可以安全使用 asyncio.run
                return asyncio.run(coro)
            else:
                # 其他运行时错误，重新抛出
                raise
    
    async def run_in_isolated_thread(self, coro: Coroutine) -> Any:
        """在隔离的线程中运行异步函数，避免事件循环冲突"""
        def run_in_new_loop():
            # 创建新的事件循环
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        # 在线程池中运行
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, run_in_new_loop)
    
    def run_sync_in_isolated_thread(self, coro: Coroutine) -> Any:
        """在隔离的线程中同步运行异步函数"""
        def run_in_new_loop():
            # 创建新的事件循环
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        # 在线程池中运行并等待结果
        future = self._executor.submit(run_in_new_loop)
        return future.result()


def safe_async_run(coro: Coroutine) -> Any:
    """安全运行异步函数的装饰器函数"""
    manager = AsyncLoopManager()
    return manager.run_sync(coro)


def run_in_isolated_loop(coro: Coroutine) -> Any:
    """在隔离的事件循环中运行异步函数（同步版本）"""
    manager = AsyncLoopManager()
    return manager.run_sync_in_isolated_thread(coro)


async def run_in_isolated_loop_async(coro: Coroutine) -> Any:
    """在隔离的事件循环中运行异步函数（异步版本）"""
    manager = AsyncLoopManager()
    return await manager.run_in_isolated_thread(coro)


def async_to_sync(func: Callable) -> Callable:
    """将异步函数转换为同步函数的装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        return safe_async_run(coro)
    return wrapper


def handle_async_context(func: Callable) -> Callable:
    """处理异步上下文的装饰器，自动选择合适的执行方式"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        
        try:
            # 检查是否在异步上下文中
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # 在异步上下文中，返回协程对象让调用者 await
                return coro
            else:
                # 不在异步上下文中，同步执行
                return loop.run_until_complete(coro)
        except RuntimeError:
            # 没有事件循环，使用 asyncio.run
            return asyncio.run(coro)
    
    return wrapper


async def run_in_thread_pool(func: Callable, *args, **kwargs) -> Any:
    """在线程池中运行同步函数"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


def is_async_context() -> bool:
    """检查当前是否在异步上下文中"""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


class AsyncContextManager:
    """异步上下文管理器，确保正确的事件循环处理"""
    
    def __init__(self):
        self.loop = None
        self.was_running = False
    
    async def __aenter__(self):
        try:
            self.loop = asyncio.get_running_loop()
            self.was_running = True
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.was_running = False
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.was_running and self.loop:
            # 只有当我们创建了新循环时才关闭它
            if not self.loop.is_closed():
                self.loop.close()


# 全局实例
loop_manager = AsyncLoopManager()