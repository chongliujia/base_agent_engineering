#!/usr/bin/env python3
"""
Async utility functions - Unified event loop management to avoid conflicts
"""

import asyncio
import functools
import threading
from typing import Any, Callable, Coroutine, Optional
import sys
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor


class AsyncLoopManager:
    """Async event loop manager"""
    
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
        """Get or create event loop"""
        try:
            # Try to get current event loop
            loop = asyncio.get_running_loop()
            return loop
        except RuntimeError:
            # No running event loop, create a new one
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
        """Safely run async function"""
        try:
            # Check if already in event loop
            loop = asyncio.get_running_loop()
            # If already in event loop, use create_task
            if loop.is_running():
                # Create task and wait for completion
                task = loop.create_task(coro)
                return task
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No running event loop, use asyncio.run
            return asyncio.run(coro)
    
    def run_sync(self, coro: Coroutine) -> Any:
        """Synchronously run async function (blocking)"""
        try:
            # Check if already in event loop
            loop = asyncio.get_running_loop()
            # If already in event loop, cannot use run_until_complete
            raise RuntimeError("Cannot use run_sync inside an async context. Use await instead.")
        except RuntimeError as e:
            if "no running event loop" in str(e).lower():
                # No running event loop, safe to use asyncio.run
                return asyncio.run(coro)
            else:
                # Other runtime errors, re-raise
                raise
    
    async def run_in_isolated_thread(self, coro: Coroutine) -> Any:
        """Run async function in isolated thread to avoid event loop conflicts"""
        def run_in_new_loop():
            # Create new event loop
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        # Run in thread pool
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, run_in_new_loop)
    
    def run_sync_in_isolated_thread(self, coro: Coroutine) -> Any:
        """Synchronously run async function in isolated thread"""
        def run_in_new_loop():
            # Create new event loop
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        
        # Run in thread pool and wait for result
        future = self._executor.submit(run_in_new_loop)
        return future.result()


def safe_async_run(coro: Coroutine) -> Any:
    """Decorator function to safely run async functions"""
    manager = AsyncLoopManager()
    return manager.run_sync(coro)


def run_in_isolated_loop(coro: Coroutine) -> Any:
    """Run async function in isolated event loop (sync version)"""
    manager = AsyncLoopManager()
    return manager.run_sync_in_isolated_thread(coro)


async def run_in_isolated_loop_async(coro: Coroutine) -> Any:
    """Run async function in isolated event loop (async version)"""
    manager = AsyncLoopManager()
    return await manager.run_in_isolated_thread(coro)


def async_to_sync(func: Callable) -> Callable:
    """Decorator to convert async function to sync function"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        return safe_async_run(coro)
    return wrapper


def handle_async_context(func: Callable) -> Callable:
    """Decorator to handle async context, automatically choose appropriate execution method"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        
        try:
            # Check if in async context
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # In async context, return coroutine object for caller to await
                return coro
            else:
                # Not in async context, execute synchronously
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop, use asyncio.run
            return asyncio.run(coro)
    
    return wrapper


async def run_in_thread_pool(func: Callable, *args, **kwargs) -> Any:
    """Run sync function in thread pool"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


def is_async_context() -> bool:
    """Check if currently in async context"""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


class AsyncContextManager:
    """Async context manager to ensure proper event loop handling"""
    
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
            # Only close the loop if we created a new one
            if not self.loop.is_closed():
                self.loop.close()


# Global instance
loop_manager = AsyncLoopManager()