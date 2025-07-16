# TESTIA AI Agent - Instrucciones de Uso

## 🚀 Inicio Rápido

### Opción 1: Docker (Recomendado)

1. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus API keys
   ```

2. **Ejecutar con Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Acceder a las interfaces**:
   - Web UI: http://localhost:8080
   - MCP Server: ws://localhost:3000

### Opción 2: Ejecución Local

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Ejecutar**:
   ```bash
   # Windows
   start.bat
   
   # Linux/Mac
   chmod +x start.sh
   ./start.sh
   ```

## 💻 Uso del CLI

### Modo Interactivo
```bash
# Windows
cli.bat interactive

# Linux/Mac
chmod +x cli.sh
./cli.sh interactive
```

### Comandos Específicos
```bash
# Chat directo
./cli.sh chat --agent code-assistant --stream

# Gestión de agentes
./cli.sh agents

# Gestión de modelos
./cli.sh models

# Servidor MCP
./cli.sh mcp --port 3000
```

## 🌐 Interfaz Web

La interfaz web proporciona:

- **Dashboard**: Vista general del sistema
- **Chat**: Interfaz de conversación con agentes
- **Agentes**: Gestión de agentes de IA
- **Modelos**: Configuración de modelos

### Características del Chat Web:
- Soporte para streaming en tiempo real
- Múltiples conversaciones simultáneas
- Intercambio de agentes dinámico
- Historial de conversaciones

## 🔌 Model Context Protocol (MCP)

### Servidor MCP Interno

El servidor MCP se ejecuta en el puerto 3000 y proporciona:

- **Tools disponibles**:
  - `chat`: Conversar con agentes
  - `list_agents`: Listar agentes disponibles
  - `get_agent_config`: Obtener configuración de agente
  - `update_agent_instructions`: Actualizar instrucciones

### Conectar desde VS Code

1. **Instalar extensión MCP para VS Code**
2. **Configurar conexión**:
   ```json
   {
     "mcp.servers": {
       "testia": {
         "command": "node",
         "args": ["path/to/mcp-client.js"],
         "env": {
           "MCP_SERVER_URL": "ws://localhost:3000"
         }
       }
     }
   }
   ```

### Cliente MCP Personalizado

```python
from src.mcp.client import TestiaMCPClient, MCPServerConfig

client = TestiaMCPClient()

# Agregar servidor externo
config = MCPServerConfig(
    name="external-server",
    url="ws://localhost:3001",
    description="Servidor externo"
)
await client.add_server(config)

# Llamar herramienta
response = await client.call_tool(
    "external-server", 
    "some_tool", 
    {"param": "value"}
)
```

## 🤖 Configuración de Agentes

### Agentes Predefinidos

1. **general-assistant**: Asistente general
2. **code-assistant**: Especialista en programación
3. **data-analyst**: Especialista en análisis de datos
4. **spanish-tutor**: Tutor de español
5. **docker-expert**: Experto en Docker

### Crear Agente Personalizado

#### Via Web UI:
1. Ir a `/agents`
2. Clic en "Crear Agente"
3. Completar formulario
4. Guardar

#### Via CLI:
```bash
./cli.sh agents
# Seleccionar opción 3: "Create custom agent"
```

#### Via API:
```bash
curl -X POST http://localhost:8080/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mi-agente",
    "description": "Mi agente personalizado",
    "model_name": "gpt-4",
    "instructions": "Eres un experto en...",
    "temperature": 0.7
  }'
