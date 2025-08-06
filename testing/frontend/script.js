// TDX Chatbot Test Interface - JavaScript

class ChatInterface {
    constructor() {
        // Auto-detect API base URL based on current path
        this.apiBaseUrl = this.detectApiBaseUrl();
        this.sessionId = null;
        this.isConnected = false;
        this.isTyping = false;
        
        this.initializeElements();
        this.bindEvents();
        this.updateEnvironmentInfo();
        this.checkStatus();
        this.setupAutoResize();
        
        // Log detected configuration
        console.log('TDX Chatbot Interface initialized');
        console.log('API Base URL:', this.apiBaseUrl);
        console.log('Current Path:', window.location.pathname);
    }
    
    detectApiBaseUrl() {
        /**
         * Auto-detect the correct API base URL based on current location
         * - If running at /testing/, use /testing/api/test
         * - If running standalone, use /api/test
         */
        const currentPath = window.location.pathname;
        
        if (currentPath.startsWith('/testing')) {
            // Integrated mode: running at https://domain.com/testing/
            return '/testing/api/test';
        } else {
            // Standalone mode: running at https://domain.com/ (main_test.py server)
            return '/api/test';
        }
    }
    
    updateEnvironmentInfo() {
        /**
         * Update page title and info based on detected environment
         */
        const currentPath = window.location.pathname;
        const isIntegratedMode = currentPath.startsWith('/testing');
        
        // Update page elements to show environment
        const headerTitle = document.querySelector('.header-info h1');
        const sessionInfo = document.getElementById('sessionInfo');
        
        if (headerTitle) {
            if (isIntegratedMode) {
                headerTitle.textContent = 'TDX Chatbot Test (Integrated)';
            } else {
                headerTitle.textContent = 'TDX Chatbot Test (Standalone)';
            }
        }
        
        if (sessionInfo && !this.sessionId) {
            const mode = isIntegratedMode ? 'Integrated Mode' : 'Standalone Mode';
            sessionInfo.textContent = `${mode} - Iniciando...`;
        }
    }
    
    initializeElements() {
        console.log('🔍 Initializing elements...');
        
        // Main elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.statusBtn = document.getElementById('statusBtn');
        this.exportBtn = document.getElementById('exportBtn');
        
        // Status elements
        this.sessionInfo = document.getElementById('sessionInfo');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.charCount = document.getElementById('charCount');
        this.typingIndicator = document.getElementById('typingIndicator');
        
        // Modals
        this.statusModal = document.getElementById('statusModal');
        this.exportModal = document.getElementById('exportModal');
        this.statusModalContent = document.getElementById('statusModalContent');
        this.exportModalContent = document.getElementById('exportModalContent');
        
        // Toast container
        this.toastContainer = document.getElementById('toastContainer');
        
        // Log element availability
        console.log('📋 Element check:', {
            chatMessages: !!this.chatMessages,
            messageInput: !!this.messageInput,
            sendBtn: !!this.sendBtn,
            sessionInfo: !!this.sessionInfo,
            statusIndicator: !!this.statusIndicator
        });
        
        // Check if critical elements are missing
        if (!this.messageInput || !this.sendBtn) {
            console.error('❌ Critical elements missing!', {
                messageInput: !!this.messageInput,
                sendBtn: !!this.sendBtn
            });
        }
    }
    
