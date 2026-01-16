/**
 * Bidding List Module
 * 포워더를 위한 입찰 목록 및 입찰 기능 (상세 견적서 포함)
 */

// QUOTE_API_BASE는 api.js에서 정의됨 (중복 정의 방지)
// const QUOTE_API_BASE = 'http://localhost:8001';

// ==========================================
// FREIGHT CODE 마스터 데이터 (API에서 로드)
// ==========================================

// Fallback 데이터 (API 실패 시 사용)
const FREIGHT_CODES_FALLBACK = [
    { code: 'FRT', category: 'OCEAN FREIGHT', name_ko: '해상 운임', defaultCurrency: 'USD', units: ['R/TON', 'CNTR', 'G.W', 'C.W', 'Day', 'B/L(AWB)', 'Pallet', 'Box', 'Shipment'] },
    { code: 'AFT', category: 'AIR FREIGHT', name_ko: '항공 운임', defaultCurrency: 'USD', units: ['R/TON', 'CNTR', 'G.W', 'C.W', 'Day', 'B/L(AWB)', 'Pallet', 'Box', 'Shipment'] },
    { code: 'BAF', category: 'BUNKER ADJUSTMENT FACTOR', name_ko: '유류할증료', defaultCurrency: 'USD', units: ['R/TON', 'CNTR', 'G.W', 'C.W', 'Day', 'B/L(AWB)', 'Pallet', 'Box', 'Shipment'] },
    { code: 'THC', category: 'TERMINAL HANDLING CHARGE', name_ko: '터미널 작업비', defaultCurrency: 'KRW', units: ['R/TON', 'CNTR', 'G.W', 'C.W', 'Day', 'B/L(AWB)', 'Pallet', 'Box', 'Shipment'] },
    { code: 'DOC', category: 'DOCUMENT FEE', name_ko: '서류 발급 비용', defaultCurrency: 'KRW', units: ['R/TON', 'CNTR', 'G.W', 'C.W', 'Day', 'B/L(AWB)', 'Pallet', 'Box', 'Shipment'] },
];

const UNIT_OPTIONS_FALLBACK = ['R/TON', 'CNTR', 'G.W', 'C.W', 'Day', 'B/L(AWB)', 'Pallet', 'Box', 'Shipment'];
const CURRENCY_OPTIONS = ['USD', 'KRW', 'EUR', 'JPY', 'CNY'];
const TAX_OPTIONS = ['영세', '과세'];

/**
 * Date Input Utilities - Quotation과 동일한 UI 지원
 */
