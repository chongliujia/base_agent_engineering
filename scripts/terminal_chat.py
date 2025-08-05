#!/usr/bin/env python3
"""
Terminal Chat Program - Interactive RAG Testing Tool
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Suppress various warnings and logs
import warnings
warnings.filterwarnings('ignore')

os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYTHONWARNINGS'] = 'ignore'

# Suppress gRPC fork warnings
import logging
logging.getLogger('grpc').setLevel(logging.ERROR)
logging.getLogger('google').setLevel(logging.ERROR)

# Add project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.workflow import rag_workflow
from src.knowledge_base.knowledge_base_manager import get_knowledge_base_manager
from src.prompts.prompt_manager import get_prompt_manager
from config.settings import get_settings

# Color definitions
class Colors:
    """Terminal color configuration"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


class StreamMarkdownProcessor:
    """Simplified streaming markdown processor"""
    
    def __init__(self):
        self.buffer = ""
        
    def process_chunk(self, chunk: str) -> str:
        """Process text chunk - simplified version, only processes format on newlines"""
        import re
        
        self.buffer += chunk
        output = ""
        
        # When encountering newlines, process complete lines
        if '\n' in chunk:
            lines = self.buffer.split('\n')
            # Process all complete lines except the last one
            for line in lines[:-1]:
                formatted_line = self._simple_format(line)
                output += formatted_line + '\n'
            
            # Keep the incomplete last line
            self.buffer = lines[-1]
        else:
            # For regular characters, output directly
            output = chunk
        
        return output
    
    def _simple_format(self, line: str) -> str:
        """Simple line formatting"""
        import re
        
        # Remove markdown links
        line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
        
        # Handle bold (simplified)
        line = re.sub(r'\*\*([^*]+)\*\*', f'{Colors.BOLD}\\1{Colors.RESET}', line)
        
        # Handle code
        line = re.sub(r'`([^`]+)`', f'{Colors.CYAN}\\1{Colors.RESET}', line)
        
        # Handle headers
        stripped = line.strip()
        if stripped.startswith('###'):
            return f"{Colors.BRIGHT_BLUE}{stripped[3:].strip()}{Colors.RESET}"
        elif stripped.startswith('##'):
            return f"{Colors.BRIGHT_BLUE}{Colors.BOLD}{stripped[2:].strip()}{Colors.RESET}"
        elif stripped.startswith('#'):
            return f"{Colors.BRIGHT_BLUE}{Colors.BOLD}{stripped[1:].strip()}{Colors.RESET}"
        
        # Handle lists
        if re.match(r'^\d+\.', stripped):
            number = re.match(r'^(\d+)\.', stripped).group(1)
            content = re.sub(r'^\d+\.\s*', '', stripped)
            return f"  {number}. {content}"
        elif stripped.startswith('- ') or stripped.startswith('* '):
            content = stripped[2:]
            return f"  • {content}"
        
        return line
    
    def reset(self):
        """Reset processor state"""
        self.buffer = ""