```

#### Via Configuración:
Editar `config/agents.json`:
```json
{
  "agents": [
    {
      "type": "custom",
      "name": "mi-agente-custom",
      "description": "Agente altamente especializado",
      "model_name": "gpt-4",
      "instructions": "Instrucciones detalladas...",
      "system_prompt": "Prompt de sistema...",
      "temperature": 0.3,
      "max_context_length": 8000,
      "tools": ["tool1", "tool2"],
      "enabled": true,
      "metadata": {
        "category": "specialized",
        "version": "1.0"
      }
    }
  ]
}
```

## 🧠 Configuración de Modelos

### Proveedores Soportados

1. **OpenAI**: GPT-4, GPT-3.5-turbo
2. **Anthropic**: Claude-3 (Sonnet, Opus)
3. **HuggingFace**: Mixtral, Llama, etc.
4. **Local**: Ollama, LocalAI
5. **Custom**: APIs personalizadas

### Agregar Modelo Personalizado

Editar `config/models.json`:
```json
{
  "models": {
    "mi-modelo-local": {
      "provider": "custom",
      "model_id": "llama2-7b",
      "api_base": "http://localhost:11434/v1",
      "max_tokens": 2000,
      "temperature": 0.7,
      "context_window": 4096,
      "enabled": true,
      "instructions": "Instrucciones específicas del modelo",
      "custom_parameters": {
        "stream": true,
        "top_p": 0.9
      }
    }
  }
}
```

### Variables de Entorno para API Keys

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google
GOOGLE_API_KEY=AIza...

# Hugging Face
HUGGINGFACE_API_KEY=hf_...
```

## 🔧 Personalización Avanzada

### Extender Funcionalidad

1. **Agregar nuevos proveedores de modelos**:
   - Implementar clase heredando de `BaseModelProvider`
   - Registrar en `ModelManager`

2. **Crear tipos de agentes especializados**:
   - Heredar de `BaseAgent`
   - Implementar lógica específica
   - Registrar en `AgentManager`

3. **Agregar herramientas MCP**:
   - Implementar funciones de herramientas
   - Registrar en `TestiaMCPServer`

### Hooks y Callbacks

```python
# Ejemplo: Hook para logging de conversaciones
class LoggingAgent(BaseAgent):
    async def process_message(self, message, **kwargs):
        # Log entrada
        logger.info(f"Mensaje recibido: {message}")
        
        # Procesar normalmente
        response = await super().process_message(message, **kwargs)
        
        # Log salida
        logger.info(f"Respuesta enviada: {response}")
        
        return response
```

## 📊 Monitoreo y Logs

### Logs del Sistema

```bash
# Ver logs en tiempo real
docker-compose logs -f testia-agent

# Logs específicos
tail -f logs/testia.log
tail -f logs/mcp.log
tail -f logs/web.log
```

### Métricas Disponibles

- Número de agentes activos
- Conversaciones por agente
- Uso de modelos
- Conexiones MCP
- Latencia de respuestas

### API de Estado

```bash
curl http://localhost:8080/api/status
```

## 🚧 Solución de Problemas

### Problemas Comunes

1. **Error de API Key**:
   - Verificar variables de entorno
   - Comprobar permisos de API

2. **Conexión MCP fallida**:
   - Verificar puerto 3000 disponible
   - Comprobar firewall

3. **Agente no responde**:
   - Verificar modelo configurado
   - Comprobar logs de errores

4. **Web UI no carga**:
   - Verificar puerto 8080 disponible
   - Comprobar logs del servidor web

### Comandos de Diagnóstico

```bash
# Verificar puertos
netstat -tulpn | grep :8080
netstat -tulpn | grep :3000

# Verificar Docker
docker ps
docker-compose ps

# Verificar logs
docker-compose logs testia-agent | tail -50

# Reiniciar servicios
docker-compose restart
```

### Modo Debug

```bash
# Activar logs debug
export LOG_LEVEL=DEBUG

# Ejecutar con debug
python src/main.py
```

## 🔐 Seguridad

### Recomendaciones

1. **API Keys**: Usar variables de entorno, nunca hardcodear
2. **Red**: Usar HTTPS en producción
3. **Acceso**: Configurar autenticación si es necesario
4. **Firewall**: Restringir puertos según necesidad

### Configuración de Producción

```yaml
# docker-compose.prod.yml
services:
  testia-agent:
    environment:
      - LOG_LEVEL=INFO
      - ENABLE_AUTH=true
      - JWT_SECRET=${JWT_SECRET}
    ports:
      - "443:8080"  # HTTPS
    volumes:
      - ./ssl:/app/ssl:ro
```

## 📚 Recursos Adicionales

- [Documentación MCP](https://modelcontextprotocol.io/)
- [OpenAI API](https://platform.openai.com/docs)
- [Anthropic API](https://docs.anthropic.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Docker Docs](https://docs.docker.com/)

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama de feature
3. Hacer cambios
4. Agregar tests
5. Crear Pull Request

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles.