const DateInputUtils = {
    /**
     * 분리된 입력 필드에서 날짜 값 수집 (ISO 형식 반환)
     * @param {string} prefix - 필드 prefix (예: 'bid-etd', 'bid-eta', 'bid-validity')
     * @param {boolean} withTime - 시간 포함 여부
     * @returns {string|null} ISO 형식 날짜 문자열 또는 null
     */
    getDateValue(prefix, withTime = true) {
        const year = document.getElementById(`${prefix}-year`)?.value;
        const month = document.getElementById(`${prefix}-month`)?.value;
        const day = document.getElementById(`${prefix}-day`)?.value;
        
        if (!year || !month || !day) return null;
        
        const paddedMonth = month.padStart(2, '0');
        const paddedDay = day.padStart(2, '0');
        
        if (withTime) {
            const hour = document.getElementById(`${prefix}-hour`)?.value || '00';
            const minute = document.getElementById(`${prefix}-minute`)?.value || '00';
            const paddedHour = hour.padStart(2, '0');
            const paddedMinute = minute.padStart(2, '0');
            return `${year}-${paddedMonth}-${paddedDay}T${paddedHour}:${paddedMinute}`;
        }
        
        return `${year}-${paddedMonth}-${paddedDay}`;
    },
    
    /**
     * 분리된 입력 필드에 날짜 값 설정
     * @param {string} prefix - 필드 prefix
     * @param {string} dateStr - ISO 형식 날짜 문자열
     * @param {boolean} withTime - 시간 포함 여부
     */
    setDateValue(prefix, dateStr, withTime = true) {
        if (!dateStr) {
            // Clear all fields
            const fields = withTime 
                ? ['year', 'month', 'day', 'hour', 'minute']
                : ['year', 'month', 'day'];
            fields.forEach(f => {
                const el = document.getElementById(`${prefix}-${f}`);
                if (el) el.value = '';
            });
            return;
        }
        
        try {
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) return;
            
            const yearEl = document.getElementById(`${prefix}-year`);
            const monthEl = document.getElementById(`${prefix}-month`);
            const dayEl = document.getElementById(`${prefix}-day`);
            
            if (yearEl) yearEl.value = date.getFullYear();
            if (monthEl) monthEl.value = String(date.getMonth() + 1).padStart(2, '0');
            if (dayEl) dayEl.value = String(date.getDate()).padStart(2, '0');
            
            if (withTime) {
                const hourEl = document.getElementById(`${prefix}-hour`);
                const minuteEl = document.getElementById(`${prefix}-minute`);
                if (hourEl) hourEl.value = String(date.getHours()).padStart(2, '0');
                if (minuteEl) minuteEl.value = String(date.getMinutes()).padStart(2, '0');
            }
        } catch (e) {
            console.warn('Date parsing error:', e);
        }
    },
    
    /**
     * 날짜 입력 필드에 자동 이동 및 계산 이벤트 설정
     * @param {string} prefix - 필드 prefix
     * @param {Function} onChangeCallback - 값 변경 시 콜백
     */
    setupDateInputListeners(prefix, onChangeCallback) {
        const fields = ['year', 'month', 'day', 'hour', 'minute'];
        const maxLengths = { year: 4, month: 2, day: 2, hour: 2, minute: 2 };
        const nextField = { year: 'month', month: 'day', day: 'hour', hour: 'minute', minute: null };
        
        fields.forEach(field => {
            const el = document.getElementById(`${prefix}-${field}`);
            if (!el) return;
            
            // 숫자만 입력 허용
            el.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/[^0-9]/g, '');
                
                // 최대 길이 도달 시 다음 필드로 이동
                if (e.target.value.length >= maxLengths[field] && nextField[field]) {
                    const nextEl = document.getElementById(`${prefix}-${nextField[field]}`);
                    if (nextEl) nextEl.focus();
                }
                
                // 값 변경 콜백 호출
                if (onChangeCallback) onChangeCallback();
            });
            
            // 값 범위 검증 (blur 시)
            el.addEventListener('blur', (e) => {
                let val = parseInt(e.target.value, 10);
                if (isNaN(val)) return;
                
                const limits = {
                    month: { min: 1, max: 12 },
                    day: { min: 1, max: 31 },
                    hour: { min: 0, max: 23 },
                    minute: { min: 0, max: 59 }
                };
                
                if (limits[field]) {
                    if (val < limits[field].min) val = limits[field].min;
                    if (val > limits[field].max) val = limits[field].max;
                    e.target.value = String(val).padStart(maxLengths[field], '0');
                }
            });
        });
    },
    
    /**
     * 날짜 입력 그룹 유효성 검사
     * @param {string} prefix - 필드 prefix
     * @param {boolean} withTime - 시간 포함 여부
     * @returns {boolean} 유효 여부
     */
    isValidDate(prefix, withTime = true) {
        const year = document.getElementById(`${prefix}-year`)?.value;
        const month = document.getElementById(`${prefix}-month`)?.value;
        const day = document.getElementById(`${prefix}-day`)?.value;
        
        if (!year || !month || !day) return false;
        if (year.length !== 4 || month.length === 0 || day.length === 0) return false;
        
        // 유효한 날짜인지 확인
        const date = new Date(year, parseInt(month) - 1, day);
        if (isNaN(date.getTime())) return false;
        if (date.getMonth() + 1 !== parseInt(month) || date.getDate() !== parseInt(day)) return false;
        
        return true;
    }
};

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
    
    // Freight Code 마스터 데이터 (API에서 로드)
    freightCategories: [],  // 카테고리별 운임 코드
    freightCodes: [],       // 전체 운임 코드 flat 배열
    freightUnits: [],       // 단위 목록
    freightCodesLoaded: false,

    /**
     * Initialize the module
     */
    init() {
        console.log('🚀 BiddingList module initialized');
        
        // Check for stored forwarder session
        this.loadSession();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load freight codes from API
        this.loadFreightCodes();
        
        // Load initial data
        this.loadStats();
        this.loadBiddingList();
        
        // Update UI based on login state
        this.updateAuthUI();
    },
    
    /**
     * Load freight codes from API
     * @param {string} shippingType - ocean, air, truck (optional)
     */
    async loadFreightCodes(shippingType = null) {
        try {
            const apiBase = typeof QUOTE_API_BASE !== 'undefined' ? QUOTE_API_BASE : 'http://localhost:8001';
            let url = `${apiBase}/api/freight-codes`;
            if (shippingType) {
                url += `?shipping_type=${shippingType}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            // 카테고리별 데이터 저장
            this.freightCategories = data.categories || [];
            
            // Flat 배열로 변환하여 저장
            this.freightCodes = [];
            this.freightCategories.forEach(cat => {
                (cat.codes || []).forEach(code => {
                    this.freightCodes.push({
                        code: code.code,
                        category: code.name_en,
                        name_ko: code.name_ko,
                        group: code.group_name,
                        categoryCode: cat.code,
                        defaultCurrency: code.default_currency,
                        vatApplicable: code.vat_applicable,
                        units: code.units || []
                    });
                });
            });
            
            // 단위 목록 저장
            this.freightUnits = (data.units || []).map(u => u.code);
            
            this.freightCodesLoaded = true;
            console.log(`✅ Loaded ${this.freightCodes.length} freight codes, ${this.freightUnits.length} units`);
            
        } catch (error) {
            console.warn('⚠️ Failed to load freight codes from API, using fallback:', error.message);
            // Fallback 데이터 사용
            this.freightCodes = FREIGHT_CODES_FALLBACK;
            this.freightUnits = UNIT_OPTIONS_FALLBACK;
            this.freightCodesLoaded = true;
        }
    },
    
    /**
     * Get freight codes for specific shipping type
     * @param {string} shippingType - ocean, air, truck
     * @returns {Array} 해당 타입의 운임 코드 배열
     */
    getFreightCodesForType(shippingType) {
        if (!shippingType || !this.freightCodesLoaded) {
            return this.freightCodes;
        }
        
        // Shipping type에 따라 카테고리 필터링
        // - Ocean: OCEAN + PORT_CHARGES (해상항만) + LOCAL_CHARGES
        // - Air: AIR (ATHC 포함) + LOCAL_CHARGES (PORT_CHARGES 제외 - 해상항만이므로)
        // - Truck: LOCAL_CHARGES
        const typeMapping = {
            'ocean': ['OCEAN', 'PORT_CHARGES', 'LOCAL_CHARGES'],
            'air': ['AIR', 'LOCAL_CHARGES'],  // PORT_CHARGES는 해상항만용, AIR에 ATHC가 있음
            'truck': ['LOCAL_CHARGES']
        };
        
        const allowedCategories = typeMapping[shippingType] || [];
        if (allowedCategories.length === 0) {
            return this.freightCodes;
        }
        
        return this.freightCodes.filter(fc => allowedCategories.includes(fc.categoryCode));
    },
    
    /**
     * Get units for specific freight code
     * @param {string} code - 운임 코드
     * @returns {Array} 허용 단위 배열
     */
    getUnitsForCode(code) {
        const freightCode = this.freightCodes.find(fc => fc.code === code);
        if (freightCode && freightCode.units && freightCode.units.length > 0) {
            return freightCode.units;
        }
        return this.freightUnits.length > 0 ? this.freightUnits : UNIT_OPTIONS_FALLBACK;
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
     * Load stored session - Auth.js 연동
     * Auth.js의 aal_user와 기존 forwarder 세션 모두 확인
     */
    loadSession() {
        // 1. Auth.js 세션 확인 (우선)
        if (window.Auth && Auth.user && Auth.user.user_type === 'forwarder') {
            this.forwarder = Auth.user;
            console.log('✅ Session restored from Auth.js for:', this.forwarder.company);
            return;
        }
        
        // 2. Auth.js localStorage 직접 확인
        const authStored = localStorage.getItem('aal_user');
        if (authStored) {
            try {
                const authUser = JSON.parse(authStored);
                if (authUser.user_type === 'forwarder') {
                    this.forwarder = authUser;
                    console.log('✅ Session restored from aal_user for:', this.forwarder.company);
                    return;
                }
            } catch (e) {
                console.warn('Failed to parse aal_user');
            }
        }
        
        // 3. 기존 forwarder 세션 확인 (마이그레이션 호환)
        const stored = localStorage.getItem('forwarder');
        if (stored) {
            try {
                this.forwarder = JSON.parse(stored);
                console.log('✅ Session restored from forwarder for:', this.forwarder.company);
                // 기존 세션을 Auth.js 형식으로 마이그레이션
                this.forwarder.user_type = 'forwarder';
                localStorage.setItem('aal_user', JSON.stringify(this.forwarder));
                localStorage.removeItem('forwarder'); // 기존 키 제거
            } catch (e) {
                localStorage.removeItem('forwarder');
            }
        }
    },

    /**
     * Sync session with Auth.js
     * Auth.js 상태 변경 시 호출
     */
    syncWithAuth() {
        if (window.Auth && Auth.user && Auth.user.user_type === 'forwarder') {
            this.forwarder = Auth.user;
        } else {
            this.forwarder = null;
        }
        this.updateAuthUI();
        this.loadBiddingList();
    },

    /**
     * Update auth UI based on login state
     */
    updateAuthUI() {
        // Auth.js 세션 다시 확인
        if (!this.forwarder && window.Auth && Auth.user && Auth.user.user_type === 'forwarder') {
            this.forwarder = Auth.user;
        }
        
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
            // Logged out state - 헤더의 로그인 버튼 사용
            actionsDiv.innerHTML = '';
            forwarderBar.style.display = 'none';
        }
        
        // 테이블 헤더의 "입찰참여" 컬럼명 변경 (화주인 경우)
        this.updateTableHeaderForUserType();
    },
    
    /**
     * Update table header based on user type
     * 화주(shipper)인 경우 "입찰참여" → "상세" 로 변경
     */
    updateTableHeaderForUserType() {
        const isShipper = window.Auth && Auth.user && Auth.user.user_type === 'shipper';
        const tableHeaders = document.querySelectorAll('.bidding-table thead th');
        
        // 마지막 컬럼이 "입찰참여" 또는 "상세"
        if (tableHeaders.length > 0) {
            const lastHeader = tableHeaders[tableHeaders.length - 1];
            lastHeader.textContent = isShipper ? '상세' : '입찰참여';
        }
    },

    /**
     * Open auth modal - Auth.js 사용 (포워더 전용)
     */
    openAuthModal() {
        if (window.Auth) {
            // Bidding은 포워더 전용이므로 포워더 로그인 폼 바로 표시
            Auth.openModalForForwarder();
        } else {
            alert('인증 모듈을 불러올 수 없습니다.');
        }
    },

    /**
     * Close auth modal - Auth.js 사용
     */
    closeAuthModal() {
        if (window.Auth) {
            Auth.closeModal();
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
        const isExpired = item.deadline && this.isDeadlinePassed(item.deadline);
        
        // Determine effective status (마감일이 지났으면 expired로 처리)
        let effectiveStatus = item.status;
        if (item.status === 'open' && isExpired) {
            effectiveStatus = 'expired';
        }
        
        // Determine action button
        let actionBtn = '';
        
        // 화주(shipper)인 경우 입찰 버튼 대신 상세보기만 표시
        const isShipper = window.Auth && Auth.user && Auth.user.user_type === 'shipper';
        
        if (isShipper) {
            // 화주는 입찰 참여 불가 - 상세보기만 가능
            actionBtn = `<button class="action-btn secondary" onclick="BiddingList.openDetailModal('${item.bidding_no}')">
                상세보기
            </button>`;
        } else if (effectiveStatus === 'open') {
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

        // Format average bid price
        // 평균 입찰가 정수화
        const avgPriceFormatted = item.avg_bid_price 
            ? `$${Math.round(item.avg_bid_price).toLocaleString('en-US')}`
            : '-';

        return `
            <tr class="${rowClass}">
                <td>
                    <span class="bidding-no ${isExpired ? 'expired-text' : ''}" onclick="BiddingList.openDetailModal('${item.bidding_no}')">
                        ${item.bidding_no}
                    </span>
                </td>
                <td>${item.customer_company}</td>
                <td>
                    <span class="port-cell">${this.formatPort(item.pol, item.pol_name)}</span>
                </td>
                <td>
                    <span class="port-cell">${this.formatPort(item.pod, item.pod_name)}</span>
                </td>
                <td>
                    <span class="type-badge ${item.shipping_type}">
                        <i class="fas fa-${this.getShippingIcon(item.shipping_type)}"></i>
                        ${item.shipping_type.toUpperCase()} / ${item.load_type.toUpperCase()}
                    </span>
                </td>
                <td>
                    <span class="cargo-summary">${item.cargo_summary || '-'}</span>
                </td>
                <td>${this.formatDate(item.etd)}</td>
                <td>
                    <span class="status-badge ${effectiveStatus}">${this.getStatusLabel(effectiveStatus)}</span>
                </td>
                <td>
                    <span class="bid-count">${item.bid_count}</span>
                </td>
                <td>
                    <span class="avg-price">${avgPriceFormatted}</span>
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

        // Transport Section - ETD 초기화 (분리된 입력 필드 사용)
        DateInputUtils.setDateValue('bid-etd', detail.etd, true);
        // hidden input에도 설정
        const bidETD = document.getElementById('bidETD');
        if (bidETD) bidETD.value = detail.etd ? this.formatDateTimeLocal(detail.etd) : '';

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
     * Format datetime for datetime-local input (YYYY-MM-DDTHH:MM)
     */
    formatDateTimeLocal(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return '';
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    },

    /**
     * Calculate Transit Time (일 단위)
     */
    calculateTT() {
        const ttEl = document.getElementById('bidTT');
        if (!ttEl) return;
        
        // DateInputUtils를 사용하여 날짜 값 가져오기
        const etdValue = DateInputUtils.getDateValue('bid-etd', true);
        const etaValue = DateInputUtils.getDateValue('bid-eta', true);
        
        // hidden input에도 값 업데이트
        const bidETD = document.getElementById('bidETD');
        const bidETA = document.getElementById('bidETA');
        if (bidETD) bidETD.value = etdValue || '';
        if (bidETA) bidETA.value = etaValue || '';
        
        if (etdValue && etaValue) {
            const etd = new Date(etdValue);
            const eta = new Date(etaValue);
            // 일 단위 계산 (시간 무시, 날짜만 비교)
            const etdDate = new Date(etd.getFullYear(), etd.getMonth(), etd.getDate());
            const etaDate = new Date(eta.getFullYear(), eta.getMonth(), eta.getDate());
            const days = Math.round((etaDate - etdDate) / (1000 * 60 * 60 * 24));
            ttEl.value = days >= 0 ? `${days}` : '-';
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
                
                // Transport Details - 분리된 입력 필드 사용
                const bidCarrier = document.getElementById('bidCarrier');
                const bidRemark = document.getElementById('bidRemark');
                
                // ETD: 포워더가 제안한 ETD 또는 원본 ETD
                const etdValue = detail.my_bid.etd || detail.etd;
                DateInputUtils.setDateValue('bid-etd', etdValue, true);
                const bidETD = document.getElementById('bidETD');
                if (bidETD) bidETD.value = etdValue ? this.formatDateTimeLocal(etdValue) : '';
                
                // ETA: 분리된 입력 필드 사용
                DateInputUtils.setDateValue('bid-eta', detail.my_bid.eta, true);
                const bidETA = document.getElementById('bidETA');
                if (bidETA) bidETA.value = detail.my_bid.eta ? this.formatDateTimeLocal(detail.my_bid.eta) : '';
                
                // Validity: 날짜만 (시간 없음)
                DateInputUtils.setDateValue('bid-validity', detail.my_bid.validity_date, false);
                const bidValidity = document.getElementById('bidValidity');
                if (bidValidity) bidValidity.value = detail.my_bid.validity_date ? detail.my_bid.validity_date.split('T')[0] : '';
                
                if (bidCarrier) bidCarrier.value = detail.my_bid.carrier || '';
                if (bidRemark) bidRemark.value = detail.my_bid.remark || '';
                
                // T/T 계산
                this.calculateTT();
                
                // 기존 bid의 line_items 로드
                if (detail.my_bid.line_items && detail.my_bid.line_items.length > 0) {
                    this.lineItems = detail.my_bid.line_items.map((item, idx) => ({
                        id: idx,
                        code: item.code,
                        category: item.category,
                        group: item.group || 'ETC',
                        categoryCode: item.category_code || 'OTHER',
                        rateGroup: item.rate_group || 'FREIGHT',  // 고정 그룹 키
                        unit: item.unit || '',
                        qty: item.qty || 1,
                        rate: item.rate || 0,
                        currency: item.currency || 'USD',
                        tax: item.tax_type || '영세',
                        vat: item.vat_percent || 0
                    }));
                } else {
                    // 기존 단순 금액을 라인 아이템으로 변환 (rateGroup 포함)
                    this.lineItems = [];
                    if (detail.my_bid.freight_charge) {
                        this.lineItems.push({
                            id: 0,
                            code: detail.shipping_type === 'air' ? 'AFT' : 'FRT',
                            category: detail.shipping_type === 'air' ? 'Air Freight' : 'Ocean Freight',
                            group: 'FREIGHT',
                            categoryCode: detail.shipping_type === 'air' ? 'AIR' : 'OCEAN',
                            rateGroup: 'FREIGHT',
                            unit: detail.load_type || 'CNTR',
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
                            group: 'HANDLING',
                            categoryCode: 'PORT_CHARGES',
                            rateGroup: 'ORIGIN_PORT',
                            unit: detail.load_type || 'CNTR',
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
                            code: 'DOC',
                            category: 'Document Fee',
                            group: 'DOCUMENT',
                            categoryCode: 'LOCAL_CHARGES',
                            rateGroup: 'ORIGIN_LOCAL',
                            unit: 'B/L(AWB)',
                            qty: 1,
                            rate: detail.my_bid.other_charge,
                            currency: 'USD',
                            tax: '영세',
                            vat: 0
                        });
                    }
                }
                
            } else {
                // Clear form - 빈 상태로 시작 (각 그룹에서 Add 버튼으로 추가)
                this.currentBid = null;
                this.lineItems = [];
                
                // Clear transport fields (ETD는 원본 값 유지)
                const bidCarrier = document.getElementById('bidCarrier');
                const bidRemark = document.getElementById('bidRemark');
                const bidTT = document.getElementById('bidTT');
                
                // ETD는 원본 요청 값으로 초기화 (수정 가능) - 분리된 입력 필드 사용
                DateInputUtils.setDateValue('bid-etd', detail.etd, true);
                const bidETD = document.getElementById('bidETD');
                if (bidETD) bidETD.value = detail.etd ? this.formatDateTimeLocal(detail.etd) : '';
                
                // ETA, Validity 초기화
                DateInputUtils.setDateValue('bid-eta', null, true);
                DateInputUtils.setDateValue('bid-validity', null, false);
                const bidETA = document.getElementById('bidETA');
                const bidValidity = document.getElementById('bidValidity');
                if (bidETA) bidETA.value = '';
                if (bidValidity) bidValidity.value = '';
                
                if (bidCarrier) bidCarrier.value = '';
                if (bidRemark) bidRemark.value = '';
                if (bidTT) bidTT.value = '';
            }

            // 조건에 따라 그룹 가시성 업데이트
            this.updateGroupVisibility();
            
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
        // 기본 입력 필드
        const inputs = ['bidCarrier', 'bidRemark'];
        inputs.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.removeEventListener('input', this.handleBidInputChange);
                el.addEventListener('input', () => this.markAsEdited());
            }
        });
        
        // 날짜 입력 필드 (분리된 구조)에 이벤트 리스너 설정
        const dateCallback = () => {
            this.calculateTT();
            this.markAsEdited();
        };
        
        DateInputUtils.setupDateInputListeners('bid-etd', dateCallback);
        DateInputUtils.setupDateInputListeners('bid-eta', dateCallback);
        DateInputUtils.setupDateInputListeners('bid-validity', () => {
            // validity hidden input 업데이트
            const validityValue = DateInputUtils.getDateValue('bid-validity', false);
            const bidValidity = document.getElementById('bidValidity');
            if (bidValidity) bidValidity.value = validityValue || '';
            this.markAsEdited();
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
     * 5개 고정 그룹 정의
     * ORIGIN_LOCAL → ORIGIN_PORT → FREIGHT → DEST_PORT → DEST_LOCAL
     */
    RATE_GROUPS: ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT', 'DEST_PORT', 'DEST_LOCAL'],
    
    /**
     * 그룹별 허용 카테고리 코드 매핑
     */
    GROUP_CATEGORY_MAP: {
        'ORIGIN_LOCAL': ['LOCAL_CHARGES'],
        'ORIGIN_PORT': ['PORT_CHARGES'],
        'FREIGHT': ['OCEAN', 'AIR'],
        'DEST_PORT': ['PORT_CHARGES'],
        'DEST_LOCAL': ['LOCAL_CHARGES']
    },
    
    /**
     * 조건별 그룹 출력 규칙
     * [shipping_type][trade_mode][incoterms] = 표시할 그룹 배열
     */
    GROUP_DISPLAY_RULES: {
        'air': {
            'export': {
                'CIF': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT'],
                'CFR': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT'],
                'FOB': ['ORIGIN_LOCAL', 'ORIGIN_PORT'],
                'EXW': [],
                'DAP': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT', 'DEST_PORT', 'DEST_LOCAL'],
                'DDP': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT', 'DEST_PORT', 'DEST_LOCAL']
            },
            'import': {
                'CIF': [],
                'CFR': [],
                'FOB': ['FREIGHT', 'DEST_LOCAL'],
                'EXW': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT', 'DEST_PORT', 'DEST_LOCAL'],
                'DAP': [],
                'DDP': []
            }
        },
        'ocean': {
            'export': {
                'CIF': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT'],
                'CFR': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT'],
                'FOB': ['ORIGIN_LOCAL', 'ORIGIN_PORT'],
                'EXW': [],
                'DAP': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT', 'DEST_PORT', 'DEST_LOCAL'],
                'DDP': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT', 'DEST_PORT', 'DEST_LOCAL']
            },
            'import': {
                'CIF': [],
                'CFR': [],
                'FOB': ['FREIGHT', 'DEST_LOCAL'],
                'EXW': ['ORIGIN_LOCAL', 'ORIGIN_PORT', 'FREIGHT', 'DEST_PORT', 'DEST_LOCAL'],
                'DAP': ['DEST_LOCAL'],
                'DDP': ['DEST_LOCAL']
            }
        }
    },
    
    /**
     * 현재 조건에 따라 표시할 그룹 목록 반환
     * @returns {Array} 표시할 그룹 키 배열
     */
    getVisibleGroups() {
        const tradeMode = this.currentBidding?.trade_mode?.toLowerCase() || 'export';
        const shippingType = this.currentBidding?.shipping_type?.toLowerCase() || 'ocean';
        const incoterms = this.currentBidding?.incoterms?.toUpperCase() || 'FOB';
        
        const rules = this.GROUP_DISPLAY_RULES[shippingType]?.[tradeMode]?.[incoterms];
        
        // 규칙이 없으면 기본값 반환 (FREIGHT만)
        if (!rules) {
            console.warn(`No display rule for: ${shippingType}/${tradeMode}/${incoterms}, using default`);
            return ['FREIGHT'];
        }
        
        return rules;
    },
    
    /**
     * 조건에 따라 그룹 표시/숨김 처리
     */
    updateGroupVisibility() {
        const visibleGroups = this.getVisibleGroups();
        
        console.log(`📋 Visible groups for ${this.currentBidding?.trade_mode}/${this.currentBidding?.shipping_type}/${this.currentBidding?.incoterms}:`, visibleGroups);
        
        this.RATE_GROUPS.forEach(groupKey => {
            const groupEl = document.getElementById(`rateGroup_${groupKey}`);
            if (groupEl) {
                const isVisible = visibleGroups.includes(groupKey);
                groupEl.style.display = isVisible ? 'block' : 'none';
            }
        });
    },
    
    /**
     * Render line items - 5개 고정 그룹 섹션에 각각 렌더링
     */
    renderLineItems() {
        // 각 그룹별로 해당하는 라인 아이템을 필터링하여 렌더링
        this.RATE_GROUPS.forEach(groupKey => {
            this.renderGroupItems(groupKey);
        });
        
        // Freight 섹션 타이틀 업데이트 (shipping_type에 따라)
        this.updateFreightTitle();
        
        // 소계 및 총계 업데이트
        this.calculateGroupSubtotals();
    },
    
    /**
     * 특정 그룹의 라인 아이템만 렌더링
     * @param {string} groupKey - ORIGIN_LOCAL, ORIGIN_PORT, FREIGHT, DEST_PORT, DEST_LOCAL
     */
    renderGroupItems(groupKey) {
        const tbody = document.getElementById(`rateGroupBody_${groupKey}`);
        if (!tbody) return;
        
        // 해당 그룹의 아이템만 필터링
        const groupItems = this.lineItems.filter((item, idx) => {
            return item.rateGroup === groupKey;
        });
        
        if (groupItems.length === 0) {
            tbody.innerHTML = `
                <tr class="rate-group-empty-row">
                    <td colspan="9">
                        <div class="rate-group-empty">
                            <i class="fas fa-plus-circle"></i>
                            <span>항목을 추가하려면 Add 버튼을 클릭하세요</span>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }
        
        // 라인 아이템 렌더링
        tbody.innerHTML = groupItems.map(item => {
            const originalIdx = this.lineItems.indexOf(item);
            return this.renderLineItemRow(item, originalIdx, groupKey);
        }).join('');
    },
    
    /**
     * Freight 섹션 타이틀 업데이트 (shipping_type에 따라)
     */
    updateFreightTitle() {
        const titleEl = document.getElementById('freightTitle');
        const iconEl = document.getElementById('freightIcon');
        
        if (!titleEl || !iconEl) return;
        
        const shippingType = this.currentBidding?.shipping_type || 'ocean';
        
        if (shippingType === 'air') {
            titleEl.textContent = 'Air Freight';
            iconEl.className = 'fas fa-plane';
        } else {
            titleEl.textContent = 'Ocean Freight';
            iconEl.className = 'fas fa-ship';
        }
    },
    
    /**
     * 각 그룹별 소계 및 전체 합계 계산
     */
    calculateGroupSubtotals() {
        let grandTotal = 0;
        
        this.RATE_GROUPS.forEach(groupKey => {
            const groupItems = this.lineItems.filter(item => item.rateGroup === groupKey);
            const subtotal = groupItems.reduce((sum, item) => sum + this.calculateLineAmount(item), 0);
            
            const subtotalEl = document.getElementById(`subtotal_${groupKey}`);
            if (subtotalEl) {
                subtotalEl.textContent = subtotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
            
            grandTotal += subtotal;
        });
        
        // 전체 합계 업데이트
        const totalEl = document.getElementById('bidTotalAmount');
        if (totalEl) {
            totalEl.textContent = grandTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
    },
    
    /**
     * 그룹별 허용되는 운임 코드 가져오기
     * @param {string} groupKey - ORIGIN_LOCAL, ORIGIN_PORT, FREIGHT, DEST_PORT, DEST_LOCAL
     * @returns {Array} 허용되는 freight codes
     */
    getCodesForGroup(groupKey) {
        const shippingType = this.currentBidding?.shipping_type || 'ocean';
        const allowedCategories = this.GROUP_CATEGORY_MAP[groupKey] || [];
        
        // FREIGHT 그룹의 경우 shipping_type에 따라 필터링
        let filteredCategories = allowedCategories;
        if (groupKey === 'FREIGHT') {
            filteredCategories = shippingType === 'air' ? ['AIR'] : ['OCEAN'];
        }
        
        // 해당 카테고리의 코드만 필터링
        return this.freightCodes.filter(fc => filteredCategories.includes(fc.categoryCode));
    },

    /**
     * Render single line item row
     * @param {Object} item - 라인 아이템 데이터
     * @param {number} idx - lineItems 배열에서의 인덱스
     * @param {string} groupKey - 해당 그룹 키 (ORIGIN_LOCAL 등)
     */
    renderLineItemRow(item, idx, groupKey) {
        // 해당 그룹에서 허용되는 운임 코드만 가져오기
        const availableCodes = this.getCodesForGroup(groupKey || item.rateGroup);
        
        const codeOptions = availableCodes.map(fc => 
            `<option value="${fc.code}" ${item.code === fc.code ? 'selected' : ''}>${fc.code} - ${fc.name_ko || fc.category}</option>`
        ).join('');

        // 선택된 코드의 허용 단위
        const availableUnits = this.getUnitsForCode(item.code);
        const unitOptions = availableUnits.map(u => 
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
     * Add new line item to specific group
     * @param {string} groupKey - ORIGIN_LOCAL, ORIGIN_PORT, FREIGHT, DEST_PORT, DEST_LOCAL
     */
    addLineItemToGroup(groupKey) {
        const newId = this.lineItems.length > 0 
            ? Math.max(...this.lineItems.map(i => i.id)) + 1 
            : 0;

        // 해당 그룹에서 허용되는 운임 코드 가져오기
        const availableCodes = this.getCodesForGroup(groupKey);
        const shippingType = this.currentBidding?.shipping_type || 'ocean';
        
        // 그룹별 기본 코드 선택
        let defaultCode = null;
        
        if (groupKey === 'FREIGHT') {
            // FREIGHT 그룹: shipping_type에 따라
            const defaultCodeStr = shippingType === 'air' ? 'AFT' : 'FRT';
            defaultCode = availableCodes.find(fc => fc.code === defaultCodeStr);
        } else if (groupKey === 'ORIGIN_LOCAL' || groupKey === 'DEST_LOCAL') {
            // LOCAL: DOC 또는 첫 번째 코드
            defaultCode = availableCodes.find(fc => fc.code === 'DOC') || availableCodes[0];
        } else if (groupKey === 'ORIGIN_PORT' || groupKey === 'DEST_PORT') {
            // PORT: THC 또는 첫 번째 코드
            defaultCode = availableCodes.find(fc => fc.code === 'THC') || availableCodes[0];
        }
        
        // Fallback: 첫 번째 가용 코드
        if (!defaultCode && availableCodes.length > 0) {
            defaultCode = availableCodes[0];
        }
        
        // 최종 Fallback
        if (!defaultCode) {
            defaultCode = {
                code: 'ETC',
                category: 'ETC',
                group: 'ETC',
                categoryCode: 'OTHER',
                defaultCurrency: 'USD',
                units: this.freightUnits
            };
        }
        
        // 기본 단위 선택
        const defaultUnit = defaultCode.units && defaultCode.units.length > 0 
            ? defaultCode.units[0] 
            : (this.freightUnits[0] || 'CNTR');

        this.lineItems.push({
            id: newId,
            code: defaultCode.code,
            category: defaultCode.category,
            group: defaultCode.group || 'ETC',
            categoryCode: defaultCode.categoryCode || 'OTHER',
            rateGroup: groupKey,  // 새 필드: 어떤 그룹에 속하는지
            unit: defaultUnit,
            qty: 1,
            rate: 0,
            currency: defaultCode.defaultCurrency || 'USD',
            tax: '영세',
            vat: 0
        });

        this.renderLineItems();
        this.calculateTotal();
    },
    
    /**
     * (레거시) 기존 addLineItem 호환용 - FREIGHT 그룹에 추가
     */
    addLineItem() {
        this.addLineItemToGroup('FREIGHT');
    },

    /**
     * Remove line item
     */
    removeLineItem(idx) {
        // 해당 항목 삭제
        this.lineItems.splice(idx, 1);
        this.renderLineItems();
        this.calculateTotal();
    },

    /**
     * Update line item value
     */
    updateLineItem(idx, field, value) {
        if (!this.lineItems[idx]) return;

        // 특별 처리: Code 변경 시 Category, Group, CategoryCode 자동 채움 및 통화/단위 설정
        if (field === 'code') {
            const freightCode = this.freightCodes.find(fc => fc.code === value);
            if (freightCode) {
                this.lineItems[idx].code = value;
                this.lineItems[idx].category = freightCode.category;
                // Group, CategoryCode 자동 설정
                this.lineItems[idx].group = freightCode.group || 'ETC';
                this.lineItems[idx].categoryCode = freightCode.categoryCode || 'OTHER';
                // 기본 통화 설정
                if (freightCode.defaultCurrency) {
                    this.lineItems[idx].currency = freightCode.defaultCurrency;
                }
                // 첫 번째 허용 단위로 설정 (현재 단위가 허용 목록에 없으면)
                if (freightCode.units && freightCode.units.length > 0) {
                    if (!freightCode.units.includes(this.lineItems[idx].unit)) {
                        this.lineItems[idx].unit = freightCode.units[0];
                    }
                }
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
     * Calculate total amount from all line items (각 그룹별 소계 포함)
     */
    calculateTotal() {
        // 환율 정의
        const exchangeRates = {
            'USD': 1,
            'KRW': 0.00075, // 1 KRW ≈ 0.00075 USD
            'EUR': 1.08,
            'JPY': 0.0067,
            'CNY': 0.14
        };
        
        let grandTotal = 0;
        
        // 각 그룹별 소계 계산 및 업데이트
        this.RATE_GROUPS.forEach(groupKey => {
            const groupItems = this.lineItems.filter(item => item.rateGroup === groupKey);
            const subtotal = groupItems.reduce((sum, item) => {
                let amount = this.calculateLineAmount(item);
                const rate = exchangeRates[item.currency] || 1;
                return sum + (amount * rate);
            }, 0);
            
            // 소계 표시 업데이트
            const subtotalEl = document.getElementById(`subtotal_${groupKey}`);
            if (subtotalEl) {
                subtotalEl.textContent = subtotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
            
            grandTotal += subtotal;
        });
        
        // 전체 합계 업데이트
        const totalEl = document.getElementById('bidTotalAmount');
        if (totalEl) {
            totalEl.textContent = grandTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        return grandTotal;
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

        // 날짜 값을 DateInputUtils에서 직접 가져오기
        const etdValue = DateInputUtils.getDateValue('bid-etd', true);
        const etaValue = DateInputUtils.getDateValue('bid-eta', true);
        const validityValue = DateInputUtils.getDateValue('bid-validity', false);

        return {
            bidding_id: this.currentBidding.id,
            total_amount: this.calculateTotal(),
            freight_charge: freightCharge || null,
            local_charge: localCharge || null,
            other_charge: otherCharge || null,
            carrier: document.getElementById('bidCarrier')?.value.trim() || null,
            etd: etdValue || null,  // 포워더 제안 ETD
            eta: etaValue || null,
            transit_time: document.getElementById('bidTT')?.value || null,
            validity_date: validityValue || null,
            remark: document.getElementById('bidRemark')?.value.trim() || null,
            line_items: lineItemsData
        };
    },

    /**
     * Validate bid form with visual guide
     * @param {boolean} forSubmit - true for submit validation, false for save validation
     * @returns {Object} { valid: boolean, errors: string[], firstErrorElement: Element }
     */
    validateBidForm(forSubmit = false) {
        const errors = [];
        let firstErrorElement = null;
        
        // 모든 에러 표시 초기화
        document.querySelectorAll('.qr-section.error').forEach(el => el.classList.remove('error'));
        document.querySelectorAll('.validation-highlight').forEach(el => el.classList.remove('validation-highlight'));
        
        // 1. Rates 섹션 - 최소 1개 비용 항목 필수
        const ratesSection = document.querySelector('.rates-section');
        if (this.lineItems.length === 0) {
            errors.push('최소 1개의 비용 항목을 입력해주세요.');
            if (ratesSection) {
                ratesSection.classList.add('error');
                if (!firstErrorElement) firstErrorElement = ratesSection;
            }
        }
        
        // Submit 시 추가 검증
        if (forSubmit) {
            // 2. Rate 값이 있는 항목이 최소 1개 필요
            const hasValidRate = this.lineItems.some(item => (item.rate || 0) > 0);
            if (this.lineItems.length > 0 && !hasValidRate) {
                errors.push('최소 1개 항목에 Rate를 입력해주세요.');
                if (ratesSection) {
                    ratesSection.classList.add('error');
                    if (!firstErrorElement) firstErrorElement = ratesSection;
                }
            }
            
            // 3. Total Amount 검증
            const total = this.calculateTotal();
            if (total <= 0) {
                errors.push('입찰 금액이 0보다 커야 합니다.');
                if (ratesSection) {
                    ratesSection.classList.add('error');
                    if (!firstErrorElement) firstErrorElement = ratesSection;
                }
            }
            
            // 4. ETD 필수 (Transport Details) - DateInputUtils 사용
            const transportSection = document.querySelector('.transport-section');
            const etdValue = DateInputUtils.getDateValue('bid-etd', true);
            const etdInputGroup = document.getElementById('bid-etd-input-group');
            if (!etdValue || !DateInputUtils.isValidDate('bid-etd', true)) {
                errors.push('ETD (예상 출발일)를 입력해주세요.');
                if (transportSection) {
                    transportSection.classList.add('error');
                    if (etdInputGroup) {
                        etdInputGroup.closest('.date-input-wrapper')?.classList.add('error');
                    }
                    if (!firstErrorElement) firstErrorElement = transportSection;
                }
            }
            
            // 5. ETA 필수 - DateInputUtils 사용
            const etaValue = DateInputUtils.getDateValue('bid-eta', true);
            const etaInputGroup = document.getElementById('bid-eta-input-group');
            if (!etaValue || !DateInputUtils.isValidDate('bid-eta', true)) {
                errors.push('ETA (예상 도착일)를 입력해주세요.');
                if (transportSection) {
                    transportSection.classList.add('error');
                    if (etaInputGroup) {
                        etaInputGroup.closest('.date-input-wrapper')?.classList.add('error');
                    }
                    if (!firstErrorElement) firstErrorElement = transportSection;
                }
            }
            
            // 6. Validity Date 필수 - DateInputUtils 사용
            const validityValue = DateInputUtils.getDateValue('bid-validity', false);
            const validityInputGroup = document.getElementById('bid-validity-input-group');
            if (!validityValue || !DateInputUtils.isValidDate('bid-validity', false)) {
                errors.push('견적 유효기간을 입력해주세요.');
                if (transportSection) {
                    transportSection.classList.add('error');
                    if (validityInputGroup) {
                        validityInputGroup.closest('.date-input-wrapper')?.classList.add('error');
                    }
                    if (!firstErrorElement) firstErrorElement = transportSection;
                }
            }
        }
        
        return {
            valid: errors.length === 0,
            errors,
            firstErrorElement
        };
    },
    
    /**
     * Show validation error modal
     */
    showValidationError(errors, firstErrorElement) {
        // 첫 번째 에러 요소로 스크롤
        if (firstErrorElement) {
            firstErrorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        // 에러 메시지 표시
        const errorList = errors.map(e => `• ${e}`).join('\n');
        alert(`입력 정보를 확인해주세요:\n\n${errorList}`);
    },

    /**
     * Save bid (draft)
     */
    async saveBid() {
        if (!this.forwarder || !this.currentBidding) return;

        // 유효성 검사 (Save는 최소 검증만)
        const validation = this.validateBidForm(false);
        if (!validation.valid) {
            this.showValidationError(validation.errors, validation.firstErrorElement);
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

        // 전체 유효성 검사 (Submit은 모든 필수 항목 검증)
        const validation = this.validateBidForm(true);
        if (!validation.valid) {
            this.showValidationError(validation.errors, validation.firstErrorElement);
            return;
        }

        // 수정된 내용이 있으면 저장 먼저
        if (this.bidEdited || !this.bidSaved) {
            // 자동 저장 후 제출
            await this.saveBid();
            if (!this.bidSaved) return; // 저장 실패 시 중단
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
     * Open detail modal - Quote Summary Style
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
            
            // Cargo summary 생성
            let cargoSummary = '-';
            if (detail.cargo_details && detail.cargo_details.length > 0) {
                const cargo = detail.cargo_details;
                if (detail.load_type === 'FCL') {
                    cargoSummary = cargo.map(c => `${c.container_type} x ${c.quantity}`).join(', ');
                } else {
                    const totalPcs = cargo.reduce((sum, c) => sum + (c.quantity || 0), 0);
                    const totalWeight = cargo.reduce((sum, c) => sum + (c.gross_weight || 0), 0);
                    const totalCbm = cargo.reduce((sum, c) => sum + (c.cbm || 0), 0);
                    cargoSummary = `${totalPcs} PCS / ${totalWeight.toLocaleString()} KG / ${totalCbm.toFixed(1)} CBM`;
                }
            }

            // Additional services summary
            let additionalSummary = [];
            if (detail.export_customs) additionalSummary.push('Export CC');
            if (detail.import_customs) additionalSummary.push('Import CC');
            if (detail.pickup_required) additionalSummary.push('Pickup');
            if (detail.delivery_required) additionalSummary.push('Delivery');
            if (detail.marine_insurance) additionalSummary.push('Insurance');
            
            let html = `
                <div class="quote-summary-box">
                    <div class="quote-summary-title">Quote Summary</div>
                    <ul class="quote-summary-list">
                        <li>
                            <span class="qs-label">Customer</span>
                            <span class="qs-value highlight">${detail.customer_company}</span>
                        </li>
                        <li>
                            <span class="qs-label">Trade Mode</span>
                            <span class="qs-value">${detail.trade_mode ? detail.trade_mode.toUpperCase() : '-'}</span>
                        </li>
                        <li>
                            <span class="qs-label">Shipping Type</span>
                            <span class="qs-value">${detail.shipping_type ? detail.shipping_type.toUpperCase() : '-'}</span>
                        </li>
                        <li>
                            <span class="qs-label">Load Type</span>
                            <span class="qs-value">${detail.load_type || '-'}</span>
                        </li>
                        <li>
                            <span class="qs-label">Route</span>
                            <span class="qs-value highlight">${detail.pol} → ${detail.pod}</span>
                        </li>
                        <li>
                            <span class="qs-label">Shipping Schedule</span>
                            <span class="qs-value">ETD: ${this.formatDate(detail.etd)}<br>ETA: ${detail.eta ? this.formatDate(detail.eta) : '-'}</span>
                        </li>
                        <li>
                            <span class="qs-label">Incoterms</span>
                            <span class="qs-value">${detail.incoterms || '-'}</span>
                        </li>
                        <li>
                            <span class="qs-label">Cargo Details</span>
                            <span class="qs-value">${cargoSummary}</span>
                        </li>
                        <li>
                            <span class="qs-label">Additional Services</span>
                            <span class="qs-value">${additionalSummary.length > 0 ? additionalSummary.join(', ') : '-'}</span>
                        </li>
                        <li>
                            <span class="qs-label">Dangerous Goods</span>
                            <span class="qs-value">${detail.is_dg ? 'Yes' : 'No'}</span>
                        </li>
                        <li>
                            <span class="qs-label">Deadline</span>
                            <span class="qs-value">${detail.deadline ? this.formatDateTime(detail.deadline) : '-'}</span>
                        </li>
                        <li>
                            <span class="qs-label">Status</span>
                            <span class="qs-value"><span class="status-badge ${detail.status}">${this.getStatusLabel(detail.status)}</span></span>
                        </li>
                        <li>
                            <span class="qs-label">Bid Count</span>
                            <span class="qs-value">${detail.bid_count || 0} bids</span>
                        </li>
                    </ul>
            `;

            if (detail.remark) {
                html += `
                    <div class="quote-summary-section">
                        <div class="quote-summary-section-title">Special Remarks</div>
                        <p style="color: var(--text-sub); font-size: 0.9rem; line-height: 1.6;">${detail.remark}</p>
                    </div>
                `;
            }

            if (detail.my_bid) {
                html += `
                    <div class="quote-summary-section">
                        <div class="quote-summary-section-title">My Bid</div>
                        <div class="my-bid-card">
                            <ul class="quote-summary-list">
                                <li>
                                    <span class="qs-label">Total Amount</span>
                                    <span class="qs-value highlight">$ ${parseFloat(detail.my_bid.total_amount).toLocaleString()}</span>
                                </li>
                                <li>
                                    <span class="qs-label">Status</span>
                                    <span class="qs-value"><span class="status-badge ${detail.my_bid.status}">${this.getBidStatusLabel(detail.my_bid.status)}</span></span>
                                </li>
                            </ul>
                        </div>
                    </div>
                `;
            }

            html += `</div>`;

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
            'closing_soon': '마감예정',
            'expired': '마감',
            'awarded': '낙찰',
            'closed': '유찰',
            'cancelled': '유찰',
            'failed': '유찰'
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
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}.${month}.${day}`;
    },

    /**
     * Format port code with name
     * @param {string} code - Port code (e.g., KRPUS)
     * @param {string} name - Port name (e.g., BUSAN, KOREA)
     * @returns {string} Formatted port string (e.g., KRPUS(BUSAN, KOREA))
     */
    formatPort(code, name) {
        if (name) {
            return `${code}(${name})`;
        }
        return code || '-';
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
