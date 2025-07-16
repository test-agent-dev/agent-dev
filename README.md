# Custom AI Agent with MCP Support

Este proyecto proporciona un agente de IA dockerizado con soporte para Model Context Protocol (MCP) y modelos custom.

## Características

- 🐳 Dockerizado para fácil despliegue
- 🔌 Soporte completo para MCP (Model Context Protocol)
- 🤖 Modelos de IA intercambiables y configurables
- 💻 Interfaz CLI
- 🌐 Web UI moderna
- 🛠️ API REST para integraciones
- 📝 Instrucciones personalizables por agente

## Estructura del Proyecto

```
TESTIA/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
│   ├── agents/          # Configuración de agentes
│   ├── mcp/            # Servidor y cliente MCP
│   ├── models/         # Configuración de modelos
│   ├── cli/            # Interfaz de línea de comandos
│   ├── web/            # Interfaz web
│   └── api/            # API REST
├── config/
│   ├── agents.json     # Configuración de agentes
│   ├── models.json     # Configuración de modelos
│   └── mcp.json        # Configuración MCP
└── data/               # Datos persistentes
```

## Inicio Rápido

1. **Clonar y configurar**:
   ```bash
   cd TESTIA
   cp config/example.env .env
   # Editar .env con tus configuraciones
   ```

2. **Ejecutar con Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Usar CLI**:
   ```bash
   docker exec -it testia-agent python src/cli/main.py
   ```

4. **Acceder Web UI**:
   - Abrir http://localhost:8080

## Configuración de Modelos Custom

Edita `config/models.json` para agregar tus modelos:

```json
{
  "models": {
    "custom-gpt": {
      "provider": "openai",
      "model": "gpt-4",
      "api_key": "${OPENAI_API_KEY}",
      "instructions": "Eres un asistente especializado..."
    }
  }
}
```

## MCP Support

El proyecto incluye un servidor MCP completo que permite:
- Conexión con herramientas externas
- Intercambio de contexto entre agentes
- Extensibilidad mediante plugins
