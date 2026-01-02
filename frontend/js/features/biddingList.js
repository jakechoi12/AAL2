/**
 * Bidding List Module
 * 포워더를 위한 입찰 목록 및 입찰 기능 (상세 견적서 포함)
 */

// QUOTE_API_BASE는 api.js에서 정의됨 (중복 정의 방지)
// const QUOTE_API_BASE = 'http://localhost:8001';

// 표준 Freight Codes (백엔드 연동 전 프론트엔드 데이터)
const FREIGHT_CODES = [
    { code: 'OFR', category: 'Ocean Freight', defaultCurrency: 'USD' },
    { code: 'AFR', category: 'Air Freight', defaultCurrency: 'USD' },
    { code: 'BAF', category: 'Bunker Adjustment Factor', defaultCurrency: 'USD' },
    { code: 'CAF', category: 'Currency Adjustment Factor', defaultCurrency: 'USD' },
    { code: 'THC', category: 'Terminal Handling Charge', defaultCurrency: 'USD' },
    { code: 'DOC', category: 'Documentation Fee', defaultCurrency: 'USD' },
    { code: 'WFG', category: 'Wharfage', defaultCurrency: 'USD' },
    { code: 'CFS', category: 'CFS Charge', defaultCurrency: 'USD' },
    { code: 'SEAL', category: 'Seal Fee', defaultCurrency: 'USD' },
    { code: 'AMS', category: 'AMS Fee', defaultCurrency: 'USD' },
    { code: 'ENS', category: 'ENS Fee', defaultCurrency: 'USD' },
    { code: 'LSS', category: 'Low Sulphur Surcharge', defaultCurrency: 'USD' },
    { code: 'EBS', category: 'Emergency Bunker Surcharge', defaultCurrency: 'USD' },
    { code: 'CIC', category: 'Container Imbalance Charge', defaultCurrency: 'USD' },
    { code: 'PSS', category: 'Peak Season Surcharge', defaultCurrency: 'USD' },
    { code: 'INLAND', category: 'Inland Transport', defaultCurrency: 'USD' },
    { code: 'CUSTOMS', category: 'Customs Clearance', defaultCurrency: 'USD' },
    { code: 'TRUCKING', category: 'Trucking', defaultCurrency: 'USD' },
    { code: 'HANDLING', category: 'Handling Fee', defaultCurrency: 'USD' },
    { code: 'OTHER', category: 'Other Charges', defaultCurrency: 'USD' }
];

