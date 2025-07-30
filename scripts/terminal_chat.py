#!/usr/bin/env python3
"""
终端聊天程序 - 交互式RAG测试工具
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

# 抑制各种警告和日志
import warnings
warnings.filterwarnings('ignore')

os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYTHONWARNINGS'] = 'ignore'

# 抑制gRPC fork警告
import logging
logging.getLogger('grpc').setLevel(logging.ERROR)
logging.getLogger('google').setLevel(logging.ERROR)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.workflow import rag_workflow
from src.knowledge_base.knowledge_base_manager import get_knowledge_base_manager
from src.prompts.prompt_manager import get_prompt_manager
from config.settings import get_settings

# 颜色定义
class Colors:
    """终端颜色配置"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 明亮色
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # 背景色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


class StreamMarkdownProcessor:
    """简化的流式markdown处理器"""
    
    def __init__(self):
        self.buffer = ""
        
    def process_chunk(self, chunk: str) -> str:
        """处理文本块 - 简化版本，只在换行时处理格式"""
        import re
        
        self.buffer += chunk
        output = ""
        
        # 当遇到换行时，处理完整的行
        if '\n' in chunk:
            lines = self.buffer.split('\n')
            # 处理除最后一行外的所有完整行
            for line in lines[:-1]:
                formatted_line = self._simple_format(line)
                output += formatted_line + '\n'
            
            # 保留未完成的最后一行
            self.buffer = lines[-1]
        else:
            # 对于普通字符，直接输出
            output = chunk
        
        return output
    
    def _simple_format(self, line: str) -> str:
        """简单的行格式化"""
        import re
        
        # 移除markdown链接
        line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
        
        # 处理粗体（简化）
        line = re.sub(r'\*\*([^*]+)\*\*', f'{Colors.BOLD}\\1{Colors.RESET}', line)
        
        # 处理代码
        line = re.sub(r'`([^`]+)`', f'{Colors.CYAN}\\1{Colors.RESET}', line)
        
        # 处理标题
        stripped = line.strip()
        if stripped.startswith('###'):
            return f"{Colors.BRIGHT_BLUE}{stripped[3:].strip()}{Colors.RESET}"
        elif stripped.startswith('##'):
            return f"{Colors.BRIGHT_BLUE}{Colors.BOLD}{stripped[2:].strip()}{Colors.RESET}"
        elif stripped.startswith('#'):
            return f"{Colors.BRIGHT_BLUE}{Colors.BOLD}{stripped[1:].strip()}{Colors.RESET}"
        
        # 处理列表
        if re.match(r'^\d+\.', stripped):
            number = re.match(r'^(\d+)\.', stripped).group(1)
            content = re.sub(r'^\d+\.\s*', '', stripped)
            return f"  {number}. {content}"
        elif stripped.startswith('- ') or stripped.startswith('* '):
            content = stripped[2:]
            return f"  • {content}"
        
        return line
    
    def reset(self):
        """重置处理器状态"""
        self.buffer = ""