class TerminalChat:
    """Terminal chat application"""
    
    def __init__(self):
        self.settings = get_settings()
        self.kb_manager = get_knowledge_base_manager()
        self.prompt_manager = get_prompt_manager()
        self.chat_history = []
        self.session_start = datetime.now()
        
        # Streaming output processor
        self.markdown_processor = StreamMarkdownProcessor()
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "total_time": 0.0,
            "avg_response_time": 0.0,
            "modes_used": {
                "Hybrid Mode": 0,
                "Knowledge Base Mode": 0,
                "Web Mode": 0,
                "Fallback Mode": 0
            }
        }
    
    def format_for_terminal(self, text: str) -> str:
        """Convert markdown format to terminal-friendly format"""
        import re
        
        # Remove markdown links, keep text part
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Handle bold markers
        text = re.sub(r'\*\*([^*]+)\*\*', f'{Colors.BOLD}\\1{Colors.RESET}', text)
        text = re.sub(r'__([^_]+)__', f'{Colors.BOLD}\\1{Colors.RESET}', text)
        
        # Handle italic markers (simplified to plain text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # Handle code block markers
        text = re.sub(r'`([^`]+)`', f'{Colors.CYAN}\\1{Colors.RESET}', text)
        
        # Handle header markers
        text = re.sub(r'^### (.+)$', f'{Colors.BRIGHT_BLUE}\\1{Colors.RESET}', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', f'{Colors.BRIGHT_BLUE}{Colors.BOLD}\\1{Colors.RESET}', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', f'{Colors.BRIGHT_BLUE}{Colors.BOLD}\\1{Colors.RESET}', text, flags=re.MULTILINE)
        
        # Handle list markers
        text = re.sub(r'^- (.+)$', f'  • \\1', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\. (.+)$', f'  \\1', text, flags=re.MULTILINE)
        
        return text
    
    def print_welcome(self):
        """Print welcome message"""
        print(f"{Colors.BRIGHT_CYAN}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BRIGHT_BLUE}{Colors.BOLD}🚀 Intelligent RAG Terminal Chat Assistant v2.0{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.CYAN}💡 Features:{Colors.RESET}")
        print(f"   • ⚡ Parallel Retrieval (Knowledge Base + Web Search)")  
        print(f"   • 🧠 Intelligent Mode Adaptation")
        print(f"   • 🔗 Multi-source Information Fusion")
        print(f"   • 📊 Real-time Performance Monitoring")
        print()
        print(f"{Colors.YELLOW}📋 Available Commands:{Colors.RESET}")
        print(f"   /help     - Show help information")
        print(f"   /stats    - Show session statistics")
        print(f"   /kb       - Knowledge base management")
        print(f"   /history  - Show conversation history")
        print(f"   /clear    - Clear screen")
        print(f"   /exit     - Exit program")
        print()
        
        # Show current configuration
        print(f"{Colors.GREEN}🔧 Current Configuration:{Colors.RESET}")
        print(f"   Knowledge Base: {self.settings.current_collection_name}")
        print(f"   Web Search: {'✅ Enabled' if self.settings.tavily_api_key else '❌ Not Configured'}")
        print(f"   Session Started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BRIGHT_CYAN}{'-' * 60}{Colors.RESET}")
        print()
    
    def print_help(self):
        """Print help information"""
        print(f"\n{Colors.BRIGHT_BLUE}📖 RAG Terminal Chat Assistant Help{Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * 40}{Colors.RESET}")
        
        print(f"\n{Colors.YELLOW}💬 Basic Usage:{Colors.RESET}")
        print(f"   Simply enter your question, the system will automatically perform parallel retrieval and answer")
        print(f"   Example: What are the advantages of Python's asynchronous programming?")
        
        print(f"\n{Colors.YELLOW}🎯 How It Works:{Colors.RESET}")
        print(f"   1. 📝 Query Analysis - Understand your question")
        print(f"   2. ⚡ Parallel Retrieval - Search knowledge base and web simultaneously")
        print(f"   3. 🔗 Information Fusion - Integrate multi-source information")
        print(f"   4. 🤖 Intelligent Answer - Generate comprehensive response")
        
        print(f"\n{Colors.YELLOW}📊 System Commands:{Colors.RESET}")
        
        commands = [
            ("/help", "Show this help information"),
            ("/stats", "Show session statistics"),
            ("/history", "Show conversation history"),
            ("/kb list", "List all knowledge bases"),
            ("/kb switch <n>", "Switch to specified knowledge base"),
            ("/kb info", "Show current knowledge base information"),
            ("/clear", "Clear terminal screen"),
            ("/exit", "Exit chat program")
        ]
        
        for cmd, desc in commands:
            print(f"   {Colors.BRIGHT_GREEN}{cmd:<20}{Colors.RESET} - {desc}")
        
        print(f"\n{Colors.YELLOW}🎨 Display Legend:{Colors.RESET}")
        print(f"   {Colors.BRIGHT_BLUE}Blue{Colors.RESET} - System information")
        print(f"   {Colors.BRIGHT_GREEN}Green{Colors.RESET} - Success status")
        print(f"   {Colors.BRIGHT_YELLOW}Yellow{Colors.RESET} - Warning information")
        print(f"   {Colors.BRIGHT_RED}Red{Colors.RESET} - Error information")
        print(f"   {Colors.CYAN}Cyan{Colors.RESET} - Statistical data")
        print()
    
    def print_stats(self):
        """Print statistics information"""
        print(f"\n{Colors.BRIGHT_BLUE}📊 Session Statistics{Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * 40}{Colors.RESET}")
        
        session_duration = datetime.now() - self.session_start
        duration_str = str(session_duration).split('.')[0]  # Remove microseconds
        
        print(f"🕒 Session Duration: {duration_str}")
        print(f"💬 Total Queries: {self.stats['total_queries']}")
        
        if self.stats['total_queries'] > 0:
            print(f"⚡ Average Response: {self.stats['avg_response_time']:.2f}s")
            print(f"⏱️  Total Processing Time: {self.stats['total_time']:.2f}s")
            
            print(f"\n{Colors.YELLOW}🎯 Mode Usage Statistics:{Colors.RESET}")
            for mode, count in self.stats['modes_used'].items():
                if count > 0:
                    percentage = (count / self.stats['total_queries']) * 100
                    print(f"   {mode}: {count} times ({percentage:.1f}%)")
        else:
            print(f"   {Colors.DIM}No query records yet{Colors.RESET}")
        print()
    
    def print_history(self, limit: int = 5):
        """Print conversation history"""
        print(f"\n{Colors.BRIGHT_BLUE}📜 Conversation History (Latest {min(limit, len(self.chat_history))} entries){Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * 50}{Colors.RESET}")
        
        if not self.chat_history:
            print(f"   {Colors.DIM}No conversation records yet{Colors.RESET}")
            return
        
        for i, record in enumerate(self.chat_history[-limit:], 1):
            timestamp = record['timestamp'].strftime('%H:%M:%S')
            query = record['query'][:50] + ('...' if len(record['query']) > 50 else '')
            mode = record.get('mode', 'Unknown')
            response_time = record.get('response_time', 0)
            
            print(f"{Colors.GREEN}{i:2d}.{Colors.RESET} [{timestamp}] {Colors.CYAN}{mode}{Colors.RESET}")
            print(f"     Q: {query}")
            print(f"     T: {response_time:.2f}s")
            print()
    
    async def handle_kb_command(self, args: list):
        """Handle knowledge base commands"""
        if not args:
            print(f"{Colors.YELLOW}💡 Usage: /kb <list|switch|info>{Colors.RESET}")
            return
        
        cmd = args[0].lower()
        
        if cmd == "list":
            print(f"\n{Colors.BRIGHT_BLUE}📚 Available Knowledge Bases:{Colors.RESET}")
            try:
                kbs = self.kb_manager.list_knowledge_bases()
                current = self.settings.current_collection_name
                
                for kb in kbs:
                    marker = "✅" if kb == current else "  "
                    print(f"   {marker} {kb}")
                    
                if not kbs:
                    print(f"   {Colors.DIM}No knowledge bases available{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}❌ Failed to get knowledge base list: {e}{Colors.RESET}")
        
        elif cmd == "switch":
            if len(args) < 2:
                print(f"{Colors.YELLOW}💡 Usage: /kb switch <knowledge_base_name>{Colors.RESET}")
                return
            
            kb_name = args[1]
            try:
                kbs = self.kb_manager.list_knowledge_bases()
                if kb_name in kbs:
                    self.settings.current_collection_name = kb_name
                    print(f"{Colors.GREEN}✅ Switched to knowledge base: {kb_name}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}❌ Knowledge base '{kb_name}' does not exist{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}❌ Failed to switch knowledge base: {e}{Colors.RESET}")
        
        elif cmd == "info":
            print(f"\n{Colors.BRIGHT_BLUE}ℹ️  Current Knowledge Base Information:{Colors.RESET}")
            current = self.settings.current_collection_name
            print(f"   Name: {current}")
            
            try:
                stats = self.kb_manager.get_knowledge_base_stats(current)
                print(f"   Documents: {stats.get('total_documents', 'N/A')}")
                print(f"   Last Updated: {stats.get('last_updated', 'N/A')}")
            except Exception as e:
                print(f"   {Colors.YELLOW}⚠️ Unable to get detailed information: {e}{Colors.RESET}")
        
        else:
            print(f"{Colors.RED}❌ Unknown knowledge base command: {cmd}{Colors.RESET}")
        
        print()
    
    async def stream_chunk_handler(self, chunk: str):
        """Handle streaming output text chunks"""
        # Output text directly, now AI outputs plain text format
        print(chunk, end='', flush=True)
    
    def reset_stream_processor(self):
        """Reset streaming processor state"""
        self.markdown_processor.reset()
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query"""
        print(f"{Colors.BRIGHT_BLUE}🔄 Processing query...{Colors.RESET}")
        
        # Reset streaming processor state
        self.reset_stream_processor()
        
        start_time = time.time()
        
        try:
            # Show answer start marker
            print(f"\n{Colors.BRIGHT_GREEN}🤖 AI Assistant Response{Colors.RESET}")
            print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
            print()
            
            # Execute RAG workflow - use streaming output
            result = await rag_workflow.run(query, stream_callback=self.stream_chunk_handler)
            
            # Output newline to indicate answer end
            print("\n")
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self.stats['total_queries'] += 1
            self.stats['total_time'] += processing_time
            self.stats['avg_response_time'] = self.stats['total_time'] / self.stats['total_queries']
            
            # Compatibility handling: check if result is RAGState object or dictionary
            if hasattr(result, 'metadata'):
                # RAGState object
                response = result.response
                metadata = result.metadata
            else:
                # Dictionary format
                response = result.get('response', str(result))
                metadata = result.get('metadata', {})
            
            # Count mode usage
            mode = metadata.get('retrieval_mode', 'Unknown Mode')
            if mode in self.stats['modes_used']:
                self.stats['modes_used'][mode] += 1
            
            # Record conversation history
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
            error_msg = "User interrupted answer generation"
            print(f"\n{Colors.YELLOW}⚠️ {error_msg}{Colors.RESET}")
            
            self.chat_history.append({
                'timestamp': datetime.now(),
                'query': query,
                'response': error_msg,
                'mode': 'Interrupted',
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
            error_msg = f"Error occurred while processing query: {str(e)}"
            print(f"\n{Colors.RED}❌ {error_msg}{Colors.RESET}")
            
            self.chat_history.append({
                'timestamp': datetime.now(),
                'query': query,
                'response': error_msg,
                'mode': 'Error',
                'response_time': processing_time,
                'metadata': {'error': str(e)}
            })
            
            return {
                'response': error_msg,
                'metadata': {'error': str(e)},
                'processing_time': processing_time
            }
    
    def display_response(self, result: Dict[str, Any]):
        """Display response result metadata information (response content already shown via streaming output)"""
        metadata = result['metadata']
        processing_time = result['processing_time']
        
        # Don't show detailed information for errors or interruptions
        if 'error' in metadata or 'interrupted' in metadata:
            return
        
        # Processing information area - more compact display
        print(f"{Colors.DIM}📊 Processing Information{Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * 30}{Colors.RESET}")
        
        # Create information line
        info_parts = []
        info_parts.append(f"⚡ {processing_time:.2f}s")
        
        if 'retrieval_mode' in metadata:
            mode = metadata['retrieval_mode']
            mode_emoji = {
                "Hybrid Mode": "🔗",
                "Knowledge Base Mode": "📚", 
                "Web Mode": "🌐",
                "No Results": "❌"
            }.get(mode, "🎯")
            info_parts.append(f"{mode_emoji} {mode}")
        
        # Result statistics
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
        
        # Display all information in single line
        print(f"   {' | '.join(info_parts)}")
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print()
    
    async def run(self):
        """Run main loop"""
        try:
            self.print_welcome()
            
            while True:
                try:
                    # Get user input
                    user_input = input(f"{Colors.BRIGHT_YELLOW}➤ {Colors.RESET}").strip()
                    
                    # Handle empty input
                    if not user_input:
                        continue
                    
                    # Handle system commands
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
                            print(f"{Colors.BRIGHT_BLUE}👋 Thank you for using RAG Terminal Chat Assistant!{Colors.RESET}")
                            break
                        else:
                            print(f"{Colors.RED}❌ Unknown command: {user_input}{Colors.RESET}")
                            print(f"{Colors.YELLOW}💡 Type /help to see available commands{Colors.RESET}")
                        
                        continue
                    
                    # Handle normal queries
                    result = await self.process_query(user_input)
                    self.display_response(result)
                
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}⚠️ Interrupt signal detected{Colors.RESET}")
                    confirm = input(f"{Colors.YELLOW}Are you sure you want to exit? (y/N): {Colors.RESET}").strip().lower()
                    if confirm in ['y', 'yes']:
                        break
                    else:
                        print(f"{Colors.GREEN}Continuing conversation...{Colors.RESET}\n")
                        continue
                
                except Exception as e:
                    print(f"{Colors.RED}❌ Program error: {e}{Colors.RESET}")
                    print(f"{Colors.YELLOW}💡 Program will continue running, you can keep asking questions{Colors.RESET}\n")
        
        except Exception as e:
            print(f"{Colors.RED}❌ Program startup failed: {e}{Colors.RESET}")
            return
        
        finally:
            # Show session summary
            print(f"\n{Colors.BRIGHT_BLUE}📊 Session Summary:{Colors.RESET}")
            session_duration = datetime.now() - self.session_start
            print(f"   Session Duration: {str(session_duration).split('.')[0]}")
            print(f"   Total Queries: {self.stats['total_queries']}")
            if self.stats['total_queries'] > 0:
                print(f"   Average Response Time: {self.stats['avg_response_time']:.2f}s")
            print(f"{Colors.BRIGHT_CYAN}Goodbye!{Colors.RESET}")


async def main():
    """Main function"""
    chat = TerminalChat()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Program interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Program runtime error: {e}{Colors.RESET}")
        sys.exit(1)
