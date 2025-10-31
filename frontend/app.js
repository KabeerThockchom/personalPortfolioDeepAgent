// WebSocket connection and chat UI management
class ChatApp {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.isConnected = false;
        this.pendingApprovals = [];
        this.currentMessageId = null;
        
        this.initializeElements();
        this.initializeEventListeners();
        this.connect();
    }

    initializeElements() {
        this.chatContainer = document.getElementById('chatContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.clearBtn = document.getElementById('clearBtn');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.sessionIdSpan = document.getElementById('sessionId');
        this.welcomeMessage = document.getElementById('welcomeMessage');
        this.approvalModal = document.getElementById('approvalModal');
        this.approvalBody = document.getElementById('approvalBody');
    }

    initializeEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter (Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
        });

        // Clear history
        this.clearBtn.addEventListener('click', () => this.clearHistory());
    }

    connect() {
        // Determine WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/chat`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.isConnected = true;
            this.updateConnectionStatus('connected', 'Connected');
            this.sendButton.disabled = false;
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus('disconnected', 'Connection Error');
        };

        this.ws.onclose = () => {
            this.isConnected = false;
            this.updateConnectionStatus('disconnected', 'Disconnected');
            this.sendButton.disabled = true;
            
            // Attempt to reconnect after 3 seconds
            setTimeout(() => this.connect(), 3000);
        };
    }

    updateConnectionStatus(status, text) {
        this.statusDot.className = `status-dot ${status}`;
        this.statusText.textContent = text;
    }

    handleMessage(data) {
        switch (data.type) {
            case 'connected':
                this.sessionId = data.session_id;
                this.sessionIdSpan.textContent = this.sessionId.substring(0, 8) + '...';
                if (this.welcomeMessage) {
                    this.welcomeMessage.style.display = 'none';
                }
                break;

            case 'thinking':
                this.showThinking(data.node);
                break;

            case 'tool_call':
                this.showToolCall(data);
                break;

            case 'tool_result':
                this.showToolResult(data);
                break;

            case 'subagent_spawn':
                this.showSubagentSpawn(data);
                break;

            case 'subagent_complete':
                this.showSubagentComplete(data);
                break;

            case 'message':
                this.showMessage(data.content, 'assistant');
                break;

            case 'file_update':
                this.showFileUpdate(data.paths);
                break;

            case 'todo_update':
                this.showTodoUpdate(data.todos);
                break;

            case 'approval_request':
                this.showApprovalRequest(data.action_requests);
                break;

            case 'complete':
                this.hideThinking();
                break;

            case 'error':
                this.showError(data.error, data.details);
                break;

            default:
                console.log('Unknown event type:', data.type, data);
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.isConnected) return;

        // Add user message to chat
        this.showMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // Hide welcome message
        if (this.welcomeMessage) {
            this.welcomeMessage.style.display = 'none';
        }

        // Send to server
        this.ws.send(JSON.stringify({
            type: 'message',
            content: message
        }));
    }

    showMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? '👤' : '🤖';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        // Format content (support markdown-style code blocks)
        if (content.includes('```')) {
            const parts = content.split('```');
            parts.forEach((part, index) => {
                if (index % 2 === 0) {
                    bubble.appendChild(document.createTextNode(part));
                } else {
                    const codeBlock = document.createElement('pre');
                    codeBlock.textContent = part;
                    bubble.appendChild(codeBlock);
                }
            });
        } else {
            bubble.textContent = content;
        }
        
        contentDiv.appendChild(bubble);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showThinking(node) {
        // Remove existing thinking indicator
        this.hideThinking();
        
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'thinking';
        thinkingDiv.id = 'thinkingIndicator';
        
        const text = document.createElement('span');
        text.textContent = `💭 Thinking...`;
        
        const dots = document.createElement('div');
        dots.className = 'thinking-dots';
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'thinking-dot';
            dots.appendChild(dot);
        }
        
        thinkingDiv.appendChild(text);
        thinkingDiv.appendChild(dots);
        this.chatContainer.appendChild(thinkingDiv);
        this.scrollToBottom();
    }

    hideThinking() {
        const thinking = document.getElementById('thinkingIndicator');
        if (thinking) {
            thinking.remove();
        }
    }

    showToolCall(data) {
        this.hideThinking();
        
        const toolDiv = document.createElement('div');
        toolDiv.className = `tool-call ${data.is_subagent_spawn ? 'subagent' : ''}`;
        toolDiv.id = `tool-${data.tool_call_id}`;
        
        const header = document.createElement('div');
        header.className = 'tool-call-header';
        
        const icon = data.is_subagent_spawn ? '🚀' : '🔧';
        header.innerHTML = `${icon} <strong>${this.formatToolName(data.tool_name)}</strong>`;
        if (data.subagent_name) {
            header.innerHTML += ` <span style="color: var(--warning-color);">(${data.subagent_name})</span>`;
        }
        
        const args = document.createElement('div');
        args.className = 'tool-args';
        args.textContent = JSON.stringify(data.args, null, 2);
        
        toolDiv.appendChild(header);
        toolDiv.appendChild(args);
        
        this.chatContainer.appendChild(toolDiv);
        this.scrollToBottom();
    }

    showToolResult(data) {
        const toolDiv = document.getElementById(`tool-${data.tool_call_id}`);
        if (!toolDiv) return;

        const resultDiv = document.createElement('div');
        resultDiv.className = `tool-result ${data.success === false ? 'error' : ''}`;
        
        const header = document.createElement('div');
        header.className = 'tool-call-header';
        header.innerHTML = `${data.success === false ? '❌' : '✓'} Result`;
        
        const content = document.createElement('div');
        content.className = 'tool-result-content';
        
        // Try to parse and format JSON results
        let parsedResult = null;
        try {
            parsedResult = JSON.parse(data.result);
            content.textContent = JSON.stringify(parsedResult, null, 2);
        } catch {
            content.textContent = data.result;
        }
        
        // If result contains file_path, show actual disk location
        if (parsedResult && parsedResult.file_path) {
            const fileInfo = document.createElement('div');
            fileInfo.style.marginTop = '0.75rem';
            fileInfo.style.padding = '0.75rem';
            fileInfo.style.background = 'rgba(37, 99, 235, 0.1)';
            fileInfo.style.borderRadius = '6px';
            fileInfo.style.borderLeft = '3px solid var(--primary-color)';
            fileInfo.style.fontSize = '0.875rem';
            
            const virtualPath = parsedResult.file_path;
            const actualPath = `sessions/${this.sessionId}/${virtualPath}`;
            
            fileInfo.innerHTML = `
                <strong>📁 File saved:</strong><br>
                <span style="font-family: monospace; color: var(--primary-color);">Virtual: ${virtualPath}</span><br>
                <span style="font-family: monospace; color: var(--text-secondary);">Actual: ${actualPath}</span>
            `;
            
            content.appendChild(fileInfo);
        }
        
        resultDiv.appendChild(header);
        resultDiv.appendChild(content);
        toolDiv.appendChild(resultDiv);
        this.scrollToBottom();
    }

    showSubagentSpawn(data) {
        const spawnDiv = document.createElement('div');
        spawnDiv.className = 'tool-call subagent';
        spawnDiv.innerHTML = `
            <div class="tool-call-header">
                🚀 Spawning Subagent: <strong>${data.name}</strong>
            </div>
            <div class="tool-args">${this.escapeHtml(data.description)}</div>
        `;
        this.chatContainer.appendChild(spawnDiv);
        this.scrollToBottom();
    }

    showSubagentComplete(data) {
        const completeDiv = document.createElement('div');
        completeDiv.className = 'tool-call subagent';
        completeDiv.innerHTML = `
            <div class="tool-call-header">
                ✓ Subagent Complete: <strong>${data.name}</strong>
            </div>
        `;
        this.chatContainer.appendChild(completeDiv);
        this.scrollToBottom();
    }

    showFileUpdate(paths) {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'file-update';
        
        let content = `<strong>📁 Files updated:</strong><br>`;
        paths.forEach(path => {
            // Show virtual path
            content += `<span style="font-family: monospace; color: var(--primary-color);">${path}</span>`;
            
            // Show actual disk location if session ID is available
            if (this.sessionId) {
                let actualPath = '';
                if (path.startsWith('/financial_data/')) {
                    actualPath = `sessions/${this.sessionId}/financial_data/${path.replace('/financial_data/', '')}`;
                } else if (path.startsWith('/reports/')) {
                    actualPath = `sessions/${this.sessionId}/reports/${path.replace('/reports/', '')}`;
                } else {
                    actualPath = `(virtual path in session state)`;
                }
                content += `<br><span style="font-family: monospace; color: var(--text-secondary); font-size: 0.8em;">  → ${actualPath}</span>`;
            }
            content += '<br>';
        });
        
        fileDiv.innerHTML = content;
        this.chatContainer.appendChild(fileDiv);
        this.scrollToBottom();
    }

    showTodoUpdate(todos) {
        const todoDiv = document.createElement('div');
        todoDiv.className = 'todo-update';
        
        todos.slice(0, 5).forEach(todo => {
            const item = document.createElement('div');
            item.className = `todo-item ${todo.status || 'pending'}`;
            item.textContent = todo.content || JSON.stringify(todo);
            todoDiv.appendChild(item);
        });
        
        if (todos.length > 5) {
            const more = document.createElement('div');
            more.textContent = `... and ${todos.length - 5} more`;
            more.style.fontSize = '0.8rem';
            more.style.color = 'var(--text-secondary)';
            more.style.marginTop = '0.5rem';
            todoDiv.appendChild(more);
        }
        
        this.chatContainer.appendChild(todoDiv);
        this.scrollToBottom();
    }

    showApprovalRequest(actionRequests) {
        this.pendingApprovals = actionRequests;
        this.approvalBody.innerHTML = '';
        
        actionRequests.forEach((request, index) => {
            const requestDiv = document.createElement('div');
            requestDiv.className = 'approval-request';
            
            const title = document.createElement('h3');
            title.textContent = `Request ${index + 1}: ${request.name || 'Unknown Tool'}`;
            
            const details = document.createElement('div');
            details.className = 'approval-request-details';
            details.textContent = JSON.stringify(request.args || {}, null, 2);
            
            const buttons = document.createElement('div');
            buttons.className = 'approval-buttons';
            
            const allowedDecisions = request.allowed_decisions || ['approve', 'reject'];
            
            if (allowedDecisions.includes('approve')) {
                const approveBtn = document.createElement('button');
                approveBtn.className = 'approval-btn approve';
                approveBtn.textContent = 'Approve';
                approveBtn.onclick = () => this.sendApprovalDecision(index, 'approve');
                buttons.appendChild(approveBtn);
            }
            
            if (allowedDecisions.includes('reject')) {
                const rejectBtn = document.createElement('button');
                rejectBtn.className = 'approval-btn reject';
                rejectBtn.textContent = 'Reject';
                rejectBtn.onclick = () => this.sendApprovalDecision(index, 'reject');
                buttons.appendChild(rejectBtn);
            }
            
            requestDiv.appendChild(title);
            requestDiv.appendChild(details);
            requestDiv.appendChild(buttons);
            this.approvalBody.appendChild(requestDiv);
        });
        
        this.approvalModal.style.display = 'flex';
    }

    sendApprovalDecision(requestIndex, decision) {
        const decisions = this.pendingApprovals.map((_, index) => ({
            type: index === requestIndex ? decision : 'approve' // Default others to approve
        }));
        
        // Close modal
        this.approvalModal.style.display = 'none';
        
        // Send decisions to server
        this.ws.send(JSON.stringify({
            type: 'approval_response',
            decisions: decisions
        }));
        
        // Show message about decision
        this.showMessage(`✅ ${decision === 'approve' ? 'Approved' : 'Rejected'} action request ${requestIndex + 1}`, 'assistant');
    }

    showError(error, details) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <strong>❌ Error:</strong> ${this.escapeHtml(error)}
            ${details ? `<br><small>${this.escapeHtml(details)}</small>` : ''}
        `;
        this.chatContainer.appendChild(errorDiv);
        this.scrollToBottom();
    }

    clearHistory() {
        if (confirm('Clear conversation history?')) {
            this.chatContainer.innerHTML = '';
            if (this.welcomeMessage) {
                this.welcomeMessage.style.display = 'block';
            }
            // Note: This clears UI only. Server-side clearing would require an API call.
        }
    }

    formatToolName(toolName) {
        // Convert snake_case to Title Case
        return toolName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }
}

// Close approval modal when clicking outside
window.closeApprovalModal = function() {
    document.getElementById('approvalModal').style.display = 'none';
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});

