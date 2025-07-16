"""
Command Line Interface for TESTIA AI Agent
"""
import asyncio
import click
import json
import sys
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from ..models.manager import ModelManager
from ..agents.manager import AgentManager
from ..mcp.server import TestiaMCPServer

console = Console()


class TESTIACLI:
    def __init__(self):
        self.model_manager: Optional[ModelManager] = None
        self.agent_manager: Optional[AgentManager] = None
        self.mcp_server: Optional[TestiaMCPServer] = None
        self.current_agent = "general-assistant"
        self.current_conversation = None
        
    async def initialize(self):
        """Initialize the CLI components"""
        try:
            console.print("[bold green]Initializing TESTIA AI Agent...[/bold green]")
            
            # Initialize model manager
            self.model_manager = ModelManager()
            await self.model_manager.load_models()
            
            # Initialize agent manager
            self.agent_manager = AgentManager(self.model_manager)
            await self.agent_manager.load_agents()
            
            # Initialize MCP server
            self.mcp_server = TestiaMCPServer(self.model_manager)
            
            # Add agents to MCP server
            for agent_id, agent in self.agent_manager.agents.items():
                await self.mcp_server.add_agent(agent_id, agent)
            
            console.print("[bold green]✅ TESTIA initialized successfully![/bold green]")
            
        except Exception as e:
            console.print(f"[bold red]❌ Error initializing TESTIA: {e}[/bold red]")
            raise

    def show_welcome(self):
        """Show welcome message"""
        welcome_text = """
# Welcome to TESTIA AI Agent CLI

🤖 **Custom AI Agent with MCP Support**

**Available Commands:**
- `chat` - Start interactive chat
- `agents` - Manage agents
- `models` - Manage models  
- `mcp` - MCP server operations
- `help` - Show this help
- `exit` - Exit CLI

Type a command to get started!
        """
        
        console.print(Panel(
            Markdown(welcome_text),
            title="[bold blue]TESTIA AI Agent[/bold blue]",
            border_style="blue"
        ))


@click.group()
@click.pass_context
def cli(ctx):
    """TESTIA AI Agent - Custom AI with MCP Support"""
    if ctx.obj is None:
        ctx.obj = TESTIACLI()


@cli.command()
@click.option('--agent', '-a', default=None, help='Agent to chat with')
@click.option('--stream', '-s', is_flag=True, help='Enable streaming responses')
@click.pass_context
def chat(ctx, agent, stream):
    """Start interactive chat with an AI agent"""
    asyncio.run(_chat_command(ctx.obj, agent, stream))


async def _chat_command(cli_obj: TESTIACLI, agent_name: Optional[str], stream: bool):
    """Async chat command implementation"""
    await cli_obj.initialize()
    
    if agent_name:
        if agent_name not in cli_obj.agent_manager.list_agents():
            console.print(f"[red]Agent '{agent_name}' not found[/red]")
            return
        cli_obj.current_agent = agent_name
    
    agent = cli_obj.agent_manager.get_agent(cli_obj.current_agent)
    if not agent:
        console.print(f"[red]Agent '{cli_obj.current_agent}' not available[/red]")
        return
    
    console.print(f"[green]💬 Starting chat with {agent.name}[/green]")
    console.print(f"[dim]Type 'exit' to end chat, '/help' for commands[/dim]\n")
    
    # Setup prompt session
    session = PromptSession(
        history=FileHistory('.testia_history'),
        auto_suggest=AutoSuggestFromHistory(),
    )
    
    conversation_id = None
    
    while True:
        try:
            # Get user input
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, lambda: session.prompt(f"[{cli_obj.current_agent}] You: ")
            )
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                break
            elif user_input.startswith('/'):
                await _handle_chat_command(cli_obj, user_input, agent)
                continue
            elif not user_input.strip():
                continue
            
            # Process message
            try:
                if stream:
                    console.print(f"[{cli_obj.current_agent}] Assistant: ", end="")
                    response_chunks = []
                    async for chunk in cli_obj.agent_manager.process_message(
                        cli_obj.current_agent, 
                        user_input, 
                        conversation_id=conversation_id,
                        stream=True
                    ):
                        console.print(chunk, end="")
                        response_chunks.append(chunk)
                    console.print()  # New line after streaming
                else:
                    with console.status("[bold green]Thinking...", spinner="dots"):
                        response = await cli_obj.agent_manager.process_message(
                            cli_obj.current_agent, 
                            user_input,
                            conversation_id=conversation_id
                        )
                    
                    console.print(f"[{cli_obj.current_agent}] Assistant: {response}")
                
                # Set conversation ID if not set
                if conversation_id is None:
                    conversations = agent.list_conversations()
                    if conversations:
                        conversation_id = conversations[-1]
                        
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Chat interrupted[/yellow]")
            break
        except EOFError:
            break
    
    console.print(f"[green]👋 Chat with {agent.name} ended[/green]")