class TerminalChat:
    """终端聊天应用"""
    
    def __init__(self):
        self.settings = get_settings()
        self.kb_manager = get_knowledge_base_manager()
        self.prompt_manager = get_prompt_manager()
        self.chat_history = []
        self.session_start = datetime.now()
        
        # 流式输出处理器
        self.markdown_processor = StreamMarkdownProcessor()
        
        # 统计信息
        self.stats = {
            "total_queries": 0,
            "total_time": 0.0,
            "avg_response_time": 0.0,
            "modes_used": {
                "混合模式": 0,
                "知识库模式": 0,
                "网络模式": 0,
                "兜底模式": 0
            }
        }
    
    def format_for_terminal(self, text: str) -> str:
        """将markdown格式转换为适合终端显示的格式"""
        import re
        
        # 移除markdown链接，保留文字部分
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # 处理粗体标记
        text = re.sub(r'\*\*([^*]+)\*\*', f'{Colors.BOLD}\\1{Colors.RESET}', text)
        text = re.sub(r'__([^_]+)__', f'{Colors.BOLD}\\1{Colors.RESET}', text)
        
        # 处理斜体标记（简化为普通文本）
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # 处理代码块标记
        text = re.sub(r'`([^`]+)`', f'{Colors.CYAN}\\1{Colors.RESET}', text)
        
        # 处理标题标记
        text = re.sub(r'^### (.+)$', f'{Colors.BRIGHT_BLUE}\\1{Colors.RESET}', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', f'{Colors.BRIGHT_BLUE}{Colors.BOLD}\\1{Colors.RESET}', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', f'{Colors.BRIGHT_BLUE}{Colors.BOLD}\\1{Colors.RESET}', text, flags=re.MULTILINE)
        
        # 处理列表标记
        text = re.sub(r'^- (.+)$', f'  • \\1', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\. (.+)$', f'  \\1', text, flags=re.MULTILINE)
        
        return text
    
    def print_welcome(self):
        """打印欢迎信息"""
        print(f"{Colors.BRIGHT_CYAN}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_BLUE}{Colors.BOLD}🚀 智能RAG终端聊天助手 v2.0{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.CYAN}💡 特性：{Colors.RESET}")
        print(f"   • ⚡ 并行检索 (知识库 + 网络搜索)")  
        print(f"   • 🧠 智能模式自适应")
        print(f"   • 🔗 多源信息融合")
        print(f"   • 📊 实时性能监控")
        print()
        print(f"{Colors.YELLOW}📋 可用命令：{Colors.RESET}")
        print(f"   /help     - 显示帮助信息")
        print(f"   /stats    - 显示会话统计")
        print(f"   /kb       - 知识库管理")
        print(f"   /history  - 显示对话历史")
        print(f"   /clear    - 清空屏幕")
        print(f"   /exit     - 退出程序")
        print()
        
        # 显示当前配置
        print(f"{Colors.GREEN}🔧 当前配置：{Colors.RESET}")
        print(f"   知识库：{self.settings.current_collection_name}")
        print(f"   网络搜索：{'✅ 已启用' if self.settings.tavily_api_key else '❌ 未配置'}")
        print(f"   会话开始：{self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BRIGHT_CYAN}{'-' * 60}{Colors.RESET}")
        print()
    
    def print_help(self):
        """打印帮助信息"""
        print(f"\n{Colors.BRIGHT_BLUE}📖 RAG终端聊天助手帮助{Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * 40}{Colors.RESET}")
        
        print(f"\n{Colors.YELLOW}💬 基本使用：{Colors.RESET}")
        print(f"   直接输入问题，系统会自动进行并行检索并回答")
        print(f"   例如：Python的异步编程有什么优势？")
        
        print(f"\n{Colors.YELLOW}🎯 工作原理：{Colors.RESET}")
        print(f"   1. 📝 查询分析 - 理解您的问题")
        print(f"   2. ⚡ 并行检索 - 同时搜索知识库和网络")
        print(f"   3. 🔗 信息融合 - 整合多源信息")
        print(f"   4. 🤖 智能回答 - 生成综合回答")
        
        print(f"\n{Colors.YELLOW}📊 系统命令：{Colors.RESET}")
        
        commands = [
            ("/help", "显示此帮助信息"),
            ("/stats", "显示会话统计信息"),
            ("/history", "显示对话历史记录"),
            ("/kb list", "列出所有知识库"),
            ("/kb switch <name>", "切换到指定知识库"),
            ("/kb info", "显示当前知识库信息"),
            ("/clear", "清空终端屏幕"),
            ("/exit", "退出聊天程序")
        ]
        
        for cmd, desc in commands:
            print(f"   {Colors.BRIGHT_GREEN}{cmd:<20}{Colors.RESET} - {desc}")
        
        print(f"\n{Colors.YELLOW}🎨 显示说明：{Colors.RESET}")
        print(f"   {Colors.BRIGHT_BLUE}蓝色{Colors.RESET} - 系统信息")
        print(f"   {Colors.BRIGHT_GREEN}绿色{Colors.RESET} - 成功状态")
        print(f"   {Colors.BRIGHT_YELLOW}黄色{Colors.RESET} - 警告信息")
        print(f"   {Colors.BRIGHT_RED}红色{Colors.RESET} - 错误信息")
        print(f"   {Colors.CYAN}青色{Colors.RESET} - 统计数据")
        print()
    
    def print_stats(self):
        """打印统计信息"""
        print(f"\n{Colors.BRIGHT_BLUE}📊 会话统计信息{Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * 40}{Colors.RESET}")
        
        session_duration = datetime.now() - self.session_start
        duration_str = str(session_duration).split('.')[0]  # 去掉微秒
        
        print(f"🕒 会话时长：{duration_str}")
        print(f"💬 查询总数：{self.stats['total_queries']}")
        
        if self.stats['total_queries'] > 0:
            print(f"⚡ 平均响应：{self.stats['avg_response_time']:.2f}秒")
            print(f"⏱️  总处理时间：{self.stats['total_time']:.2f}秒")
            
            print(f"\n{Colors.YELLOW}🎯 模式使用统计：{Colors.RESET}")
            for mode, count in self.stats['modes_used'].items():
                if count > 0:
                    percentage = (count / self.stats['total_queries']) * 100
                    print(f"   {mode}: {count}次 ({percentage:.1f}%)")
        else:
            print(f"   {Colors.DIM}暂无查询记录{Colors.RESET}")
        print()
    
    def print_history(self, limit: int = 5):
        """打印对话历史"""
        print(f"\n{Colors.BRIGHT_BLUE}📜 对话历史 (最近{min(limit, len(self.chat_history))}条){Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * 50}{Colors.RESET}")
        
        if not self.chat_history:
            print(f"   {Colors.DIM}暂无对话记录{Colors.RESET}")
            return
        
        for i, record in enumerate(self.chat_history[-limit:], 1):
            timestamp = record['timestamp'].strftime('%H:%M:%S')
            query = record['query'][:50] + ('...' if len(record['query']) > 50 else '')
            mode = record.get('mode', '未知')
            response_time = record.get('response_time', 0)
            
            print(f"{Colors.GREEN}{i:2d}.{Colors.RESET} [{timestamp}] {Colors.CYAN}{mode}{Colors.RESET}")
            print(f"     Q: {query}")
            print(f"     T: {response_time:.2f}s")
            print()
    
    async def handle_kb_command(self, args: list):
        """处理知识库命令"""
        if not args:
            print(f"{Colors.YELLOW}💡 使用方法：/kb <list|switch|info>{Colors.RESET}")
            return
        
        cmd = args[0].lower()
        
        if cmd == "list":
            print(f"\n{Colors.BRIGHT_BLUE}📚 可用知识库：{Colors.RESET}")
            try:
                kbs = self.kb_manager.list_knowledge_bases()
                current = self.settings.current_collection_name
                
                for kb in kbs:
                    marker = "✅" if kb == current else "  "
                    print(f"   {marker} {kb}")
                    
                if not kbs:
                    print(f"   {Colors.DIM}暂无知识库{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}❌ 获取知识库列表失败: {e}{Colors.RESET}")
        
        elif cmd == "switch":
            if len(args) < 2:
                print(f"{Colors.YELLOW}💡 使用方法：/kb switch <知识库名称>{Colors.RESET}")
                return
            
            kb_name = args[1]
            try:
                kbs = self.kb_manager.list_knowledge_bases()
                if kb_name in kbs:
                    self.settings.current_collection_name = kb_name
                    print(f"{Colors.GREEN}✅ 已切换到知识库：{kb_name}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}❌ 知识库 '{kb_name}' 不存在{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}❌ 切换知识库失败: {e}{Colors.RESET}")
        
        elif cmd == "info":
            print(f"\n{Colors.BRIGHT_BLUE}ℹ️  当前知识库信息：{Colors.RESET}")
            current = self.settings.current_collection_name
            print(f"   名称: {current}")
            
            try:
                stats = self.kb_manager.get_knowledge_base_stats(current)
                print(f"   文档数: {stats.get('total_documents', 'N/A')}")
                print(f"   更新时间: {stats.get('last_updated', 'N/A')}")
            except Exception as e:
                print(f"   {Colors.YELLOW}⚠️ 无法获取详细信息: {e}{Colors.RESET}")
        
        else:
            print(f"{Colors.RED}❌ 未知的知识库命令: {cmd}{Colors.RESET}")
        
        print()
    
    async def stream_chunk_handler(self, chunk: str):
        """处理流式输出的文本块"""
        # 直接输出文本，现在AI会输出纯文本格式
        print(chunk, end='', flush=True)
    
    def reset_stream_processor(self):
        """重置流式处理器状态"""
        self.markdown_processor.reset()
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """处理用户查询"""
        print(f"{Colors.BRIGHT_BLUE}🔄 正在处理查询...{Colors.RESET}")
        
        # 重置流式处理器状态
        self.reset_stream_processor()
        
        start_time = time.time()
        
        try:
            # 显示回答开始标记
            print(f"\n{Colors.BRIGHT_GREEN}🤖 AI助手回答{Colors.RESET}")
            print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
            print()
            
            # 执行RAG工作流 - 使用流式输出
            result = await rag_workflow.run(query, stream_callback=self.stream_chunk_handler)
            
            # 输出换行，表示回答结束
            print("\n")
            
            processing_time = time.time() - start_time
            
            # 更新统计信息
            self.stats['total_queries'] += 1
            self.stats['total_time'] += processing_time
            self.stats['avg_response_time'] = self.stats['total_time'] / self.stats['total_queries']
            
            # 兼容处理：检查result是否为RAGState对象或字典
            if hasattr(result, 'metadata'):
                # RAGState对象
                response = result.response
                metadata = result.metadata
            else:
                # 字典格式
                response = result.get('response', str(result))
                metadata = result.get('metadata', {})
            
            # 统计模式使用
            mode = metadata.get('retrieval_mode', '未知模式')
            if mode in self.stats['modes_used']:
                self.stats['modes_used'][mode] += 1
            
            # 记录对话历史
            self.chat_history.append({
                'timestamp': datetime.now(),
                'query': query,
                'response': response,
                'mode': mode,
                'response_time': processing_time,
                'metadata': metadata
            })
            
            return {
                'response': response,  
                'metadata': metadata,
                'processing_time': processing_time
            }
            
        except KeyboardInterrupt:
            processing_time = time.time() - start_time
            error_msg = "用户中断了回答生成"
            print(f"\n{Colors.YELLOW}⚠️ {error_msg}{Colors.RESET}")
            
            self.chat_history.append({
                'timestamp': datetime.now(),
                'query': query,
                'response': error_msg,
                'mode': '中断',
                'response_time': processing_time,
                'metadata': {'interrupted': True}
            })
            
            return {
                'response': error_msg,
                'metadata': {'interrupted': True},
                'processing_time': processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"处理查询时发生错误: {str(e)}"
            print(f"\n{Colors.RED}❌ {error_msg}{Colors.RESET}")
            
            self.chat_history.append({
                'timestamp': datetime.now(),
                'query': query,
                'response': error_msg,
                'mode': '错误',
                'response_time': processing_time,
                'metadata': {'error': str(e)}
            })
            
            return {
                'response': error_msg,
                'metadata': {'error': str(e)},
                'processing_time': processing_time
            }
    
    def display_response(self, result: Dict[str, Any]):
        """显示回答结果的元数据信息（回答内容已通过流式输出显示）"""
        metadata = result['metadata']
        processing_time = result['processing_time']
        
        # 如果是错误或中断，不显示详细信息
        if 'error' in metadata or 'interrupted' in metadata:
            return
        
        # 处理信息区域 - 更紧凑的显示
        print(f"{Colors.DIM}📊 处理信息{Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * 30}{Colors.RESET}")
        
        # 创建信息行
        info_parts = []
        info_parts.append(f"⚡ {processing_time:.2f}s")
        
        if 'retrieval_mode' in metadata:
            mode = metadata['retrieval_mode']
            mode_emoji = {
                "混合模式": "🔗",
                "知识库模式": "📚", 
                "网络模式": "🌐",
                "无结果": "❌"
            }.get(mode, "🎯")
            info_parts.append(f"{mode_emoji} {mode}")
        
        # 结果统计
        results_info = []
        if 'knowledge_retrieved' in metadata:
            kb_count = metadata['knowledge_retrieved']
            if kb_count > 0:
                results_info.append(f"📚{kb_count}")
        
        if 'web_retrieved' in metadata:
            web_count = metadata['web_retrieved']
            if web_count > 0:
                results_info.append(f"🌐{web_count}")
        
        if results_info:
            info_parts.append(" + ".join(results_info))
        
        if 'parallel_retrieval_time' in metadata:
            parallel_time = metadata['parallel_retrieval_time']
            info_parts.append(f"🔄 {parallel_time:.2f}s")
        
        # 单行显示所有信息
        print(f"   {' | '.join(info_parts)}")
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print()
    
    async def run(self):
        """运行主循环"""
        try:
            self.print_welcome()
            
            while True:
                try:
                    # 获取用户输入
                    user_input = input(f"{Colors.BRIGHT_YELLOW}➤ {Colors.RESET}").strip()
                    
                    # 处理空输入
                    if not user_input:
                        continue
                    
                    # 处理系统命令
                    if user_input.startswith('/'):
                        cmd_parts = user_input[1:].split()
                        if not cmd_parts:
                            continue
                        
                        cmd = cmd_parts[0].lower()
                        args = cmd_parts[1:]
                        
                        if cmd == 'help':
                            self.print_help()
                        elif cmd == 'stats':
                            self.print_stats()
                        elif cmd == 'history':
                            self.print_history()
                        elif cmd == 'kb':
                            await self.handle_kb_command(args)
                        elif cmd == 'clear':
                            os.system('clear' if os.name == 'posix' else 'cls')
                            self.print_welcome()
                        elif cmd == 'exit':
                            print(f"{Colors.BRIGHT_BLUE}👋 感谢使用RAG终端聊天助手！{Colors.RESET}")
                            break
                        else:
                            print(f"{Colors.RED}❌ 未知命令: {user_input}{Colors.RESET}")
                            print(f"{Colors.YELLOW}💡 输入 /help 查看可用命令{Colors.RESET}")
                        
                        continue
                    
                    # 处理正常查询
                    result = await self.process_query(user_input)
                    self.display_response(result)
                
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}⚠️ 检测到中断信号{Colors.RESET}")
                    confirm = input(f"{Colors.YELLOW}确定要退出吗？(y/N): {Colors.RESET}").strip().lower()
                    if confirm in ['y', 'yes']:
                        break
                    else:
                        print(f"{Colors.GREEN}继续对话...{Colors.RESET}\n")
                        continue
                
                except Exception as e:
                    print(f"{Colors.RED}❌ 程序错误: {e}{Colors.RESET}")
                    print(f"{Colors.YELLOW}💡 程序将继续运行，您可以继续提问{Colors.RESET}\n")
        
        except Exception as e:
            print(f"{Colors.RED}❌ 程序启动失败: {e}{Colors.RESET}")
            return
        
        finally:
            # 显示会话总结
            print(f"\n{Colors.BRIGHT_BLUE}📊 会话总结：{Colors.RESET}")
            session_duration = datetime.now() - self.session_start
            print(f"   会话时长: {str(session_duration).split('.')[0]}")
            print(f"   总查询数: {self.stats['total_queries']}")
            if self.stats['total_queries'] > 0:
                print(f"   平均响应时间: {self.stats['avg_response_time']:.2f}秒")
            print(f"{Colors.BRIGHT_CYAN}再见！{Colors.RESET}")


async def main():
    """主函数"""
    chat = TerminalChat()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}程序被用户中断{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}程序运行错误: {e}{Colors.RESET}")
        sys.exit(1)