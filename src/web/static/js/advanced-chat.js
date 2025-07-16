// Advanced Chat Interface JavaScript
class AdvancedChatInterface {
    constructor() {
        this.currentConversationId = null;
        this.currentFiles = [];
        this.isStreaming = false;
        this.agents = [];
        this.models = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.loadInitialData();
    }

    initializeElements() {
        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        
        // Configuration elements
        this.agentSelect = document.getElementById('agentSelect');
        this.modelSelect = document.getElementById('modelSelect');
        this.temperatureSlider = document.getElementById('temperatureSlider');
        this.temperatureValue = document.getElementById('temperatureValue');
        this.maxTokensSlider = document.getElementById('maxTokensSlider');
        this.maxTokensValue = document.getElementById('maxTokensValue');
        this.systemPromptTextarea = document.getElementById('systemPromptTextarea');
        this.customInstructions = document.getElementById('customInstructions');
        
        // Code panel elements
        this.codeEditor = document.getElementById('codeEditor');
        this.filesList = document.getElementById('filesList');
        this.extractCodeButton = document.getElementById('extractCodeButton');
        this.saveFileButton = document.getElementById('saveFileButton');
        
        // Status elements
        this.statusIndicator = document.getElementById('statusIndicator');
    }

    setupEventListeners() {
        // Send message
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Configuration changes
        this.agentSelect.addEventListener('change', () => this.updateConfiguration());
        this.modelSelect.addEventListener('change', () => this.updateConfiguration());
        
        // Sliders
        this.temperatureSlider.addEventListener('input', (e) => {
            this.temperatureValue.textContent = e.target.value;
        });
        
        this.maxTokensSlider.addEventListener('input', (e) => {
            this.maxTokensValue.textContent = e.target.value;
        });

        // Code extraction
        this.extractCodeButton.addEventListener('click', () => this.extractCode());
        
        // File management
        this.saveFileButton.addEventListener('click', () => this.saveCurrentFile());
        
        // Apply configuration
        document.getElementById('applyConfigButton').addEventListener('click', () => {
            this.applyConfiguration();
        });
        
        // Clear chat
        document.getElementById('clearChatButton').addEventListener('click', () => {
            this.clearChat();
        });
    }

    async loadInitialData() {
        try {
            // Load agents
            const agentsResponse = await fetch('/api/agents');
            const agentsData = await agentsResponse.json();
            this.agents = agentsData.agents || [];
            this.populateAgentSelect();

            // Load models
            const modelsResponse = await fetch('/api/models');
            const modelsData = await modelsResponse.json();
            this.models = modelsData.models || [];
            this.populateModelSelect();

            this.updateStatus('Ready', 'success');
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.updateStatus('Error loading configuration', 'error');
        }
    }

    populateAgentSelect() {
        this.agentSelect.innerHTML = '<option value="">Select Agent...</option>';
        this.agents.forEach(agent => {
            if (agent.enabled) {
                const option = document.createElement('option');
                option.value = agent.id;
                option.textContent = `${agent.name} - ${agent.description}`;
                this.agentSelect.appendChild(option);
            }
        });
    }

    populateModelSelect() {
        this.modelSelect.innerHTML = '<option value="">Select Model...</option>';
        this.models.forEach(model => {
            if (model.enabled) {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = `${model.name} (${model.provider})`;
                this.modelSelect.appendChild(option);
            }
        });
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isStreaming) return;

        const agentId = this.agentSelect.value;
        if (!agentId) {
            alert('Please select an agent first.');
            return;
        }

        // Add user message to chat
        this.addMessage('user', message);
        this.messageInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            this.isStreaming = true;
            this.sendButton.disabled = true;
            this.updateStatus('Generating response...', 'loading');

