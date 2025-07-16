"""
TESTIA AI Agent - Main Application
"""
import os
import sys
import asyncio
import logging
from typing import Optional

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.manager import ModelManager
from src.agents.manager import AgentManager
from src.mcp.server import SimpleMCPServer as TestiaMCPServer
from src.web.app import run_web_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TestiaApplication:
    """Main TESTIA application"""
    
    def __init__(self):
        self.model_manager: Optional[ModelManager] = None
        self.agent_manager: Optional[AgentManager] = None
        self.mcp_server: Optional[TestiaMCPServer] = None
        
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("🚀 Initializing TESTIA AI Agent...")
            
            # Initialize model manager
            logger.info("📊 Loading models...")
            self.model_manager = ModelManager()
            await self.model_manager.load_models()
            logger.info(f"✅ Loaded {len(self.model_manager.get_available_models())} models")
            
            # Initialize agent manager
            logger.info("🤖 Loading agents...")
            self.agent_manager = AgentManager(self.model_manager)
            await self.agent_manager.load_agents()
            logger.info(f"✅ Loaded {len(self.agent_manager.list_agents())} agents")
            
            # Initialize MCP server
            logger.info("🔌 Setting up MCP server...")
            self.mcp_server = TestiaMCPServer(self.model_manager)
            
            # Add agents to MCP server
            for agent_id, agent in self.agent_manager.agents.items():
                await self.mcp_server.add_agent(agent_id, agent)
            
            logger.info("✅ TESTIA AI Agent initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing TESTIA: {e}")
            raise
    
    async def start_mcp_server(self, host: str = "0.0.0.0", port: int = 3000):
        """Start the MCP server"""
        try:
            logger.info(f"🌐 Starting MCP server on {host}:{port}...")
            server = await self.mcp_server.start_server(host, port)
            logger.info(f"✅ MCP server running on ws://{host}:{port}")
            return server
        except Exception as e:
            logger.error(f"❌ Error starting MCP server: {e}")
            raise
    
    def start_web_server(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the web server"""
        try:
            logger.info(f"🌐 Starting web server on {host}:{port}...")
            # Set global managers for web app
            from src.web import app as web_app
            web_app.model_manager = self.model_manager
            web_app.agent_manager = self.agent_manager
            web_app.mcp_server = self.mcp_server
            
            run_web_server(host, port)
        except Exception as e:
            logger.error(f"❌ Error starting web server: {e}")
            raise
    
    async def run_all_servers(self, 
                             web_host: str = "0.0.0.0", 
                             web_port: int = 8080,
                             mcp_host: str = "0.0.0.0", 
                             mcp_port: int = 3000):
        """Run both MCP and web servers concurrently"""
        try:
            # Start MCP server
            await self.start_mcp_server(mcp_host, mcp_port)
            
            # Give MCP server time to start
            await asyncio.sleep(1)
            
            # Start web server in a thread (since uvicorn.run is blocking)
            import threading
            web_thread = threading.Thread(
                target=self.start_web_server,
                args=(web_host, web_port),
                daemon=True
            )
            web_thread.start()
            
            logger.info("🎉 All servers started successfully!")
            logger.info(f"📱 Web UI: http://{web_host}:{web_port}")
            logger.info(f"🔌 MCP Server: ws://{mcp_host}:{mcp_port}")
            logger.info("Press Ctrl+C to stop")
            
            # Keep the main process alive
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Shutting down servers...")
                
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down servers...")
        except Exception as e:
            logger.error(f"❌ Error running servers: {e}")
            raise


async def main():
    """Main entry point"""
    app = TestiaApplication()
    await app.initialize()
    
    # Get configuration from environment
    web_host = os.getenv("WEB_HOST", "0.0.0.0")
    web_port = int(os.getenv("WEB_PORT", "8080"))
    mcp_host = os.getenv("MCP_HOST", "0.0.0.0")
    mcp_port = int(os.getenv("MCP_PORT", "3000"))
    
    # Run all servers
    await app.run_all_servers(web_host, web_port, mcp_host, mcp_port)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 TESTIA AI Agent stopped")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