async def _handle_chat_command(cli_obj: TESTIACLI, command: str, agent):
    """Handle special chat commands"""
    cmd_parts = command[1:].split()
    cmd = cmd_parts[0] if cmd_parts else ""
    
    if cmd == "help":
        help_text = """
**Chat Commands:**
- `/help` - Show this help
- `/clear` - Clear conversation history
- `/agent <name>` - Switch to different agent
- `/status` - Show current agent status
- `/save <filename>` - Save conversation
        """
        console.print(Panel(Markdown(help_text), title="Chat Help"))
        
    elif cmd == "clear":
        agent.clear_all_conversations()
        console.print("[green]✅ Conversation history cleared[/green]")
        
    elif cmd == "agent" and len(cmd_parts) > 1:
        new_agent = cmd_parts[1]
        if new_agent in cli_obj.agent_manager.list_agents():
            cli_obj.current_agent = new_agent
            console.print(f"[green]✅ Switched to agent: {new_agent}[/green]")
        else:
            console.print(f"[red]❌ Agent '{new_agent}' not found[/red]")
            
    elif cmd == "status":
        status = agent.get_status()
        table = Table(title=f"Agent Status: {agent.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in status.items():
            table.add_row(str(key), str(value))
        
        console.print(table)
        
    else:
        console.print(f"[red]Unknown command: {command}[/red]")


@cli.command()
@click.pass_context
def agents(ctx):
    """Manage AI agents"""
    asyncio.run(_agents_command(ctx.obj))


async def _agents_command(cli_obj: TESTIACLI):
    """Async agents command implementation"""
    await cli_obj.initialize()
    
    while True:
        console.print("\n[bold blue]🤖 Agent Management[/bold blue]")
        console.print("1. List agents")
        console.print("2. Show agent details")
        console.print("3. Create custom agent")
        console.print("4. Enable/Disable agent")
        console.print("5. Update agent instructions")
        console.print("6. Back to main menu")
        
        choice = console.input("\nChoice (1-6): ")
        
        if choice == "1":
            await _list_agents(cli_obj)
        elif choice == "2":
            await _show_agent_details(cli_obj)
        elif choice == "3":
            await _create_custom_agent(cli_obj)
        elif choice == "4":
            await _toggle_agent(cli_obj)
        elif choice == "5":
            await _update_agent_instructions(cli_obj)
        elif choice == "6":
            break
        else:
            console.print("[red]Invalid choice[/red]")


async def _list_agents(cli_obj: TESTIACLI):
    """List all agents"""
    table = Table(title="Available Agents")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("Conversations", style="blue")
    
    for agent_id, agent in cli_obj.agent_manager.agents.items():
        status = "🟢 Enabled" if agent.config.enabled else "🔴 Disabled"
        conv_count = len(agent.conversations)
        
        table.add_row(
            agent_id,
            agent.name,
            agent.config.model_name,
            status,
            str(conv_count)
        )
    
    console.print(table)


async def _show_agent_details(cli_obj: TESTIACLI):
    """Show detailed information about an agent"""
    agent_id = console.input("Enter agent ID: ")
    agent = cli_obj.agent_manager.get_agent(agent_id)
    
    if not agent:
        console.print(f"[red]Agent '{agent_id}' not found[/red]")
        return
    
    details = agent.to_dict()
    
    console.print(f"\n[bold]Agent Details: {agent.name}[/bold]")
    console.print(f"Description: {details['description']}")
    console.print(f"Model: {details['model_name']}")
    console.print(f"Temperature: {details['temperature']}")
    console.print(f"Max Context: {details['max_context_length']}")
    console.print(f"Tools: {', '.join(details['tools']) or 'None'}")
    console.print(f"Enabled: {details['enabled']}")
    
    console.print(f"\n[bold]Instructions:[/bold]")
    console.print(Panel(details['instructions'], border_style="dim"))


async def _create_custom_agent(cli_obj: TESTIACLI):
    """Create a new custom agent"""
    console.print("\n[bold]Create Custom Agent[/bold]")
    
    name = console.input("Agent name: ")
    description = console.input("Description: ")
    
    # Show available models
    models = cli_obj.model_manager.get_available_models()
    console.print(f"Available models: {', '.join(models)}")
    model_name = console.input("Model name: ")
    
    if model_name not in models:
        console.print(f"[red]Model '{model_name}' not available[/red]")
        return
    
    instructions = console.input("Instructions: ")
    
    try:
        await cli_obj.agent_manager.create_custom_agent(
            name=name,
            description=description,
            model_name=model_name,
            instructions=instructions
        )
        
        # Add to MCP server
        agent = cli_obj.agent_manager.get_agent(name)
        await cli_obj.mcp_server.add_agent(name, agent)
        
        console.print(f"[green]✅ Created agent: {name}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error creating agent: {e}[/red]")


async def _toggle_agent(cli_obj: TESTIACLI):
    """Enable or disable an agent"""
    agent_id = console.input("Enter agent ID: ")
    agent = cli_obj.agent_manager.get_agent(agent_id)
    
    if not agent:
        console.print(f"[red]Agent '{agent_id}' not found[/red]")
        return
    
    if agent.config.enabled:
        cli_obj.agent_manager.disable_agent(agent_id)
        console.print(f"[yellow]🔴 Disabled agent: {agent_id}[/yellow]")
    else:
        cli_obj.agent_manager.enable_agent(agent_id)
        console.print(f"[green]🟢 Enabled agent: {agent_id}[/green]")


async def _update_agent_instructions(cli_obj: TESTIACLI):
    """Update agent instructions"""
    agent_id = console.input("Enter agent ID: ")
    agent = cli_obj.agent_manager.get_agent(agent_id)
    
    if not agent:
        console.print(f"[red]Agent '{agent_id}' not found[/red]")
        return
    
    console.print(f"\nCurrent instructions:\n{agent.instructions}")
    new_instructions = console.input("\nNew instructions: ")
    
    if new_instructions:
        agent.update_instructions(new_instructions)
        console.print(f"[green]✅ Updated instructions for {agent_id}[/green]")


@cli.command()
@click.pass_context  
def models(ctx):
    """Manage AI models"""
    asyncio.run(_models_command(ctx.obj))


async def _models_command(cli_obj: TESTIACLI):
    """Async models command implementation"""
    await cli_obj.initialize()
    
    while True:
        console.print("\n[bold blue]🧠 Model Management[/bold blue]")
        console.print("1. List models")
        console.print("2. Show model details")
        console.print("3. Add model configuration")
        console.print("4. Back to main menu")
        
        choice = console.input("\nChoice (1-4): ")
        
        if choice == "1":
            await _list_models(cli_obj)
        elif choice == "2":
            await _show_model_details(cli_obj)
        elif choice == "3":
            await _add_model_config(cli_obj)
        elif choice == "4":
            break
        else:
            console.print("[red]Invalid choice[/red]")


async def _list_models(cli_obj: TESTIACLI):
    """List all available models"""
    models_info = cli_obj.model_manager.get_all_models_info()
    
    table = Table(title="Available Models")
    table.add_column("Name", style="cyan")
    table.add_column("Provider", style="green")
    table.add_column("Model ID", style="yellow")
    table.add_column("Max Tokens", style="magenta")
    table.add_column("Context Window", style="blue")
    
    for name, info in models_info.items():
        table.add_row(
            name,
            info["provider"],
            info["model_id"],
            str(info["max_tokens"]),
            str(info["context_window"])
        )
    
    console.print(table)


async def _show_model_details(cli_obj: TESTIACLI):
    """Show detailed model information"""
    model_name = console.input("Enter model name: ")
    info = cli_obj.model_manager.get_model_info(model_name)
    
    if not info:
        console.print(f"[red]Model '{model_name}' not found[/red]")
        return
    
    table = Table(title=f"Model Details: {model_name}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in info.items():
        table.add_row(str(key), str(value))
    
    console.print(table)


async def _add_model_config(cli_obj: TESTIACLI):
    """Add a new model configuration"""
    console.print("\n[bold]Add Model Configuration[/bold]")
    console.print("This feature requires manual configuration file editing.")
    console.print("Please edit config/models.json to add new models.")


@cli.command()
@click.option('--port', '-p', default=3000, help='MCP server port')
@click.pass_context
def mcp(ctx, port):
    """Start MCP server"""
    asyncio.run(_mcp_command(ctx.obj, port))


async def _mcp_command(cli_obj: TESTIACLI, port: int):
    """Start MCP server"""
    await cli_obj.initialize()
    
    console.print(f"[bold green]🚀 Starting MCP server on port {port}...[/bold green]")
    
    try:
        server = await cli_obj.mcp_server.start_server(port=port)
        console.print(f"[green]✅ MCP server running on ws://localhost:{port}[/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        
        # Keep server running
        try:
            await server.wait_closed()
        except KeyboardInterrupt:
            console.print("\n[yellow]🛑 MCP server stopped[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Error starting MCP server: {e}[/red]")


@cli.command()
def interactive():
    """Start interactive mode"""
    asyncio.run(_interactive_mode())


async def _interactive_mode():
    """Interactive mode implementation"""
    cli_obj = TESTIACLI()
    await cli_obj.initialize()
    
    cli_obj.show_welcome()
    
    session = PromptSession(
        history=FileHistory('.testia_cli_history'),
        auto_suggest=AutoSuggestFromHistory(),
    )
    
    while True:
        try:
            command = await asyncio.get_event_loop().run_in_executor(
                None, lambda: session.prompt("TESTIA> ")
            )
            
            if command.lower() in ['exit', 'quit']:
                break
            elif command == 'help':
                cli_obj.show_welcome()
            elif command == 'chat':
                await _chat_command(cli_obj, None, False)
            elif command == 'agents':
                await _agents_command(cli_obj)
            elif command == 'models':
                await _models_command(cli_obj)
            elif command.startswith('mcp'):
                parts = command.split()
                port = int(parts[1]) if len(parts) > 1 else 3000
                await _mcp_command(cli_obj, port)
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
        except EOFError:
            break
    
    console.print("[green]👋 Goodbye![/green]")


if __name__ == "__main__":
    cli()
