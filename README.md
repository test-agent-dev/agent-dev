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

## Configuración de Modelos

Los modelos disponibles se definen en `models.config.json`. Cada entrada
incluye:
  - `provider`: nombre del servicio o tipo de modelo
  - `api_key`: credencial asociada (opcional)
  - `endpoint`: URL o ruta local del modelo
  - `parameters`: configuración de temperatura, máximo de tokens, etc.

Ejemplo con dos proveedores:

```json
{
  "models": {
    "gpt-4": {
      "provider": "openai",
      "api_key": "${OPENAI_API_KEY}",
      "endpoint": "https://api.openai.com/v1",
      "parameters": {"temperature": 0.7, "max_tokens": 4000}
    },
    "local-llama": {
      "provider": "custom",
      "endpoint": "http://localhost:11434/v1",
      "parameters": {"temperature": 0.7, "max_tokens": 2000}
    }
  }
}
```

Para añadir un nuevo modelo simplemente agrega otra sección siguiendo la misma estructura.

## MCP Support

El proyecto incluye un servidor MCP completo que permite:
- Conexión con herramientas externas
- Intercambio de contexto entre agentes
- Extensibilidad mediante plugins