const UNIT_OPTIONS = ['20DC', '40DC', '40HC', '45HC', 'CBM', 'KG', 'BL', 'CNTR', 'SHPT'];
const CURRENCY_OPTIONS = ['USD', 'KRW', 'EUR', 'JPY', 'CNY'];
const TAX_OPTIONS = ['영세', '과세'];

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
    lineItems: [], // 비용 항목 배열
    bidSaved: false,      // SAVE 완료 여부
    bidEdited: false,     // 수정됨 여부
    originalBidData: null, // 원본 데이터 (변경 감지용)

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
     * Check if deadline has passed
     */
    isDeadlinePassed(dateStr) {
        if (!dateStr) return false;
        const deadline = new Date(dateStr);
        const now = new Date();
        return deadline < now;
    },

    /**
     * Render a table row
     */
    renderRow(item) {
        const isUrgent = item.deadline && this.isWithin24Hours(item.deadline);
        const isExpired = item.deadline && this.isDeadlinePassed(item.deadline);
        const deadlineFormatted = item.deadline ? this.formatDateTime(item.deadline) : '-';
        
        // Determine effective status (마감일이 지났으면 expired로 처리)
        let effectiveStatus = item.status;
        if (item.status === 'open' && isExpired) {
            effectiveStatus = 'expired';
        }
        
        // Determine action button
        let actionBtn = '';
        if (effectiveStatus === 'open') {
            if (!this.forwarder) {
                actionBtn = `<button class="action-btn secondary" onclick="BiddingList.openAuthModal()">
                    로그인 필요
                </button>`;
            } else if (item.my_bid_status) {
                actionBtn = `<button class="action-btn success" onclick="BiddingList.goToQuoteRegistration('${item.bidding_no}', true)">
                    <i class="fas fa-edit"></i> 수정하기
                </button>`;
            } else {
                actionBtn = `<button class="action-btn primary" onclick="BiddingList.goToQuoteRegistration('${item.bidding_no}')">
                    <i class="fas fa-gavel"></i> 입찰하기
                </button>`;
            }
        } else if (effectiveStatus === 'expired') {
            // 마감된 항목은 상세보기만 가능
            actionBtn = `<button class="action-btn secondary" onclick="BiddingList.openDetailModal('${item.bidding_no}')">
                상세보기
            </button>`;
        } else if (item.status === 'awarded' && item.my_bid_status === 'awarded') {
            actionBtn = `<span class="status-badge awarded"><i class="fas fa-trophy"></i> 낙찰</span>`;
        } else {
            actionBtn = `<button class="action-btn secondary" onclick="BiddingList.openDetailModal('${item.bidding_no}')">
                상세보기
            </button>`;
        }

        // 마감 여부에 따른 행 클래스
        const rowClass = isExpired ? 'expired-row' : '';

        return `
            <tr class="${rowClass}">
                <td>
                    <span class="bidding-no ${isExpired ? 'expired-text' : ''}" onclick="BiddingList.openDetailModal('${item.bidding_no}')">
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
                <td class="deadline-cell ${isExpired ? 'expired' : (isUrgent ? 'urgent' : '')}">${deadlineFormatted}${isExpired ? ' <span class="expired-label">마감</span>' : ''}</td>
                <td>
                    <span class="status-badge ${effectiveStatus}">${this.getStatusLabel(effectiveStatus)}</span>
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
     * Navigate to Quote Registration (now opens modal)
     */
    goToQuoteRegistration(biddingNo, isEdit = false) {
        // Use modal instead of page navigation
        this.openBidModal(biddingNo, isEdit);
    },

    /**
     * Toggle Additional Info section
     */
    toggleAdditionalInfo() {
        const content = document.getElementById('additionalInfoContent');
        const icon = document.getElementById('additionalToggleIcon');
        
        if (content.classList.contains('show')) {
            content.classList.remove('show');
            icon.classList.remove('expanded');
        } else {
            content.classList.add('show');
            icon.classList.add('expanded');
        }
    },

    /**
     * Populate Request Details from Quotation data (새 UI 구조)
     */
    populateRequestDetails(detail) {
        const setTextContent = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.textContent = value || '-';
        };

        // Header Deadline
        const headerDeadline = document.getElementById('headerDeadline');
        const headerDday = document.getElementById('headerDday');
        if (headerDeadline && detail.deadline) {
            headerDeadline.textContent = this.formatDateTime(detail.deadline);
            if (headerDday) {
                const dday = this.calculateDday(detail.deadline);
                headerDday.textContent = dday;
                headerDday.style.background = dday.startsWith('D+') ? '#6b7280' : '#ef4444';
            }
        }

        // Request Information Grid
        setTextContent('reqCustomer', detail.customer_company);
        setTextContent('reqTradeMode', detail.trade_mode ? detail.trade_mode.charAt(0).toUpperCase() + detail.trade_mode.slice(1) : '-');
        setTextContent('reqShippingMode', this.getShippingTypeLabel(detail.shipping_type));
        setTextContent('reqLoadType', detail.load_type);
        setTextContent('reqIncoterms', detail.incoterms);
        setTextContent('reqPOL', detail.pol);
        setTextContent('reqPOD', detail.pod);
        setTextContent('reqETD', detail.etd ? this.formatDate(detail.etd) : '-');
        setTextContent('reqETA', detail.eta ? this.formatDate(detail.eta) : '-');
        setTextContent('reqInvoice', detail.invoice_value ? `USD ${this.formatNumber(detail.invoice_value)}` : '-');
        
        // DG (Dangerous Goods)
        const dgEl = document.getElementById('reqDG');
        if (dgEl) {
            if (detail.is_dg) {
                let dgText = 'Yes';
                if (detail.dg_class) dgText += ` (${detail.dg_class})`;
                dgEl.innerHTML = `<span style="color: #f59e0b;"><i class="fas fa-exclamation-triangle"></i> ${dgText}</span>`;
            } else {
                dgEl.innerHTML = '<span style="color: #6b7280;">No</span>';
            }
        }

        // Cargo Details Table (동적 컬럼)
        this.populateCargoDetailsTable(detail);

        // Transport Section - ETD 표시 (readonly)
        const bidETD = document.getElementById('bidETD');
        if (bidETD) {
            bidETD.value = detail.etd ? this.formatDate(detail.etd) : '-';
        }

        // Carrier label 동적 변경
        const carrierLabel = document.getElementById('carrierLabel');
        if (carrierLabel) {
            const labels = { 'air': 'Airline', 'ocean': 'Carrier', 'truck': 'Trucker' };
            carrierLabel.textContent = labels[detail.shipping_type] || 'Carrier';
        }

        // Special Remarks
        const remarksSection = document.getElementById('remarksSection');
        const reqRemarks = document.getElementById('reqRemarks');
        if (remarksSection && reqRemarks) {
            if (detail.remark && detail.remark.trim()) {
                reqRemarks.textContent = detail.remark;
                remarksSection.style.display = 'block';
            } else {
                remarksSection.style.display = 'none';
            }
        }
    },

    /**
     * Calculate D-Day
     */
    calculateDday(deadline) {
        const now = new Date();
        const deadlineDate = new Date(deadline);
        const diff = Math.ceil((deadlineDate - now) / (1000 * 60 * 60 * 24));
        if (diff > 0) return `D-${diff}`;
        if (diff === 0) return 'D-Day';
        return `D+${Math.abs(diff)}`;
    },

    /**
     * Calculate Transit Time
     */
    calculateTT() {
        const etdEl = document.getElementById('bidETD');
        const etaEl = document.getElementById('bidETA');
        const ttEl = document.getElementById('bidTT');
        
        if (!etdEl || !etaEl || !ttEl) return;
        
        const etdValue = this.currentBidding?.etd;
        const etaValue = etaEl.value;
        
        if (etdValue && etaValue) {
            const etd = new Date(etdValue);
            const eta = new Date(etaValue);
            const days = Math.ceil((eta - etd) / (1000 * 60 * 60 * 24));
            ttEl.value = days > 0 ? `${days} Days` : '-';
        } else {
            ttEl.value = '-';
        }
        
        // Mark as edited
        this.markAsEdited();
    },

    /**
     * Get shipping type label
     */
    getShippingTypeLabel(type) {
        const labels = {
            'ocean': 'Ocean Freight',
            'air': 'Air Freight',
            'truck': 'Trucking',
            'all': 'All Types'
        };
        return labels[type] || type || '-';
    },

    /**
     * Populate Cargo Details Table (운송 타입별 동적 컬럼)
     */
    populateCargoDetailsTable(detail) {
        const thead = document.getElementById('cargoTableHead');
        const tbody = document.getElementById('cargoDetailsBody');
        if (!thead || !tbody) return;

        const shippingType = detail.shipping_type;
        const cargoDetails = detail.cargo_details || [];
        
        // 운송 타입별 컬럼 구성
        let columns = [];
        if (shippingType === 'air') {
            // AIR: Container/Type, CBM 제외
            columns = [
                { key: 'no', label: 'No.', width: '50px' },
                { key: 'length', label: 'L(cm)', width: '70px' },
                { key: 'width', label: 'W(cm)', width: '70px' },
                { key: 'height', label: 'H(cm)', width: '70px' },
                { key: 'qty', label: 'Qty', width: '50px' },
                { key: 'gross_weight', label: 'G.W(kg)', width: '80px' },
                { key: 'volume_weight', label: 'Vol.W', width: '70px' },
                { key: 'chargeable_weight', label: 'C.W', width: '70px' }
            ];
        } else if (shippingType === 'ocean' && detail.load_type === 'FCL') {
            // Ocean FCL
            columns = [
                { key: 'no', label: 'No.', width: '50px' },
                { key: 'container_type', label: 'Container', width: '100px' },
                { key: 'qty', label: 'Qty', width: '50px' },
                { key: 'gross_weight', label: 'G.W(kg)', width: '90px' },
                { key: 'cbm', label: 'CBM', width: '80px' }
            ];
        } else {
            // Ocean LCL, Truck, 기타
            columns = [
                { key: 'no', label: 'No.', width: '50px' },
                { key: 'container_type', label: 'Type', width: '90px' },
                { key: 'length', label: 'L(cm)', width: '65px' },
                { key: 'width', label: 'W(cm)', width: '65px' },
                { key: 'height', label: 'H(cm)', width: '65px' },
                { key: 'qty', label: 'Qty', width: '50px' },
                { key: 'gross_weight', label: 'G.W(kg)', width: '80px' },
                { key: 'cbm', label: 'CBM', width: '70px' }
            ];
        }

        // 헤더 생성
        thead.innerHTML = `<tr>${columns.map(col => 
            `<th style="width: ${col.width}">${col.label}</th>`
        ).join('')}</tr>`;

        // 바디 생성
        if (cargoDetails.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${columns.length}" class="no-data">No cargo details</td></tr>`;
        } else {
            let totals = { qty: 0, gross_weight: 0, cbm: 0, volume_weight: 0, chargeable_weight: 0 };
            
            tbody.innerHTML = cargoDetails.map((cd, idx) => {
                totals.qty += cd.qty || 0;
                totals.gross_weight += cd.gross_weight || 0;
                totals.cbm += cd.cbm || 0;
                totals.volume_weight += cd.volume_weight || 0;
                totals.chargeable_weight += cd.chargeable_weight || 0;

                return `<tr>${columns.map(col => {
                    if (col.key === 'no') return `<td>${idx + 1}</td>`;
                    if (col.key === 'container_type') return `<td>${cd.container_type || cd.truck_type || '-'}</td>`;
                    if (col.key === 'gross_weight') return `<td>${cd.gross_weight ? this.formatNumber(cd.gross_weight) : '-'}</td>`;
                    if (col.key === 'cbm') return `<td>${cd.cbm ? this.formatNumber(cd.cbm, 2) : '-'}</td>`;
                    return `<td>${cd[col.key] || '-'}</td>`;
                }).join('')}</tr>`;
            }).join('');

            // Total 행 추가
            tbody.innerHTML += `<tr class="total-row">${columns.map((col, i) => {
                if (i === 0) return `<td colspan="1" style="text-align: right; font-weight: 600;">Total</td>`;
                if (col.key === 'qty') return `<td>${totals.qty}</td>`;
                if (col.key === 'gross_weight') return `<td>${totals.gross_weight ? this.formatNumber(totals.gross_weight) : '-'}</td>`;
                if (col.key === 'cbm') return `<td>${totals.cbm ? this.formatNumber(totals.cbm, 2) : '-'}</td>`;
                if (col.key === 'volume_weight') return `<td>${totals.volume_weight || '-'}</td>`;
                if (col.key === 'chargeable_weight') return `<td>${totals.chargeable_weight || '-'}</td>`;
                return '<td></td>';
            }).join('')}</tr>`;
        }
    },

    /**
     * Populate Additional Information from Quotation data
     */
    populateAdditionalInfo(detail) {
        // Export Customs Clearance
        const exportCC = detail.export_cc === true;
        const addExportCC = document.getElementById('addExportCC');
        const tagExportCC = document.getElementById('tagExportCC');
        if (addExportCC) {
            addExportCC.innerHTML = exportCC 
                ? '<i class="fas fa-check-circle"></i> Required'
                : '<i class="fas fa-times-circle"></i> No';
            addExportCC.className = 'item-value ' + (exportCC ? 'required' : 'not-required');
        }
        if (tagExportCC) tagExportCC.classList.toggle('active', exportCC);

        // Import Customs Clearance
        const importCC = detail.import_cc === true;
        const addImportCC = document.getElementById('addImportCC');
        const tagImportCC = document.getElementById('tagImportCC');
        if (addImportCC) {
            addImportCC.innerHTML = importCC 
                ? '<i class="fas fa-check-circle"></i> Required'
                : '<i class="fas fa-times-circle"></i> No';
            addImportCC.className = 'item-value ' + (importCC ? 'required' : 'not-required');
        }
        if (tagImportCC) tagImportCC.classList.toggle('active', importCC);

        // Shipping Insurance
        const insurance = detail.shipping_insurance === true;
        const addInsurance = document.getElementById('addInsurance');
        const tagInsurance = document.getElementById('tagInsurance');
        if (addInsurance) {
            addInsurance.innerHTML = insurance 
                ? '<i class="fas fa-check-circle"></i> Required'
                : '<i class="fas fa-times-circle"></i> No';
            addInsurance.className = 'item-value ' + (insurance ? 'required' : 'not-required');
        }
        if (tagInsurance) tagInsurance.classList.toggle('active', insurance);

        // Pickup
        const pickup = detail.pickup_required === true;
        const addPickup = document.getElementById('addPickup');
        const addPickupAddr = document.getElementById('addPickupAddr');
        const tagPickup = document.getElementById('tagPickup');
        if (addPickup) {
            addPickup.innerHTML = pickup 
                ? '<i class="fas fa-check-circle"></i> Required'
                : '<i class="fas fa-times-circle"></i> No';
            addPickup.className = 'item-value ' + (pickup ? 'required' : 'not-required');
        }
        if (addPickupAddr) {
            addPickupAddr.textContent = detail.pickup_address || '';
            addPickupAddr.style.display = pickup && detail.pickup_address ? 'inline' : 'none';
        }
        if (tagPickup) tagPickup.classList.toggle('active', pickup);

        // Delivery
        const delivery = detail.delivery_required === true;
        const addDelivery = document.getElementById('addDelivery');
        const addDeliveryAddr = document.getElementById('addDeliveryAddr');
        const tagDelivery = document.getElementById('tagDelivery');
        if (addDelivery) {
            addDelivery.innerHTML = delivery 
                ? '<i class="fas fa-check-circle"></i> Required'
                : '<i class="fas fa-times-circle"></i> No';
            addDelivery.className = 'item-value ' + (delivery ? 'required' : 'not-required');
        }
        if (addDeliveryAddr) {
            addDeliveryAddr.textContent = detail.delivery_address || '';
            addDeliveryAddr.style.display = delivery && detail.delivery_address ? 'inline' : 'none';
        }
        if (tagDelivery) tagDelivery.classList.toggle('active', delivery);
    },

    /**
     * Format number with commas
     */
    formatNumber(num) {
        if (num === null || num === undefined || isNaN(num)) return '-';
        return parseFloat(num).toLocaleString('en-US');
    },

    /**
     * Open bid modal - Quote Registration Modal
     */
    async openBidModal(biddingNo, isEdit = false) {
        if (!this.forwarder) {
            this.openAuthModal();
            return;
        }

        this.isEditMode = isEdit;
        
        // Reset SAVE/SUBMIT state
        this.bidSaved = false;
        this.bidEdited = false;
        this.currentBid = null;
        this.originalBidData = null;

        try {
            // Load bidding detail
            const response = await fetch(
                `${QUOTE_API_BASE}/api/bidding/${biddingNo}/detail?forwarder_id=${this.forwarder.id}`
            );
            const detail = await response.json();

            if (!response.ok) throw new Error(detail.detail);

            this.currentBidding = detail;

            // Populate modal header info
            document.getElementById('bidModalBiddingNo').textContent = biddingNo;
            
            // Populate Request Details (Quotation 정보)
            this.populateRequestDetails(detail);
            
            // Populate Additional Information (Quotation 추가 정보)
            this.populateAdditionalInfo(detail);

            // If editing, populate existing bid data
            if (isEdit && detail.my_bid) {
                this.currentBid = detail.my_bid;
                this.bidSaved = true; // 기존 데이터가 있으면 저장된 상태
                
                // Transport Details
                const bidETA = document.getElementById('bidETA');
                const bidCarrier = document.getElementById('bidCarrier');
                const bidValidity = document.getElementById('bidValidity');
                const bidRemark = document.getElementById('bidRemark');
                
                if (bidETA) bidETA.value = detail.my_bid.eta ? detail.my_bid.eta.split('T')[0] : '';
                if (bidCarrier) bidCarrier.value = detail.my_bid.carrier || '';
                if (bidValidity) bidValidity.value = detail.my_bid.validity_date ? detail.my_bid.validity_date.split('T')[0] : '';
                if (bidRemark) bidRemark.value = detail.my_bid.remark || '';
                
                // T/T 계산
                this.calculateTT();
                
                // 기존 bid의 line_items 로드
                if (detail.my_bid.line_items && detail.my_bid.line_items.length > 0) {
                    this.lineItems = detail.my_bid.line_items.map((item, idx) => ({
                        id: idx,
                        code: item.code,
                        category: item.category,
                        unit: item.unit || '',
                        qty: item.qty || 1,
                        rate: item.rate || 0,
                        currency: item.currency || 'USD',
                        tax: item.tax_type || '영세',
                        vat: item.vat_percent || 0
                    }));
                } else {
                    // 기존 단순 금액을 라인 아이템으로 변환
                    this.lineItems = [];
                    if (detail.my_bid.freight_charge) {
                        this.lineItems.push({
                            id: 0,
                            code: 'OFR',
                            category: 'Ocean Freight',
                            unit: detail.load_type || '20DC',
                            qty: 1,
                            rate: detail.my_bid.freight_charge,
                            currency: 'USD',
                            tax: '영세',
                            vat: 0
                        });
                    }
                    if (detail.my_bid.local_charge) {
                        this.lineItems.push({
                            id: 1,
                            code: 'THC',
                            category: 'Terminal Handling Charge',
                            unit: detail.load_type || '20DC',
                            qty: 1,
                            rate: detail.my_bid.local_charge,
                            currency: 'USD',
                            tax: '영세',
                            vat: 0
                        });
                    }
                    if (detail.my_bid.other_charge) {
                        this.lineItems.push({
                            id: 2,
                            code: 'OTHER',
                            category: 'Other Charges',
                            unit: 'SHPT',
                            qty: 1,
                            rate: detail.my_bid.other_charge,
                            currency: 'USD',
                            tax: '영세',
                            vat: 0
                        });
                    }
                }
                
            } else {
                // Clear form - 기본 라인 아이템 추가
                this.currentBid = null;
                this.lineItems = [
                    {
                        id: 0,
                        code: detail.shipping_type === 'air' ? 'AFR' : 'OFR',
                        category: detail.shipping_type === 'air' ? 'Air Freight' : 'Ocean Freight',
                        unit: detail.load_type || '20DC',
                        qty: 1,
                        rate: 0,
                        currency: 'USD',
                        tax: '영세',
                        vat: 0
                    }
                ];
                
                // Clear transport fields
                const bidETA = document.getElementById('bidETA');
                const bidCarrier = document.getElementById('bidCarrier');
                const bidValidity = document.getElementById('bidValidity');
                const bidRemark = document.getElementById('bidRemark');
                const bidTT = document.getElementById('bidTT');
                
                if (bidETA) bidETA.value = '';
                if (bidCarrier) bidCarrier.value = '';
                if (bidValidity) bidValidity.value = '';
                if (bidRemark) bidRemark.value = '';
                if (bidTT) bidTT.value = '';
            }

            // 라인 아이템 테이블 렌더링
            this.renderLineItems();
            this.calculateTotal();
            
            // SAVE/SUBMIT 버튼 상태 업데이트
            this.updateButtonState();
            
            // 입력 필드 변경 감지 이벤트 추가
            this.setupBidFormListeners();
            
            document.getElementById('bidModal').classList.add('active');

        } catch (error) {
            console.error('Failed to load bidding detail:', error);
            alert('입찰 정보를 불러오는데 실패했습니다: ' + error.message);
        }
    },
    
    /**
     * Setup bid form input listeners for edit detection
     */
    setupBidFormListeners() {
        const inputs = ['bidETA', 'bidCarrier', 'bidValidity', 'bidRemark'];
        inputs.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.removeEventListener('input', this.handleBidInputChange);
                el.addEventListener('input', () => this.markAsEdited());
            }
        });
    },

    /**
     * Close bid modal
     */
    closeBidModal() {
        document.getElementById('bidModal').classList.remove('active');
        this.currentBidding = null;
        this.currentBid = null;
        this.lineItems = [];
    },

    // ==========================================
    // LINE ITEMS MANAGEMENT (비용 항목 관리)
    // ==========================================

    /**
     * Render line items table
     */
    renderLineItems() {
        const tbody = document.getElementById('bidLineItemsBody');
        if (!tbody) return;

        if (this.lineItems.length === 0) {
            tbody.innerHTML = `
                <tr class="bid-line-empty-row">
                    <td colspan="10">
                        <div class="bid-line-empty">
                            <i class="fas fa-file-invoice-dollar"></i>
                            <p>비용 항목을 추가해주세요</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.lineItems.map((item, idx) => this.renderLineItemRow(item, idx)).join('');
    },

    /**
     * Render single line item row
     */
    renderLineItemRow(item, idx) {
        const codeOptions = FREIGHT_CODES.map(fc => 
            `<option value="${fc.code}" ${item.code === fc.code ? 'selected' : ''}>${fc.code}</option>`
        ).join('');

        const unitOptions = UNIT_OPTIONS.map(u => 
            `<option value="${u}" ${item.unit === u ? 'selected' : ''}>${u}</option>`
        ).join('');

        const currencyOptions = CURRENCY_OPTIONS.map(c => 
            `<option value="${c}" ${item.currency === c ? 'selected' : ''}>${c}</option>`
        ).join('');

        const taxOptions = TAX_OPTIONS.map(t => 
            `<option value="${t}" ${item.tax === t ? 'selected' : ''}>${t}</option>`
        ).join('');

        const amount = this.calculateLineAmount(item);

        return `
            <tr data-line-idx="${idx}">
                <td class="col-action">
                    <button type="button" class="btn-remove-line" onclick="BiddingList.removeLineItem(${idx})" title="삭제">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
                <td class="col-code">
                    <select class="bid-line-select" onchange="BiddingList.updateLineItem(${idx}, 'code', this.value)">
                        ${codeOptions}
                    </select>
                </td>
                <td class="col-category">
                    <input type="text" class="bid-line-input" value="${item.category}" 
                           onchange="BiddingList.updateLineItem(${idx}, 'category', this.value)" 
                           placeholder="Category">
                </td>
                <td class="col-unit">
                    <select class="bid-line-select" onchange="BiddingList.updateLineItem(${idx}, 'unit', this.value)">
                        <option value="">-</option>
                        ${unitOptions}
                    </select>
                </td>
                <td class="col-qty">
                    <input type="number" class="bid-line-input" value="${item.qty}" min="1"
                           onchange="BiddingList.updateLineItem(${idx}, 'qty', this.value)">
                </td>
                <td class="col-rate">
                    <input type="number" class="bid-line-input" value="${item.rate}" step="0.01" min="0"
                           onchange="BiddingList.updateLineItem(${idx}, 'rate', this.value)" 
                           placeholder="0.00">
                </td>
                <td class="col-currency">
                    <select class="bid-line-select" onchange="BiddingList.updateLineItem(${idx}, 'currency', this.value)">
                        ${currencyOptions}
                    </select>
                </td>
                <td class="col-tax">
                    <select class="bid-line-select" onchange="BiddingList.updateLineItem(${idx}, 'tax', this.value)">
                        ${taxOptions}
                    </select>
                </td>
                <td class="col-vat">
                    <input type="number" class="bid-line-input" value="${item.vat}" step="1" min="0" max="100"
                           onchange="BiddingList.updateLineItem(${idx}, 'vat', this.value)" 
                           ${item.tax === '영세' ? 'disabled' : ''}>
                </td>
                <td class="col-amount">
                    <span class="line-amount" id="lineAmount_${idx}">${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </td>
            </tr>
        `;
    },

    /**
     * Add new line item
     */
    addLineItem() {
        const newId = this.lineItems.length > 0 
            ? Math.max(...this.lineItems.map(i => i.id)) + 1 
            : 0;

        this.lineItems.push({
            id: newId,
            code: 'OFR',
            category: 'Ocean Freight',
            unit: this.currentBidding?.load_type || '20DC',
            qty: 1,
            rate: 0,
            currency: 'USD',
            tax: '영세',
            vat: 0
        });

        this.renderLineItems();
        this.calculateTotal();
    },

    /**
     * Remove line item
     */
    removeLineItem(idx) {
        if (this.lineItems.length <= 1) {
            alert('최소 1개의 비용 항목이 필요합니다.');
            return;
        }

        this.lineItems.splice(idx, 1);
        this.renderLineItems();
        this.calculateTotal();
    },

    /**
     * Update line item value
     */
    updateLineItem(idx, field, value) {
        if (!this.lineItems[idx]) return;

        // 특별 처리: Code 변경 시 Category 자동 채움
        if (field === 'code') {
            const freightCode = FREIGHT_CODES.find(fc => fc.code === value);
            if (freightCode) {
                this.lineItems[idx].code = value;
                this.lineItems[idx].category = freightCode.category;
                this.renderLineItems();
                this.calculateTotal();
                return;
            }
        }

        // Tax 변경 시 VAT 처리
        if (field === 'tax') {
            this.lineItems[idx].tax = value;
            if (value === '영세') {
                this.lineItems[idx].vat = 0;
            } else {
                this.lineItems[idx].vat = 10; // 기본 VAT 10%
            }
            this.renderLineItems();
            this.calculateTotal();
            return;
        }

        // 숫자 필드 처리
        if (['qty', 'rate', 'vat'].includes(field)) {
            this.lineItems[idx][field] = parseFloat(value) || 0;
        } else {
            this.lineItems[idx][field] = value;
        }

        // 금액 재계산
        this.updateLineAmount(idx);
        this.calculateTotal();
    },

    /**
     * Calculate single line amount
     */
    calculateLineAmount(item) {
        const base = (item.qty || 0) * (item.rate || 0);
        const vatAmount = item.tax === '과세' ? base * (item.vat || 0) / 100 : 0;
        return base + vatAmount;
    },

    /**
     * Update single line amount display
     */
    updateLineAmount(idx) {
        const item = this.lineItems[idx];
        if (!item) return;

        const amount = this.calculateLineAmount(item);
        const amountEl = document.getElementById(`lineAmount_${idx}`);
        if (amountEl) {
            amountEl.textContent = amount.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
    },

    /**
     * Calculate total amount from all line items
     */
    calculateTotal() {
        // USD 기준 총합 계산 (다른 통화는 변환 필요 - 현재는 단순 합계)
        const total = this.lineItems.reduce((sum, item) => {
            // USD로 환산 (간단한 예시, 실제로는 환율 API 사용)
            let amount = this.calculateLineAmount(item);
            
            // 다른 통화의 경우 임시 환율 적용 (백엔드 연동 시 실제 환율 사용)
            const exchangeRates = {
                'USD': 1,
                'KRW': 0.00075, // 1 KRW ≈ 0.00075 USD
                'EUR': 1.08,
                'JPY': 0.0067,
                'CNY': 0.14
            };
            
            const rate = exchangeRates[item.currency] || 1;
            return sum + (amount * rate);
        }, 0);
        
        document.getElementById('bidTotalAmount').textContent = total.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        return total;
    },

    /**
     * Get bid data from form
     */
    getBidFormData() {
        // 라인 아이템을 분류하여 기존 API 호환 형태로 변환
        let freightCharge = 0, localCharge = 0, otherCharge = 0;

        this.lineItems.forEach(item => {
            const amount = this.calculateLineAmount(item);
            const code = (item.code || '').toUpperCase();
            
            if (['OFR', 'AFR', 'BAF', 'CAF', 'LSS', 'EBS', 'PSS', 'CIC'].includes(code)) {
                freightCharge += amount;
            } else if (['THC', 'WFG', 'CFS', 'DOC', 'SEAL', 'AMS', 'ENS', 'HANDLING'].includes(code)) {
                localCharge += amount;
            } else {
                otherCharge += amount;
            }
        });

        const lineItemsData = this.lineItems.map((item, idx) => ({
            code: item.code,
            category: item.category,
            unit: item.unit || null,
            qty: item.qty || 1,
            rate: item.rate || 0,
            currency: item.currency || 'USD',
            tax_type: item.tax || '영세',
            vat_percent: item.vat || 0,
            sort_order: idx
        }));

        return {
            bidding_id: this.currentBidding.id,
            total_amount: this.calculateTotal(),
            freight_charge: freightCharge || null,
            local_charge: localCharge || null,
            other_charge: otherCharge || null,
            carrier: document.getElementById('bidCarrier')?.value.trim() || null,
            eta: document.getElementById('bidETA')?.value || null,
            transit_time: document.getElementById('bidTT')?.value || null,
            validity_date: document.getElementById('bidValidity')?.value || null,
            remark: document.getElementById('bidRemark')?.value.trim() || null,
            line_items: lineItemsData
        };
    },

    /**
     * Save bid (draft)
     */
    async saveBid() {
        if (!this.forwarder || !this.currentBidding) return;

        // 최소 유효성 검사
        if (this.lineItems.length === 0) {
            alert('최소 1개의 비용 항목을 입력해주세요.');
            return;
        }

        const bidData = this.getBidFormData();
        console.log('💾 Saving bid data:', bidData);

        try {
            let response;
            
            if (this.currentBid) {
                // Update existing
                response = await fetch(`${QUOTE_API_BASE}/api/bid/${this.currentBid.id}?forwarder_id=${this.forwarder.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({...bidData, status: 'draft'})
                });
            } else {
                // Create new draft
                response = await fetch(`${QUOTE_API_BASE}/api/bid/submit?forwarder_id=${this.forwarder.id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({...bidData, status: 'draft'})
                });
            }

            const result = await response.json();
            if (!response.ok) throw new Error(result.detail);

            // 상태 업데이트
            this.bidSaved = true;
            this.bidEdited = false;
            this.currentBid = result.bid || result;
            this.originalBidData = JSON.stringify(bidData);
            
            this.updateButtonState();
            this.showToast('저장되었습니다.', 'success');

        } catch (error) {
            console.error('Failed to save bid:', error);
            alert('저장에 실패했습니다: ' + error.message);
        }
    },

    /**
     * Submit bid (final)
     */
    async submitBid() {
        if (!this.forwarder || !this.currentBidding) return;

        // SAVE 먼저 해야 함
        if (!this.bidSaved) {
            alert('먼저 Save를 해주세요.');
            return;
        }

        // 수정된 내용이 있으면 저장 먼저
        if (this.bidEdited) {
            alert('수정된 내용이 있습니다. Save를 먼저 해주세요.');
            return;
        }

        // 유효성 검사
        if (this.lineItems.length === 0) {
            alert('최소 1개의 비용 항목을 입력해주세요.');
            return;
        }

        const hasValidRate = this.lineItems.some(item => (item.rate || 0) > 0);
        if (!hasValidRate) {
            alert('최소 1개 항목에 Rate를 입력해주세요.');
            return;
        }

        const total = this.calculateTotal();
        if (total <= 0) {
            alert('입찰 금액을 입력해주세요.');
            return;
        }

        if (!confirm('입찰을 제출하시겠습니까? 제출 후에는 수정이 제한됩니다.')) {
            return;
        }

        const bidData = this.getBidFormData();
        console.log('📤 Submitting bid data:', bidData);

        try {
            let response;
            
            if (this.currentBid) {
                response = await fetch(`${QUOTE_API_BASE}/api/bid/${this.currentBid.id}?forwarder_id=${this.forwarder.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({...bidData, status: 'submitted'})
                });
            } else {
                response = await fetch(`${QUOTE_API_BASE}/api/bid/submit?forwarder_id=${this.forwarder.id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bidData)
                });
            }

            const result = await response.json();
            if (!response.ok) throw new Error(result.detail);

            alert(result.message || '입찰이 제출되었습니다.');
            this.closeBidModal();
            this.loadBiddingList();
            this.loadStats();

        } catch (error) {
            console.error('Failed to submit bid:', error);
            alert('입찰 제출에 실패했습니다: ' + error.message);
        }
    },

    /**
     * Mark bid as edited
     */
    markAsEdited() {
        if (this.bidSaved && !this.bidEdited) {
            this.bidEdited = true;
            this.updateButtonState();
        }
    },

    /**
     * Update SAVE/SUBMIT button state
     */
    updateButtonState() {
        const saveBtn = document.getElementById('bidSaveBtn');
        const saveBtnText = document.getElementById('saveBtnText');
        const submitBtn = document.getElementById('bidSubmitBtn');

        if (saveBtn && saveBtnText) {
            if (this.bidSaved && !this.bidEdited) {
                // 저장됨 상태 -> Edit
                saveBtnText.textContent = 'Edit';
                saveBtn.classList.remove('edited');
            } else if (this.bidEdited) {
                // 수정됨 상태 -> Save (주황색)
                saveBtnText.textContent = 'Save';
                saveBtn.classList.add('edited');
            } else {
                // 초기 상태 -> Save
                saveBtnText.textContent = 'Save';
                saveBtn.classList.remove('edited');
            }
        }

        if (submitBtn) {
            // Save 완료 + 수정 없음 -> Submit 활성화
            submitBtn.disabled = !(this.bidSaved && !this.bidEdited);
        }
    },

    /**
     * Show toast message
     */
    showToast(message, type = 'info') {
        // 간단한 토스트 알림
        const toast = document.createElement('div');
        toast.className = `toast-message ${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 24px;
            background: ${type === 'success' ? '#22c55e' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            font-size: 14px;
            z-index: 10000;
            animation: fadeIn 0.3s ease;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2500);
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
            'expired': '마감됨',
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