    bindEvents() {
        // Send message events
        console.log('🔗 Binding events to elements:', {
            sendBtn: !!this.sendBtn,
            messageInput: !!this.messageInput
        });
        
        this.sendBtn.addEventListener('click', (e) => {
            console.log('🖱️ Send button clicked', {
                disabled: this.sendBtn.disabled,
                isConnected: this.isConnected,
                isTyping: this.isTyping
            });
            if (!this.sendBtn.disabled) {
                this.sendMessage();
            } else {
                console.log('🚫 Send button is disabled, not sending message');
            }
        });
        
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                console.log('⌨️ Enter key pressed, sending message');
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Input events
        this.messageInput.addEventListener('input', () => this.updateCharCount());
        this.messageInput.addEventListener('input', () => this.updateSendButton());
        
        // Action buttons
        this.resetBtn.addEventListener('click', () => this.resetConversation());
        this.statusBtn.addEventListener('click', () => this.showStatus());
        this.exportBtn.addEventListener('click', () => this.showExport());
        
        // Modal events
        document.getElementById('closeStatusModal').addEventListener('click', () => this.hideModal('statusModal'));
        document.getElementById('closeExportModal').addEventListener('click', () => this.hideModal('exportModal'));
        
        // Close modals on outside click
        this.statusModal.addEventListener('click', (e) => {
            if (e.target === this.statusModal) this.hideModal('statusModal');
        });
        this.exportModal.addEventListener('click', (e) => {
            if (e.target === this.exportModal) this.hideModal('exportModal');
        });
        
        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideModal('statusModal');
                this.hideModal('exportModal');
            }
        });
    }
    
    setupAutoResize() {
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
    }
    
    async checkStatus() {
        try {
            console.log('Checking status at:', `${this.apiBaseUrl}/status`);
            const response = await fetch(`${this.apiBaseUrl}/status`);
            const data = await response.json();
            console.log('Status response:', data);
            
            if (data.success) {
                this.isConnected = true;
                this.sessionId = data.session_id;
                this.updateSessionInfo(data);
                this.updateStatusIndicator('connected', 'Conectado');
                console.log('Connection established successfully');
                
                if (data.test_summary) {
                    this.showToast('Sesión de prueba cargada', 'success');
                }
            } else {
                this.handleConnectionError();
            }
        } catch (error) {
            console.error('Error checking status:', error);
            this.handleConnectionError();
        }
    }
    
    updateSessionInfo(data) {
        if (data.session_id) {
            this.sessionInfo.textContent = `Sesión: ${data.session_id.substring(0, 12)}...`;
        } else {
            this.sessionInfo.textContent = 'Sin sesión activa';
        }
    }
    
    updateStatusIndicator(status, text) {
        this.statusIndicator.className = `status-indicator ${status}`;
        this.statusIndicator.querySelector('span').textContent = text;
    }
    
    handleConnectionError() {
        this.isConnected = false;
        this.updateStatusIndicator('disconnected', 'Desconectado');
        this.sessionInfo.textContent = 'Error de conexión';
        this.showToast('Error de conexión con el servidor', 'error');
    }
    
    updateCharCount() {
        const length = this.messageInput.value.length;
        this.charCount.textContent = `${length}/1000`;
        
        if (length > 900) {
            this.charCount.style.color = '#f44336';
        } else if (length > 700) {
            this.charCount.style.color = '#ff9800';
        } else {
            this.charCount.style.color = '#666';
        }
    }
    
    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        const shouldDisable = !hasText || this.isTyping || !this.isConnected;
        this.sendBtn.disabled = shouldDisable;
        
        console.log('🔘 Send button update:', {
            hasText,
            isTyping: this.isTyping,
            isConnected: this.isConnected,
            disabled: shouldDisable
        });
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        console.log('🚀 sendMessage called with:', { message, isTyping: this.isTyping, isConnected: this.isConnected });
        
        if (!message || this.isTyping) {
            console.log('❌ sendMessage blocked:', { hasMessage: !!message, isTyping: this.isTyping });
            return;
        }
        
        // Force connection check if not connected
        if (!this.isConnected) {
            console.log('🔄 Not connected, checking status...');
            await this.checkStatus();
            if (!this.isConnected) {
                console.log('❌ Still not connected after status check');
                this.showToast('Error de conexión - verificando estado...', 'warning');
                return;
            }
        }
        
        console.log('✅ Proceeding to send message:', message);
        
        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.updateCharCount();
        this.updateSendButton();
        this.autoResize();
        
        // Show typing indicator
        this.showTyping();
        
        try {
            const fetchUrl = `${this.apiBaseUrl}/chat`;
            console.log('📤 Making fetch request to:', fetchUrl);
            console.log('📤 Request body:', JSON.stringify({ message }));
            
            const response = await fetch(fetchUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            console.log('📥 Response status:', response.status, response.statusText);
            console.log('📥 Response headers:', Object.fromEntries(response.headers.entries()));
            
            const data = await response.json();
            console.log('📥 Response data:', data);
            
            this.hideTyping();
            
            if (data.success && data.response) {
                console.log('✅ Success response, adding bot message');
                this.addMessage(data.response, 'bot');
                this.sessionId = data.session_id;
            } else {
                console.log('❌ Error in response data:', data);
                this.addMessage(data.error || 'Error procesando mensaje', 'error');
                this.showToast('Error enviando mensaje', 'error');
            }
        } catch (error) {
            console.error('❌ Fetch error:', error);
            console.error('❌ Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            this.hideTyping();
            this.addMessage('Error de conexión', 'error');
            this.showToast('Error de conexión', 'error');
        }
    }
    
    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        if (type === 'user') {
            avatar.innerHTML = '<i class=\"fas fa-user\"></i>';
        } else if (type === 'bot') {
            avatar.innerHTML = '<i class=\"fas fa-robot\"></i>';
        } else if (type === 'error') {
            avatar.innerHTML = '<i class=\"fas fa-exclamation-triangle\"></i>';
            messageDiv.className = 'bot-message error';
        }
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Format message content
        const formattedContent = this.formatMessage(content);
        messageContent.innerHTML = formattedContent;
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.className = 'message-time';
        timestamp.textContent = new Date().toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        messageContent.appendChild(timestamp);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // Basic formatting for better readability
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    }
    
    showTyping() {
        this.isTyping = true;
        this.typingIndicator.style.display = 'flex';
        this.updateSendButton();
        this.scrollToBottom();
    }
    
    hideTyping() {
        this.isTyping = false;
        this.typingIndicator.style.display = 'none';
        this.updateSendButton();
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
    
    autoResize() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
    }
    
    async resetConversation() {
        if (!confirm('¿Estás seguro de que quieres reiniciar la conversación? Se perderán todos los mensajes.')) {
            return;
        }
        
        try {
            this.updateStatusIndicator('connecting', 'Reiniciando...');
            
            const response = await fetch(`${this.apiBaseUrl}/reset`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear chat messages
                this.chatMessages.innerHTML = `
                    <div class=\"welcome-message\">
                        <div class=\"bot-message\">
                            <div class=\"message-avatar\">
                                <i class=\"fas fa-robot\"></i>
                            </div>
                            <div class=\"message-content\">
                                <p>Conversación reiniciada. Nueva sesión de prueba iniciada.</p>
                                <p>Envía un mensaje para comenzar a probar el flujo completo del agente.</p>
                            </div>
                        </div>
                    </div>
                `;
                
                this.sessionId = data.new_session_id;
                this.updateSessionInfo({ session_id: data.new_session_id });
                this.updateStatusIndicator('connected', 'Conectado');
                this.showToast('Conversación reiniciada', 'success');
            } else {
                this.showToast('Error reiniciando conversación', 'error');
                this.updateStatusIndicator('connected', 'Conectado');
            }
        } catch (error) {
            console.error('Error resetting conversation:', error);
            this.showToast('Error de conexión', 'error');
            this.updateStatusIndicator('connected', 'Conectado');
        }
    }
    
    async showStatus() {
        this.showModal('statusModal');
        this.statusModalContent.innerHTML = '<div class=\"loading\"><i class=\"fas fa-spinner fa-spin\"></i> Cargando estado...</div>';
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/status`);
            const data = await response.json();
            
            if (data.success) {
                this.renderStatusContent(data);
            } else {
                this.statusModalContent.innerHTML = '<p>Error cargando estado del sistema</p>';
            }
        } catch (error) {
            console.error('Error loading status:', error);
            this.statusModalContent.innerHTML = '<p>Error de conexión</p>';
        }
    }
    
    renderStatusContent(data) {
        const summary = data.test_summary || {};
        
        this.statusModalContent.innerHTML = `
            <div class=\"status-grid\">
                <div class=\"status-card\">
                    <h4>Estado</h4>
                    <p>${data.status}</p>
                </div>
                <div class=\"status-card\">
                    <h4>Sesión</h4>
                    <p>${data.session_id ? data.session_id.substring(0, 12) + '...' : 'N/A'}</p>
                </div>
                <div class=\"status-card\">
                    <h4>Duración</h4>
                    <p>${summary.duration || 'N/A'}</p>
                </div>
                <div class=\"status-card\">
                    <h4>Mensajes</h4>
                    <p>${summary.message_count || 0}</p>
                </div>
                <div class=\"status-card\">
                    <h4>Usuario</h4>
                    <p>${summary.user_messages || 0}</p>
                </div>
                <div class=\"status-card\">
                    <h4>Bot</h4>
                    <p>${summary.bot_messages || 0}</p>
                </div>
            </div>
            
            ${summary.data_collection_progress ? `
            <h4>Progreso de Recolección de Datos</h4>
            <div class=\"status-grid\">
                <div class=\"status-card\">
                    <h4>Email</h4>
                    <p>${summary.data_collection_progress.email ? '✅' : '❌'}</p>
                </div>
                <div class=\"status-card\">
                    <h4>Servicio</h4>
                    <p>${summary.data_collection_progress.service_interest ? '✅' : '❌'}</p>
                </div>
                <div class=\"status-card\">
                    <h4>Presupuesto</h4>
                    <p>${summary.data_collection_progress.budget_confirmed ? '✅' : '❌'}</p>
                </div>
                <div class=\"status-card\">
                    <h4>Reunión</h4>
                    <p>${summary.data_collection_progress.meeting_confirmed ? '✅' : '❌'}</p>
                </div>
            </div>
            
            <div class=\"status-card\">
                <h4>Etapa de Conversación</h4>
                <p>${this.formatStage(summary.conversation_stage)}</p>
            </div>
            ` : ''}
        `;
    }
    
    formatStage(stage) {
        const stages = {
            'initial_contact': 'Contacto Inicial',
            'contact_collection': 'Recolección de Contacto',
            'service_identified': 'Servicio Identificado',
            'budget_confirmed': 'Presupuesto Confirmado',
            'calendar_selection': 'Selección de Calendario',
            'meeting_scheduled': 'Reunión Programada'
        };
        return stages[stage] || stage;
    }
    
    async showExport() {
        this.showModal('exportModal');
        this.exportModalContent.innerHTML = '<div class=\"loading\"><i class=\"fas fa-spinner fa-spin\"></i> Preparando exportación...</div>';
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/debug/export`);
            const data = await response.json();
            
            this.renderExportContent(data);
        } catch (error) {
            console.error('Error loading export data:', error);
            this.exportModalContent.innerHTML = '<p>Error preparando exportación</p>';
        }
    }
    
    renderExportContent(data) {
        this.exportModalContent.innerHTML = `
            <div class=\"export-section\">
                <h4>Exportar Conversación</h4>
                <p>Descarga la conversación completa con todos los datos y métricas.</p>
                <button class=\"export-btn\" onclick=\"chatInterface.downloadExport()\">
                    <i class=\"fas fa-download\"></i>
                    Descargar JSON
                </button>
            </div>
            
            <div class=\"export-section\">
                <h4>Resumen Rápido</h4>
                <div class=\"status-grid\">
                    <div class=\"status-card\">
                        <h4>Mensajes</h4>
                        <p>${data.message_count || 0}</p>
                    </div>
                    <div class=\"status-card\">
                        <h4>Duración</h4>
                        <p>${data.session_duration || 'N/A'}</p>
                    </div>
                </div>
            </div>
        `;
        
        // Store export data for download
        this.exportData = data;
    }
    
    downloadExport() {
        if (!this.exportData) return;
        
        const blob = new Blob([JSON.stringify(this.exportData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tdx-chatbot-test-${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showToast('Conversación exportada', 'success');
        this.hideModal('exportModal');
    }
    
    showModal(modalId) {
        document.getElementById(modalId).classList.add('show');
    }
    
    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('show');
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        }[type] || 'fa-info-circle';
        
        toast.innerHTML = `
            <i class=\"fas ${icon}\"></i>
            <span>${message}</span>
        `;
        
        this.toastContainer.appendChild(toast);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }
}

// Initialize the chat interface when the page loads
let chatInterface;
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 DOMContentLoaded - Initializing chat interface');
    chatInterface = new ChatInterface();
    // Make chatInterface globally available for button clicks after initialization
    window.chatInterface = chatInterface;
    console.log('✅ Chat interface initialized and made globally available');
});
