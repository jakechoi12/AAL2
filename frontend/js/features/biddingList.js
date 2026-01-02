/**
 * Bidding List Module
 * 포워더를 위한 입찰 목록 및 입찰 기능
 */

const QUOTE_API_BASE = 'http://localhost:8001';

const BiddingList = {
    // State
    forwarder: null,
    currentPage: 1,
    limit: 20,
    filters: {
        status: '',
        shipping_type: '',
        search: ''
    },
    currentBidding: null,
    currentBid: null,
    isEditMode: false,

    /**
     * Initialize the module
     */
    init() {
        console.log('🚀 BiddingList module initialized');
        
        // Check for stored forwarder session
        this.loadSession();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load initial data
        this.loadStats();
        this.loadBiddingList();
        
        // Update UI based on login state
        this.updateAuthUI();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Filter changes
        document.getElementById('filterStatus').addEventListener('change', () => this.applyFilters());
        document.getElementById('filterShipping').addEventListener('change', () => this.applyFilters());
        
        // Search with debounce
        let searchTimeout;
        document.getElementById('filterSearch').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => this.applyFilters(), 300);
        });

        // Close modals on overlay click
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });

        // Close modals on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAuthModal();
                this.closeBidModal();
                this.closeDetailModal();
            }
        });
    },

    /**
     * Load stored session
     */
    loadSession() {
        const stored = localStorage.getItem('forwarder');
        if (stored) {
            try {
                this.forwarder = JSON.parse(stored);
                console.log('✅ Session restored for:', this.forwarder.company);
            } catch (e) {
                localStorage.removeItem('forwarder');
            }
        }
    },

    /**
     * Save session
     */
    saveSession() {
        if (this.forwarder) {
            localStorage.setItem('forwarder', JSON.stringify(this.forwarder));
        }
    },

    /**
     * Update auth UI based on login state
     */
    updateAuthUI() {
        const actionsDiv = document.getElementById('forwarderActions');
        const forwarderBar = document.getElementById('forwarderBar');

        if (this.forwarder) {
            // Logged in state
            actionsDiv.innerHTML = '';
            forwarderBar.style.display = 'flex';
            
            document.getElementById('forwarderAvatar').textContent = 
                this.forwarder.company.charAt(0).toUpperCase();
            document.getElementById('forwarderCompany').textContent = this.forwarder.company;
            document.getElementById('forwarderEmail').textContent = this.forwarder.email;
        } else {
            // Logged out state
            actionsDiv.innerHTML = `
                <button class="action-btn primary" onclick="BiddingList.openAuthModal()">
                    <i class="fas fa-sign-in-alt"></i> 포워더 로그인
                </button>
            `;
            forwarderBar.style.display = 'none';
        }
    },

    /**
     * Open auth modal
     */
    openAuthModal() {
        document.getElementById('authModal').classList.add('active');
        this.showLoginForm();
    },

    /**
     * Close auth modal
     */
    closeAuthModal() {
        document.getElementById('authModal').classList.remove('active');
    },

    /**
     * Show login form
     */
    showLoginForm() {
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('registerForm').style.display = 'none';
        document.getElementById('authModalTitle').textContent = '포워더 로그인';
        document.getElementById('authSubmitBtn').textContent = '로그인';
        document.getElementById('authSubmitBtn').onclick = () => this.submitAuth();
    },

    /**
     * Show register form
     */
    showRegisterForm() {
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('registerForm').style.display = 'block';
        document.getElementById('authModalTitle').textContent = '포워더 등록';
        document.getElementById('authSubmitBtn').textContent = '등록하기';
        document.getElementById('authSubmitBtn').onclick = () => this.submitRegister();
    },

    /**
     * Submit login
     */
    async submitAuth() {
        const email = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value;
        
        if (!email) {
            alert('이메일을 입력해주세요.');
            return;
        }
        
        if (!password) {
            alert('비밀번호를 입력해주세요.');
            return;
        }

        try {
            const response = await fetch(`${QUOTE_API_BASE}/api/forwarder/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.status === 404) {
                    alert('등록되지 않은 이메일입니다. 신규 등록을 해주세요.');
                    this.showRegisterForm();
                    document.getElementById('regEmail').value = email;
                } else if (response.status === 401) {
                    alert('비밀번호가 일치하지 않습니다.');
                } else {
                    throw new Error(data.detail || 'Login failed');
                }
                return;
            }

            this.forwarder = data.forwarder;
            this.saveSession();
            this.closeAuthModal();
            this.updateAuthUI();
            this.loadBiddingList();
            
            alert(`환영합니다, ${this.forwarder.company}!`);

        } catch (error) {
            console.error('Login error:', error);
            alert('로그인 중 오류가 발생했습니다: ' + error.message);
        }
    },

    /**
     * Submit registration
     */
    async submitRegister() {
        const password = document.getElementById('regPassword').value;
        const passwordConfirm = document.getElementById('regPasswordConfirm').value;
        
        const formData = {
            company: document.getElementById('regCompany').value.trim(),
            name: document.getElementById('regName').value.trim(),
            business_no: document.getElementById('regBusinessNo').value.trim() || null,
            email: document.getElementById('regEmail').value.trim(),
            password: password,
            phone: document.getElementById('regPhone').value.trim()
        };

        // Validation
        if (!formData.company || !formData.name || !formData.email || !formData.password || !formData.phone) {
            alert('필수 항목을 모두 입력해주세요.');
            return;
        }
        
        // Password validation
        if (password.length < 6) {
            alert('비밀번호는 최소 6자 이상이어야 합니다.');
            return;
        }
        
        if (password !== passwordConfirm) {
            alert('비밀번호가 일치하지 않습니다.');
            return;
        }

        try {
            const response = await fetch(`${QUOTE_API_BASE}/api/forwarder/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            this.forwarder = data.forwarder;
            this.saveSession();
            this.closeAuthModal();
            this.updateAuthUI();
            this.loadBiddingList();
            
            alert(`등록이 완료되었습니다. 환영합니다, ${this.forwarder.company}!`);

        } catch (error) {
            console.error('Registration error:', error);
            alert('등록 중 오류가 발생했습니다: ' + error.message);
        }
    },

    /**
     * Logout
     */
    logout() {
        if (confirm('로그아웃 하시겠습니까?')) {
            this.forwarder = null;
            localStorage.removeItem('forwarder');
            this.updateAuthUI();
            this.loadBiddingList();
        }
    },

    /**
     * Load dashboard stats
     */
    async loadStats() {
        try {
            const response = await fetch(`${QUOTE_API_BASE}/api/bidding/stats`);
            const data = await response.json();

            document.getElementById('statTotal').textContent = data.total_count;
            document.getElementById('statOpen').textContent = data.open_count;
            document.getElementById('statClosing').textContent = data.closing_soon_count;
            document.getElementById('statAwarded').textContent = data.awarded_count;
            document.getElementById('statFailed').textContent = data.failed_count;

        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    },

    /**
     * Apply filters
     */
    applyFilters() {
        this.filters.status = document.getElementById('filterStatus').value;
        this.filters.shipping_type = document.getElementById('filterShipping').value;
        this.filters.search = document.getElementById('filterSearch').value.trim();
        this.currentPage = 1;
        this.loadBiddingList();
    },

    /**
     * Load bidding list
     */
    async loadBiddingList() {
        const tbody = document.getElementById('biddingTableBody');
        const emptyState = document.getElementById('emptyState');
        const loadingState = document.getElementById('loadingState');

        // Show loading
        tbody.innerHTML = '';
        loadingState.style.display = 'flex';
        emptyState.style.display = 'none';

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: this.limit
            });

            if (this.filters.status) params.append('status', this.filters.status);
            if (this.filters.shipping_type) params.append('shipping_type', this.filters.shipping_type);
            if (this.filters.search) params.append('search', this.filters.search);
            if (this.forwarder) params.append('forwarder_id', this.forwarder.id);

            const response = await fetch(`${QUOTE_API_BASE}/api/bidding/list?${params}`);
            const data = await response.json();

            loadingState.style.display = 'none';

            if (data.data.length === 0) {
                emptyState.style.display = 'block';
                this.renderPagination(0, 0);
                return;
            }

            // Render rows
            tbody.innerHTML = data.data.map(item => this.renderRow(item)).join('');
            
            // Render pagination
            this.renderPagination(data.total, Math.ceil(data.total / this.limit));

        } catch (error) {
            console.error('Failed to load bidding list:', error);
            loadingState.style.display = 'none';
            emptyState.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <h3>데이터를 불러오는데 실패했습니다</h3>
                <p>서버 연결을 확인하고 다시 시도해주세요.</p>
            `;
            emptyState.style.display = 'block';
        }
    },

    /**
     * Render a table row
     */
    renderRow(item) {
        const isUrgent = item.deadline && this.isWithin24Hours(item.deadline);
        const deadlineFormatted = item.deadline ? this.formatDateTime(item.deadline) : '-';
        
        // Determine action button
        let actionBtn = '';
        if (item.status === 'open') {
            if (!this.forwarder) {
                actionBtn = `<button class="action-btn secondary" onclick="BiddingList.openAuthModal()">
                    로그인 필요
                </button>`;
            } else if (item.my_bid_status) {
                actionBtn = `<button class="action-btn success" onclick="BiddingList.openBidModal('${item.bidding_no}', true)">
                    <i class="fas fa-edit"></i> 수정하기
                </button>`;
            } else {
                actionBtn = `<button class="action-btn primary" onclick="BiddingList.openBidModal('${item.bidding_no}')">
                    <i class="fas fa-gavel"></i> 입찰하기
                </button>`;
            }
        } else if (item.status === 'awarded' && item.my_bid_status === 'awarded') {
            actionBtn = `<span class="status-badge awarded"><i class="fas fa-trophy"></i> 낙찰</span>`;
        } else {
            actionBtn = `<button class="action-btn secondary" onclick="BiddingList.openDetailModal('${item.bidding_no}')">
                상세보기
            </button>`;
        }

        return `
            <tr>
                <td>
                    <span class="bidding-no" onclick="BiddingList.openDetailModal('${item.bidding_no}')">
                        ${item.bidding_no}
                    </span>
                </td>
                <td>${item.customer_company}</td>
                <td>
                    <div class="route-cell">
                        <span>${item.pol}</span>
                        <span class="route-arrow">→</span>
                        <span>${item.pod}</span>
                    </div>
                </td>
                <td>
                    <span class="type-badge ${item.shipping_type}">
                        <i class="fas fa-${this.getShippingIcon(item.shipping_type)}"></i>
                        ${item.shipping_type.toUpperCase()} / ${item.load_type}
                    </span>
                </td>
                <td>${this.formatDate(item.etd)}</td>
                <td class="deadline-cell ${isUrgent ? 'urgent' : ''}">${deadlineFormatted}</td>
                <td>
                    <span class="status-badge ${item.status}">${this.getStatusLabel(item.status)}</span>
                </td>
                <td>
                    <span class="bid-count">${item.bid_count}</span>
                </td>
                <td>${actionBtn}</td>
            </tr>
        `;
    },

    /**
     * Render pagination
     */
    renderPagination(total, totalPages) {
        const pagination = document.getElementById('pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let html = `
            <button class="pagination-btn" onclick="BiddingList.goToPage(${this.currentPage - 1})" 
                    ${this.currentPage === 1 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i>
            </button>
        `;

        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        if (startPage > 1) {
            html += `<button class="pagination-btn" onclick="BiddingList.goToPage(1)">1</button>`;
            if (startPage > 2) html += `<span class="pagination-info">...</span>`;
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                        onclick="BiddingList.goToPage(${i})">${i}</button>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) html += `<span class="pagination-info">...</span>`;
            html += `<button class="pagination-btn" onclick="BiddingList.goToPage(${totalPages})">${totalPages}</button>`;
        }

        html += `
            <span class="pagination-info">총 ${total}건</span>
            <button class="pagination-btn" onclick="BiddingList.goToPage(${this.currentPage + 1})" 
                    ${this.currentPage === totalPages ? 'disabled' : ''}>
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        pagination.innerHTML = html;
    },

    /**
     * Go to specific page
     */
    goToPage(page) {
        this.currentPage = page;
        this.loadBiddingList();
    },

    /**
     * Refresh data
     */
    refresh() {
        this.loadStats();
        this.loadBiddingList();
    },

    /**
     * Open bid modal
     */
    async openBidModal(biddingNo, isEdit = false) {
        if (!this.forwarder) {
            this.openAuthModal();
            return;
        }

        this.isEditMode = isEdit;

        try {
            // Load bidding detail
            const response = await fetch(
                `${QUOTE_API_BASE}/api/bidding/${biddingNo}/detail?forwarder_id=${this.forwarder.id}`
            );
            const detail = await response.json();

            if (!response.ok) throw new Error(detail.detail);

            this.currentBidding = detail;

            // Populate modal
            document.getElementById('bidModalBiddingNo').textContent = biddingNo;
            document.getElementById('bidInfoRoute').textContent = `${detail.pol} → ${detail.pod}`;
            document.getElementById('bidInfoType').textContent = `${detail.shipping_type.toUpperCase()} / ${detail.load_type}`;
            document.getElementById('bidInfoEtd').textContent = this.formatDate(detail.etd);
            document.getElementById('bidInfoDeadline').textContent = detail.deadline ? 
                this.formatDateTime(detail.deadline) : '-';

            // If editing, populate existing bid data
            if (isEdit && detail.my_bid) {
                this.currentBid = detail.my_bid;
                document.getElementById('bidFreight').value = detail.my_bid.freight_charge || '';
                document.getElementById('bidLocal').value = detail.my_bid.local_charge || '';
                document.getElementById('bidOther').value = detail.my_bid.other_charge || '';
                document.getElementById('bidTransitTime').value = detail.my_bid.transit_time || '';
                document.getElementById('bidValidity').value = detail.my_bid.validity_date ? 
                    detail.my_bid.validity_date.split('T')[0] : '';
                document.getElementById('bidRemark').value = detail.my_bid.remark || '';
                
                document.getElementById('bidSubmitBtn').innerHTML = '<i class="fas fa-save"></i> 수정 저장';
            } else {
                // Clear form
                this.currentBid = null;
                document.getElementById('bidFreight').value = '';
                document.getElementById('bidLocal').value = '';
                document.getElementById('bidOther').value = '';
                document.getElementById('bidTransitTime').value = '';
                document.getElementById('bidValidity').value = '';
                document.getElementById('bidRemark').value = '';
                
                document.getElementById('bidSubmitBtn').innerHTML = '<i class="fas fa-gavel"></i> 입찰 제출';
            }

            this.calculateTotal();
            document.getElementById('bidModal').classList.add('active');

        } catch (error) {
            console.error('Failed to load bidding detail:', error);
            alert('입찰 정보를 불러오는데 실패했습니다: ' + error.message);
        }
    },

    /**
     * Close bid modal
     */
    closeBidModal() {
        document.getElementById('bidModal').classList.remove('active');
        this.currentBidding = null;
        this.currentBid = null;
    },

    /**
     * Calculate total amount
     */
    calculateTotal() {
        const freight = parseFloat(document.getElementById('bidFreight').value) || 0;
        const local = parseFloat(document.getElementById('bidLocal').value) || 0;
        const other = parseFloat(document.getElementById('bidOther').value) || 0;
        const total = freight + local + other;
        
        document.getElementById('bidTotalAmount').textContent = total.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    },

    /**
     * Submit bid
     */
    async submitBid() {
        if (!this.forwarder || !this.currentBidding) return;

        const freight = parseFloat(document.getElementById('bidFreight').value) || 0;
        const local = parseFloat(document.getElementById('bidLocal').value) || 0;
        const other = parseFloat(document.getElementById('bidOther').value) || 0;
        const total = freight + local + other;

        if (total <= 0) {
            alert('입찰 금액을 입력해주세요.');
            return;
        }

        const bidData = {
            bidding_id: this.currentBidding.id,
            total_amount: total,
            freight_charge: freight || null,
            local_charge: local || null,
            other_charge: other || null,
            transit_time: document.getElementById('bidTransitTime').value.trim() || null,
            validity_date: document.getElementById('bidValidity').value || null,
            remark: document.getElementById('bidRemark').value.trim() || null
        };

        try {
            let response;
            
            if (this.isEditMode && this.currentBid) {
                // Update existing bid
                response = await fetch(`${QUOTE_API_BASE}/api/bid/${this.currentBid.id}?forwarder_id=${this.forwarder.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bidData)
                });
            } else {
                // Submit new bid
                response = await fetch(`${QUOTE_API_BASE}/api/bid/submit?forwarder_id=${this.forwarder.id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bidData)
                });
            }

            const result = await response.json();

            if (!response.ok) throw new Error(result.detail);

            alert(result.message);
            this.closeBidModal();
            this.loadBiddingList();
            this.loadStats();

        } catch (error) {
            console.error('Failed to submit bid:', error);
            alert('입찰 제출에 실패했습니다: ' + error.message);
        }
    },

    /**
     * Open detail modal
     */
    async openDetailModal(biddingNo) {
        try {
            const forwarderId = this.forwarder ? this.forwarder.id : null;
            const url = forwarderId 
                ? `${QUOTE_API_BASE}/api/bidding/${biddingNo}/detail?forwarder_id=${forwarderId}`
                : `${QUOTE_API_BASE}/api/bidding/${biddingNo}/detail`;
            
            const response = await fetch(url);
            const detail = await response.json();

            if (!response.ok) throw new Error(detail.detail);

            document.getElementById('detailBiddingNo').textContent = biddingNo;
            
            let html = `
                <div class="bid-info-card">
                    <div class="bid-info-row">
                        <span class="bid-info-label">화주사</span>
                        <span class="bid-info-value">${detail.customer_company}</span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">구간</span>
                        <span class="bid-info-value">${detail.pol} → ${detail.pod}</span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">운송타입</span>
                        <span class="bid-info-value">${detail.shipping_type.toUpperCase()} / ${detail.load_type}</span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">Trade Mode</span>
                        <span class="bid-info-value">${detail.trade_mode.toUpperCase()}</span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">Incoterms</span>
                        <span class="bid-info-value">${detail.incoterms || '-'}</span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">ETD</span>
                        <span class="bid-info-value">${this.formatDate(detail.etd)}</span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">ETA</span>
                        <span class="bid-info-value">${detail.eta ? this.formatDate(detail.eta) : '-'}</span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">마감일시</span>
                        <span class="bid-info-value">${detail.deadline ? this.formatDateTime(detail.deadline) : '-'}</span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">상태</span>
                        <span class="bid-info-value">
                            <span class="status-badge ${detail.status}">${this.getStatusLabel(detail.status)}</span>
                        </span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">위험물</span>
                        <span class="bid-info-value">${detail.is_dg ? '예' : '아니오'}</span>
                    </div>
                    <div class="bid-info-row">
                        <span class="bid-info-label">입찰 참여</span>
                        <span class="bid-info-value">${detail.bid_count}건</span>
                    </div>
                </div>
            `;

            if (detail.remark) {
                html += `
                    <div style="margin-top: 1rem;">
                        <strong>비고:</strong>
                        <p style="color: var(--text-sub); margin-top: 0.5rem;">${detail.remark}</p>
                    </div>
                `;
            }

            if (detail.my_bid) {
                html += `
                    <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                        <h4 style="margin-bottom: 1rem;">내 입찰 정보</h4>
                        <div class="bid-info-card">
                            <div class="bid-info-row">
                                <span class="bid-info-label">입찰금액</span>
                                <span class="bid-info-value" style="color: var(--accent-color); font-weight: 700;">
                                    $ ${parseFloat(detail.my_bid.total_amount).toLocaleString()}
                                </span>
                            </div>
                            <div class="bid-info-row">
                                <span class="bid-info-label">상태</span>
                                <span class="bid-info-value">
                                    <span class="status-badge ${detail.my_bid.status}">${this.getBidStatusLabel(detail.my_bid.status)}</span>
                                </span>
                            </div>
                        </div>
                    </div>
                `;
            }

            document.getElementById('detailModalBody').innerHTML = html;

            // PDF button
            const pdfBtn = document.getElementById('detailPdfBtn');
            if (detail.pdf_url) {
                pdfBtn.href = `${QUOTE_API_BASE}${detail.pdf_url}`;
                pdfBtn.style.display = 'inline-flex';
            } else {
                pdfBtn.style.display = 'none';
            }

            document.getElementById('detailModal').classList.add('active');

        } catch (error) {
            console.error('Failed to load detail:', error);
            alert('상세 정보를 불러오는데 실패했습니다: ' + error.message);
        }
    },

    /**
     * Close detail modal
     */
    closeDetailModal() {
        document.getElementById('detailModal').classList.remove('active');
    },

    // ==========================================
    // UTILITY FUNCTIONS
    // ==========================================

    getShippingIcon(type) {
        const icons = {
            'ocean': 'ship',
            'air': 'plane',
            'truck': 'truck',
            'all': 'boxes'
        };
        return icons[type] || 'box';
    },

    getStatusLabel(status) {
        const labels = {
            'open': '진행중',
            'closed': '마감',
            'awarded': '낙찰',
            'expired': '만료',
            'cancelled': '취소'
        };
        return labels[status] || status;
    },

    getBidStatusLabel(status) {
        const labels = {
            'draft': '임시저장',
            'submitted': '제출완료',
            'awarded': '낙찰',
            'rejected': '탈락'
        };
        return labels[status] || status;
    },

    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    },

    formatDateTime(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ko-KR', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    isWithin24Hours(dateStr) {
        if (!dateStr) return false;
        const deadline = new Date(dateStr);
        const now = new Date();
        const diff = deadline - now;
        return diff > 0 && diff <= 24 * 60 * 60 * 1000;
    }
};

// Export for global access
window.BiddingList = BiddingList;
