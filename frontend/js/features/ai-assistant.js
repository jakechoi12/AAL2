/**
 * AAL AI Assistant - Sidebar Chat Component
 * 사이드바 형태의 AI 채팅 컴포넌트
 * 
 * Usage:
 *   AIAssistant.init();  // 초기화
 *   AIAssistant.open();  // 채팅창 열기
 *   AIAssistant.close(); // 채팅창 닫기
 *   AIAssistant.toggle(); // 토글
 */

const AIAssistant = (function() {
    // Configuration
    const API_BASE = 'http://localhost:5000';
    
    // State
    let isInitialized = false;
    let isOpen = false;
    let isLoading = false;
    let sessionId = null;
    
    // Elements
    let container = null;
    let messagesEl = null;
    let inputEl = null;
    let sendBtn = null;
    let toggleBtn = null;
    
    // Get or create session ID
    function getSessionId() {
        if (!sessionId) {
            sessionId = sessionStorage.getItem('ai_session_id');
            if (!sessionId) {
                sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                sessionStorage.setItem('ai_session_id', sessionId);
            }
        }
        return sessionId;
    }
    
    // Create sidebar HTML
    function createSidebarHTML() {
        return `
            <div class="ai-sidebar" id="ai-sidebar">
                <div class="ai-sidebar-header">
                    <div class="ai-sidebar-title">
                        <i class="fas fa-robot"></i>
                        <span>AAL Assistant</span>
                    </div>
                    <button class="ai-sidebar-close" onclick="AIAssistant.close()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="ai-sidebar-messages" id="ai-sidebar-messages">
                    <div class="ai-message ai">
                        안녕하세요! 무엇을 도와드릴까요?
                    </div>
                </div>
                
                <div class="ai-sidebar-input">
                    <textarea 
                        class="ai-input" 
                        id="ai-sidebar-input" 
                        placeholder="메시지 입력..." 
                        rows="1"
                    ></textarea>
                    <button class="ai-send-btn" id="ai-sidebar-send">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
            
            <button class="ai-toggle-btn" id="ai-toggle-btn" onclick="AIAssistant.toggle()">
                <i class="fas fa-robot"></i>
            </button>
        `;
    }
    
    // Create styles
    function createStyles() {
        const style = document.createElement('style');
        style.id = 'ai-assistant-styles';
        style.textContent = `
            .ai-sidebar {
                position: fixed;
                right: -400px;
                top: 0;
                width: 380px;
                height: 100vh;
                background: #111827;
                border-left: 1px solid #1f2937;
                display: flex;
                flex-direction: column;
                z-index: 9999;
                transition: right 0.3s ease;
                box-shadow: -4px 0 20px rgba(0,0,0,0.3);
            }
            
            .ai-sidebar.open {
                right: 0;
            }
            
            .ai-sidebar-header {
                padding: 1rem;
                border-bottom: 1px solid #1f2937;
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: #0d1117;
            }
            
            .ai-sidebar-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                color: #f3f4f6;
            }
            
            .ai-sidebar-title i {
                font-size: 1.25rem;
                color: #3b82f6;
            }
            
            .ai-sidebar-close {
                background: none;
                border: none;
                color: #6b7280;
                font-size: 1.25rem;
                cursor: pointer;
                padding: 4px;
                transition: color 0.2s;
            }
            
            .ai-sidebar-close:hover {
                color: #f3f4f6;
            }
            
            .ai-sidebar-messages {
                flex: 1;
                overflow-y: auto;
                padding: 1rem;
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }
            
            .ai-message {
                max-width: 85%;
                padding: 0.75rem 1rem;
                border-radius: 12px;
                font-size: 0.9rem;
                line-height: 1.5;
                animation: aiFadeIn 0.3s ease;
            }
            
            @keyframes aiFadeIn {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .ai-message.ai {
                background: #1f2937;
                border: 1px solid #374151;
                align-self: flex-start;
                color: #e5e7eb;
            }
            
            .ai-message.user {
                background: #1e40af;
                align-self: flex-end;
                color: white;
            }
            
            .ai-message.typing {
                display: flex;
                gap: 4px;
                padding: 0.75rem 1.25rem;
            }
            
            .ai-message.typing span {
                width: 6px;
                height: 6px;
                background: #6b7280;
                border-radius: 50%;
                animation: aiTyping 1.4s infinite;
            }
            
            .ai-message.typing span:nth-child(2) { animation-delay: 0.2s; }
            .ai-message.typing span:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes aiTyping {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-6px); }
            }
            
            .ai-sidebar-input {
                padding: 1rem;
                border-top: 1px solid #1f2937;
                display: flex;
                gap: 8px;
                background: #0d1117;
            }
            
            .ai-input {
                flex: 1;
                padding: 0.625rem 0.875rem;
                background: #1f2937;
                border: 1px solid #374151;
                border-radius: 8px;
                color: #f3f4f6;
                font-size: 0.9rem;
                resize: none;
                outline: none;
                max-height: 100px;
            }
            
            .ai-input:focus {
                border-color: #3b82f6;
            }
            
            .ai-send-btn {
                width: 40px;
                height: 40px;
                background: #3b82f6;
                border: none;
                border-radius: 8px;
                color: white;
                cursor: pointer;
                transition: background 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .ai-send-btn:hover {
                background: #2563eb;
            }
            
            .ai-send-btn:disabled {
                background: #374151;
                cursor: not-allowed;
            }
            
            .ai-toggle-btn {
                position: fixed;
                right: 24px;
                bottom: 24px;
                width: 56px;
                height: 56px;
                background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                border: none;
                border-radius: 50%;
                color: white;
                font-size: 1.5rem;
                cursor: pointer;
                z-index: 9998;
                box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
                transition: transform 0.2s, box-shadow 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .ai-toggle-btn:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 25px rgba(59, 130, 246, 0.5);
            }
            
            .ai-toggle-btn.hidden {
                display: none;
            }
            
            /* Quote card in sidebar */
            .ai-quote-card {
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 8px;
                padding: 0.75rem;
                margin-top: 0.5rem;
                font-size: 0.8rem;
            }
            
            .ai-quote-card-header {
                display: flex;
                align-items: center;
                gap: 6px;
                color: #10b981;
                font-weight: 600;
                margin-bottom: 0.5rem;
            }
            
            .ai-quote-card-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.25rem;
            }
            
            .ai-quote-card-item {
                color: #9ca3af;
            }
            
            .ai-quote-card-item strong {
                color: #e5e7eb;
            }
            
            .ai-quote-action {
                width: 100%;
                margin-top: 0.5rem;
                padding: 0.5rem;
                background: #10b981;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 0.8rem;
                font-weight: 500;
                cursor: pointer;
            }
            
            .ai-quote-action:hover {
                background: #059669;
            }
            
            @media (max-width: 480px) {
                .ai-sidebar {
                    width: 100%;
                    right: -100%;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Initialize
    function init() {
        if (isInitialized) return;
        
        // Create styles
        createStyles();
        
        // Create container
        container = document.createElement('div');
        container.id = 'ai-assistant-container';
        container.innerHTML = createSidebarHTML();
        document.body.appendChild(container);
        
        // Get elements
        messagesEl = document.getElementById('ai-sidebar-messages');
        inputEl = document.getElementById('ai-sidebar-input');
        sendBtn = document.getElementById('ai-sidebar-send');
        toggleBtn = document.getElementById('ai-toggle-btn');
        
        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        inputEl.addEventListener('keydown', handleKeyDown);
        inputEl.addEventListener('input', autoResize);
        
        // Restore conversation from sessionStorage
        restoreConversation();
        
        isInitialized = true;
        console.log('[AI Assistant] Initialized');
    }
    
    // Auto resize textarea
    function autoResize() {
        inputEl.style.height = 'auto';
        inputEl.style.height = Math.min(inputEl.scrollHeight, 100) + 'px';
    }
    
    // Handle key down
    function handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    }
    
    // Send message
    async function sendMessage() {
        const message = inputEl.value.trim();
        if (!message || isLoading) return;
        
        // Clear input
        inputEl.value = '';
        inputEl.style.height = 'auto';
        
        // Add user message
        addMessage(message, 'user');
        saveMessage(message, 'user');
        
        // Show typing
        const typingId = showTyping();
        setLoading(true);
        
        try {
            const response = await fetch(`${API_BASE}/api/ai/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: getSessionId(),
                    message: message
                })
            });
            
            const data = await response.json();
            removeTyping(typingId);
            
            if (data.success) {
                addMessage(data.message, 'ai', data.quote_data);
                saveMessage(data.message, 'ai', data.quote_data);
            } else {
                addMessage(data.message || '오류가 발생했습니다.', 'ai');
            }
            
        } catch (error) {
            console.error('[AI Assistant] Error:', error);
            removeTyping(typingId);
            addMessage('서버에 연결할 수 없습니다.', 'ai');
        }
        
        setLoading(false);
    }
    
    // Add message to chat
    function addMessage(text, type, quoteData = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ${type}`;
        
        // Format text
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        
        messageDiv.innerHTML = formattedText;
        
        // Add quote card if data exists
        if (quoteData && type === 'ai') {
            messageDiv.appendChild(createQuoteCard(quoteData));
        }
        
        messagesEl.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Create quote card
    function createQuoteCard(data) {
        const card = document.createElement('div');
        card.className = 'ai-quote-card';
        card.innerHTML = `
            <div class="ai-quote-card-header">
                <i class="fas fa-check-circle"></i> 견적 준비 완료
            </div>
            <div class="ai-quote-card-grid">
                <div class="ai-quote-card-item">POL: <strong>${data.pol || '-'}</strong></div>
                <div class="ai-quote-card-item">POD: <strong>${data.pod || '-'}</strong></div>
                <div class="ai-quote-card-item">Type: <strong>${data.container_type || '-'}</strong></div>
                <div class="ai-quote-card-item">ETD: <strong>${data.etd || '-'}</strong></div>
            </div>
            <button class="ai-quote-action" onclick="AIAssistant.goToQuotation('${encodeURIComponent(JSON.stringify(data))}')">
                견적 조회 페이지로 이동
            </button>
        `;
        return card;
    }
    
    // Navigate to quotation page
    function goToQuotation(encodedData) {
        const data = JSON.parse(decodeURIComponent(encodedData));
        sessionStorage.setItem('ai_quote_data', JSON.stringify(data));
        window.location.href = '/pages/quotation.html?from=ai';
    }
    
    // Show typing indicator
    function showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'ai-message ai typing';
        typingDiv.id = 'ai-typing-' + Date.now();
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        messagesEl.appendChild(typingDiv);
        scrollToBottom();
        return typingDiv.id;
    }
    
    // Remove typing indicator
    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
    
    // Set loading state
    function setLoading(loading) {
        isLoading = loading;
        sendBtn.disabled = loading;
    }
    
    // Scroll to bottom
    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }
    
    // Save message to sessionStorage
    function saveMessage(text, type, quoteData = null) {
        let history = JSON.parse(sessionStorage.getItem('ai_history') || '[]');
        history.push({ text, type, quoteData, timestamp: Date.now() });
        // Keep only last 50 messages
        if (history.length > 50) history = history.slice(-50);
        sessionStorage.setItem('ai_history', JSON.stringify(history));
    }
    
    // Restore conversation from sessionStorage
    function restoreConversation() {
        const history = JSON.parse(sessionStorage.getItem('ai_history') || '[]');
        if (history.length > 0) {
            // Clear default message
            messagesEl.innerHTML = '';
            history.forEach(msg => {
                addMessage(msg.text, msg.type, msg.quoteData);
            });
        }
    }
    
    // Open sidebar
    function open() {
        const sidebar = document.getElementById('ai-sidebar');
        sidebar.classList.add('open');
        toggleBtn.classList.add('hidden');
        isOpen = true;
        inputEl.focus();
    }
    
    // Close sidebar
    function close() {
        const sidebar = document.getElementById('ai-sidebar');
        sidebar.classList.remove('open');
        toggleBtn.classList.remove('hidden');
        isOpen = false;
    }
    
    // Toggle sidebar
    function toggle() {
        if (isOpen) {
            close();
        } else {
            open();
        }
    }
    
    // Clear conversation
    function clearConversation() {
        sessionStorage.removeItem('ai_history');
        sessionStorage.removeItem('ai_session_id');
        sessionId = null;
        messagesEl.innerHTML = '<div class="ai-message ai">안녕하세요! 무엇을 도와드릴까요?</div>';
    }
    
    // Public API
    return {
        init,
        open,
        close,
        toggle,
        goToQuotation,
        clearConversation,
        isOpen: () => isOpen
    };
})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize on all pages (sidebar chat)
    AIAssistant.init();
});