            const chatData = {
                message: message,
                agent_id: agentId,
                conversation_id: this.currentConversationId,
                temperature: parseFloat(this.temperatureSlider.value),
                max_tokens: parseInt(this.maxTokensSlider.value),
                system_prompt: this.systemPromptTextarea.value || null
            };

            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(chatData)
            });

            if (!response.ok) {
                throw new Error('Failed to get response from server');
            }

            await this.handleStreamingResponse(response);

        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('assistant', 'Error: ' + error.message);
            this.updateStatus('Error occurred', 'error');
        } finally {
            this.hideTypingIndicator();
            this.isStreaming = false;
            this.sendButton.disabled = false;
            this.updateStatus('Ready', 'success');
        }
    }

    async handleStreamingResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';
        
        // Create assistant message element
        const messageElement = this.createMessageElement('assistant', '');
        
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') {
                            return;
                        }

                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.content) {
                                assistantMessage += parsed.content;
                                messageElement.querySelector('.message-content').textContent = assistantMessage;
                                this.scrollToBottom();
                            } else if (parsed.conversation_id) {
                                this.currentConversationId = parsed.conversation_id;
                            } else if (parsed.error) {
                                throw new Error(parsed.error);
                            }
                        } catch (e) {
                            // Ignore parse errors for partial JSON
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Streaming error:', error);
            messageElement.querySelector('.message-content').textContent = 'Error: ' + error.message;
        }
    }

    showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = `
            <div class="dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
            <span class="ms-2">Assistant is typing...</span>
        `;
        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    addMessage(role, content) {
        const messageElement = this.createMessageElement(role, content);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        return messageElement;
    }

    createMessageElement(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const timestamp = new Date().toLocaleTimeString();
        messageDiv.innerHTML = `
            <div class="message-content">${content}</div>
            <div class="timestamp">${timestamp}</div>
        `;
        
        return messageDiv;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    async extractCode() {
        const lastAssistantMessage = this.getLastAssistantMessage();
        if (!lastAssistantMessage) {
            alert('No assistant messages to extract code from.');
            return;
        }

        try {
            const response = await fetch(`/api/code/extract?text=${encodeURIComponent(lastAssistantMessage)}`);
            const data = await response.json();
            
            this.currentFiles = data.files || [];
            this.displayCodeBlocks(data.code_blocks || []);
            this.displayFiles(this.currentFiles);
            
            // Switch to code tab
            document.querySelector('[data-bs-target="#codeTab"]').click();
            
        } catch (error) {
            console.error('Error extracting code:', error);
            alert('Error extracting code: ' + error.message);
        }
    }

    getLastAssistantMessage() {
        const assistantMessages = this.chatMessages.querySelectorAll('.message.assistant .message-content');
        if (assistantMessages.length > 0) {
            return assistantMessages[assistantMessages.length - 1].textContent;
        }
        return null;
    }

    displayCodeBlocks(codeBlocks) {
        if (codeBlocks.length > 0) {
            const firstBlock = codeBlocks[0];
            this.codeEditor.value = firstBlock.code;
            this.codeEditor.dataset.language = firstBlock.language;
        }
    }

    displayFiles(files) {
        this.filesList.innerHTML = '';
        
        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <div class="file-name">${file.name}</div>
                <div class="file-language">${file.language}</div>
            `;
            
            fileItem.addEventListener('click', () => {
                this.selectFile(index);
            });
            
            this.filesList.appendChild(fileItem);
        });
    }

    selectFile(index) {
        // Remove active class from all items
        this.filesList.querySelectorAll('.file-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to selected item
        this.filesList.children[index].classList.add('active');
        
        // Load file content
        const file = this.currentFiles[index];
        this.codeEditor.value = file.content;
        this.codeEditor.dataset.language = file.language;
    }

    async saveCurrentFile() {
        const content = this.codeEditor.value;
        if (!content.trim()) {
            alert('No content to save.');
            return;
        }

        const filename = prompt('Enter filename:');
        if (!filename) return;

        try {
            // Here you would implement file saving logic
            // For now, we'll just download the file
            this.downloadFile(filename, content);
            
        } catch (error) {
            console.error('Error saving file:', error);
            alert('Error saving file: ' + error.message);
        }
    }

    downloadFile(filename, content) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async updateConfiguration() {
        // This method can be extended to update agent/model configurations
        this.updateStatus('Configuration updated', 'success');
    }

    async applyConfiguration() {
        try {
            const agentId = this.agentSelect.value;
            if (!agentId) {
                alert('Please select an agent first.');
                return;
            }

            const promptData = {
                system_prompt: this.systemPromptTextarea.value,
                instructions: this.customInstructions.value
            };

            const response = await fetch(`/api/agents/${agentId}/prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(promptData)
            });

            if (response.ok) {
                this.updateStatus('Configuration applied successfully', 'success');
            } else {
                throw new Error('Failed to apply configuration');
            }

        } catch (error) {
            console.error('Error applying configuration:', error);
            this.updateStatus('Error applying configuration', 'error');
        }
    }

    clearChat() {
        this.chatMessages.innerHTML = '';
        this.currentConversationId = null;
        this.updateStatus('Chat cleared', 'success');
    }

    updateStatus(message, type) {
        this.statusIndicator.textContent = message;
        this.statusIndicator.className = `alert alert-${type === 'error' ? 'danger' : type === 'loading' ? 'warning' : 'success'}`;
    }
}

// Initialize the interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.advancedChat = new AdvancedChatInterface();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedChatInterface;
}
