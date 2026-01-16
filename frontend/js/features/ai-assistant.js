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
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 8px;
                padding: 0.75rem;
                margin-top: 0.5rem;
                font-size: 0.8rem;
            }
            
            .ai-quote-card.ai-quote-success {
                background: rgba(16, 185, 129, 0.15);
                border: 1px solid rgba(16, 185, 129, 0.4);
            }
            
            .ai-quote-card-header {
                display: flex;
                align-items: center;
                gap: 6px;
                color: #3b82f6;
                font-weight: 600;
                margin-bottom: 0.5rem;
            }
            
            .ai-quote-card-header.success {
                color: #10b981;
                font-size: 0.9rem;
            }
            
            .ai-quote-card-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.25rem;
            }
            
            .ai-quote-card-info {
                display: flex;
                flex-direction: column;
                gap: 0.25rem;
                margin-bottom: 0.5rem;
            }
            
            .ai-quote-card-info .ai-quote-card-item {
                display: flex;
                justify-content: space-between;
            }
            
            .ai-quote-card-route {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 0.5rem;
                background: rgba(255,255,255,0.05);
                border-radius: 4px;
                margin-bottom: 0.5rem;
                color: #e5e7eb;
                font-weight: 500;
            }
            
            .ai-quote-card-route i {
                color: #10b981;
            }
            
            .ai-quote-card-pickup {
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 0.4rem 0.6rem;
                background: rgba(251, 191, 36, 0.15);
                border-radius: 4px;
                color: #fbbf24;
                font-size: 0.75rem;
                margin-bottom: 0.5rem;
            }
            
            .ai-quote-card-item {
                color: #9ca3af;
            }
            
            .ai-quote-card-item span {
                color: #6b7280;
            }
            
            .ai-quote-card-item strong {
                color: #e5e7eb;
            }
            
            .ai-quote-action {
                width: 100%;
                margin-top: 0.5rem;
                padding: 0.5rem;
                background: #3b82f6;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 0.8rem;
                font-weight: 500;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
            }
            
            .ai-quote-action:hover {
                background: #2563eb;
            }
            
            .ai-quote-action.success {
                background: #10b981;
            }
            
            .ai-quote-action.success:hover {
                background: #059669;
            }
            
            /* 견적 준비 완료 카드 스타일 */
            .ai-quote-card.ai-quote-ready {
                background: rgba(251, 191, 36, 0.1);
                border: 1px solid rgba(251, 191, 36, 0.3);
            }
            
            .ai-quote-card-header.ready {
                color: #fbbf24;
            }
            
            .ai-quote-card-customer {
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 0.4rem 0.6rem;
                background: rgba(59, 130, 246, 0.15);
                border-radius: 4px;
                color: #60a5fa;
                font-size: 0.75rem;
                margin-bottom: 0.5rem;
            }
            
            .ai-quote-card-buttons {
                display: flex;
                gap: 8px;
                margin-top: 0.75rem;
            }
            
            .ai-quote-card-buttons .ai-quote-action {
                flex: 1;
                margin-top: 0;
            }
            
            .ai-quote-action.primary {
                background: linear-gradient(135deg, #10b981, #059669);
                font-weight: 600;
            }
            
            .ai-quote-action.primary:hover {
                background: linear-gradient(135deg, #059669, #047857);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            }
            
            .ai-quote-action.secondary {
                background: #374151;
                color: #9ca3af;
            }
            
            .ai-quote-action.secondary:hover {
                background: #4b5563;
                color: #e5e7eb;
            }
            
            .ai-quote-action.full-width {
                width: 100%;
                margin-top: 0.75rem;
                padding: 0.75rem;
                font-size: 0.9rem;
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
    
    // Create quote card - 견적 생성 완료 또는 준비 상태에 따라 다른 카드 표시
    function createQuoteCard(data) {
        const card = document.createElement('div');
        
        // 견적 생성이 완료된 경우 (request_number, bidding_no 존재)
        if (data.request_number && data.bidding_no) {
            card.className = 'ai-quote-card ai-quote-success';
            card.innerHTML = `
                <div class="ai-quote-card-header success">
                    <i class="fas fa-check-circle"></i> 견적 요청 완료!
                </div>
                <div class="ai-quote-card-info">
                    <div class="ai-quote-card-item"><span>요청번호:</span> <strong>${data.request_number}</strong></div>
                    <div class="ai-quote-card-item"><span>비딩번호:</span> <strong>${data.bidding_no}</strong></div>
                    <div class="ai-quote-card-item"><span>입찰마감:</span> <strong>${data.deadline || '-'}</strong></div>
                </div>
                <div class="ai-quote-card-route">
                    <span>${data.pol || '-'}</span>
                    <i class="fas fa-arrow-right"></i>
                    <span>${data.pod || '-'}</span>
                </div>
                <button class="ai-quote-action success" onclick="AIAssistant.goToBidding('${data.bidding_no}')">
                    <i class="fas fa-gavel"></i> 비딩 현황 보기
                </button>
            `;
        } else {
            // 견적 준비 완료 (아직 생성 안됨) - 버튼 2개: 즉시 요청 / 수정 후 요청
            card.className = 'ai-quote-card ai-quote-ready';
            const shippingTypeKo = {'ocean': '해상', 'air': '항공', 'truck': '육상'}[data.shipping_type] || data.shipping_type;
            const loadType = data.load_type || '-';
            const encodedData = encodeURIComponent(JSON.stringify(data));
            
            card.innerHTML = `
                <div class="ai-quote-card-header ready">
                    <i class="fas fa-clipboard-check"></i> 견적 요청 준비 완료
                </div>
                <div class="ai-quote-card-grid">
                    <div class="ai-quote-card-item">운송: <strong>${shippingTypeKo}</strong></div>
                    <div class="ai-quote-card-item">ETD: <strong>${data.etd || '-'}</strong></div>
                    <div class="ai-quote-card-item">POL: <strong>${data.pol || '-'}</strong></div>
                    <div class="ai-quote-card-item">ETA: <strong>${data.eta || '-'}</strong></div>
                    <div class="ai-quote-card-item">POD: <strong>${data.pod || '-'}</strong></div>
                    <div class="ai-quote-card-item">송장: <strong>${data.invoice_value_usd ? '$' + data.invoice_value_usd : '-'}</strong></div>
                    ${data.incoterms ? `<div class="ai-quote-card-item">조건: <strong>${data.incoterms}</strong></div>` : ''}
                    ${data.cargo_weight_kg ? `<div class="ai-quote-card-item">중량: <strong>${data.cargo_weight_kg}kg</strong></div>` : ''}
                </div>
                ${data.pickup_required ? `<div class="ai-quote-card-pickup"><i class="fas fa-truck-pickup"></i> 픽업: ${data.pickup_address || '예'}</div>` : ''}
                ${data.customer_company ? `<div class="ai-quote-card-customer"><i class="fas fa-building"></i> ${data.customer_company} (${data.customer_name})</div>` : ''}
                <button class="ai-quote-action primary full-width" onclick="AIAssistant.submitQuoteRequest('${encodedData}')">
                    <i class="fas fa-paper-plane"></i> 견적 요청하기
                </button>
            `;
        }
        return card;
    }
    
    // Navigate to bidding page
    function goToBidding(biddingNo) {
        window.location.href = `/pages/shipper-bidding.html?bidding=${biddingNo}`;
    }
    
    // Navigate to quotation page
    function goToQuotation(encodedData) {
        const data = JSON.parse(decodeURIComponent(encodedData));
        sessionStorage.setItem('ai_quote_data', JSON.stringify(data));
        window.location.href = '/pages/quotation.html?from=ai';
    }
    
    // Submit quote request - quotation 페이지로 이동 후 자동 Submit
    function submitQuoteRequest(encodedData) {
        const data = JSON.parse(decodeURIComponent(encodedData));
        
        // auto_submit 플래그 추가하여 sessionStorage에 저장
        sessionStorage.setItem('ai_quote_data', JSON.stringify({
            ...data,
            auto_submit: true
        }));
        
        // 메시지 저장 (페이지 이동 후에도 대화 유지)
        const navMsg = `📋 **견적 요청 페이지로 이동합니다.**\n\n수집된 정보를 자동 입력하고 견적 요청을 진행합니다...`;
        addMessage(navMsg, 'ai');
        saveMessage(navMsg, 'ai');
        
        // quotation 페이지로 이동
        setTimeout(() => {
            window.location.href = '/pages/quotation.html?from=ai&auto=true';
        }, 500);
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
    
    // Save message to sessionStorage (메인페이지와 공유하는 키 사용)
    function saveMessage(text, type, quoteData = null) {
        let history = JSON.parse(sessionStorage.getItem('ai_conversation') || '[]');
        // 메인페이지와 호환되는 형식 (role, content)
        history.push({ role: type, content: text, quoteData, timestamp: Date.now() });
        // Keep only last 50 messages
        if (history.length > 50) history = history.slice(-50);
        sessionStorage.setItem('ai_conversation', JSON.stringify(history));
    }
    
    // Restore conversation from sessionStorage (메인페이지와 공유)
    function restoreConversation() {
        const history = JSON.parse(sessionStorage.getItem('ai_conversation') || '[]');
        if (history.length > 0) {
            // Clear default message
            messagesEl.innerHTML = '';
            history.forEach(msg => {
                // 메인페이지 형식(role, content) 또는 기존 형식(type, text) 모두 지원
                const type = msg.role || msg.type;
                const text = msg.content || msg.text;
                addMessage(text, type, msg.quoteData);
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
    
    // Clear conversation (메인페이지와 공유하는 대화도 함께 삭제)
    function clearConversation() {
        sessionStorage.removeItem('ai_conversation');
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
        goToBidding,
        submitQuoteRequest,
        clearConversation,
        isOpen: () => isOpen
    };
})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize on all pages (sidebar chat)
    AIAssistant.init();
});
