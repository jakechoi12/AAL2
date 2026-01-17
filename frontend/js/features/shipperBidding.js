/**
 * Shipper Bidding Management Module
 * 화주를 위한 운송 요청 및 입찰 관리 기능
 */

const ShipperBidding = {
    // State
    shipper: null,  // 현재 로그인한 화주 (customer)
    currentPage: 1,
    limit: 20,
    filters: {
        status: '',
        shipping_type: '',
        search: ''
    },
    currentBidding: null,  // 현재 선택된 비딩
    selectedBid: null,     // 선정하려는 입찰

    /**
     * Initialize the module
     */
    init() {
        console.log('🚀 ShipperBidding module initialized');
        
        // Check for stored shipper session
        this.loadSession();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Update UI based on login state
        this.updateAuthUI();
        
        // Load data if logged in
        if (this.shipper) {
            this.loadStats();
            this.loadBiddingList();
        }
    },

    /**
     * Load stored session - Auth.js 연동
     */
    loadSession() {
        // Auth.js 세션 확인
        if (window.Auth && Auth.user && Auth.user.user_type === 'shipper') {
            this.shipper = Auth.user;
            console.log('✅ Session restored from Auth.js for shipper:', this.shipper.company);
            return;
        }
        
        // localStorage 직접 확인
        const authStored = localStorage.getItem('aal_user');
        if (authStored) {
            try {
                const authUser = JSON.parse(authStored);
                if (authUser.user_type === 'shipper') {
                    this.shipper = authUser;
                    console.log('✅ Session restored from aal_user for shipper:', this.shipper.company);
                    return;
                }
            } catch (e) {
                console.warn('Failed to parse aal_user');
            }
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Filter changes
        document.getElementById('filterStatus')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('filterShipping')?.addEventListener('change', () => this.applyFilters());
        
        // Search with debounce
        let searchTimeout;
        document.getElementById('filterSearch')?.addEventListener('input', (e) => {
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
                this.closeModal();
                this.closeConfirmModal();
            }
        });
    },

    /**
     * Update auth UI based on login state
     */
    updateAuthUI() {
        const loginRequiredState = document.getElementById('loginRequiredState');
        const emptyState = document.getElementById('emptyState');
        const biddingTableBody = document.getElementById('biddingTableBody');

        if (this.shipper) {
            // Logged in state
            if (loginRequiredState) loginRequiredState.style.display = 'none';
        } else {
            // Logged out state
            if (biddingTableBody) biddingTableBody.innerHTML = '';
            if (emptyState) emptyState.style.display = 'none';
            if (loginRequiredState) loginRequiredState.style.display = 'block';
        }
    },

    /**
     * Sync session with Auth.js
     */
    syncWithAuth() {
        if (window.Auth && Auth.user && Auth.user.user_type === 'shipper') {
            this.shipper = Auth.user;
        } else {
            this.shipper = null;
        }
        this.updateAuthUI();
        if (this.shipper) {
            this.loadStats();
            this.loadBiddingList();
        }
    },

    /**
     * Logout
     */
    logout() {
        if (confirm('로그아웃 하시겠습니까?')) {
            this.shipper = null;
            localStorage.removeItem('aal_user');
            if (window.Auth) {
                Auth.user = null;
            }
            this.updateAuthUI();
        }
    },

    /**
     * Load dashboard stats
     */
    async loadStats() {
        if (!this.shipper) return;
        
        try {
            const response = await fetch(
                `${QUOTE_API_BASE}/api/shipper/biddings/stats?customer_email=${encodeURIComponent(this.shipper.email)}`
            );
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
        this.filters.status = document.getElementById('filterStatus')?.value || '';
        this.filters.shipping_type = document.getElementById('filterShipping')?.value || '';
        this.filters.search = document.getElementById('filterSearch')?.value.trim() || '';
        this.currentPage = 1;
        this.loadBiddingList();
    },

    /**
     * Load bidding list
     */
    async loadBiddingList() {
        if (!this.shipper) return;
        
        const tbody = document.getElementById('biddingTableBody');
        const emptyState = document.getElementById('emptyState');
        const loadingState = document.getElementById('loadingState');
        const loginRequiredState = document.getElementById('loginRequiredState');

        // Show loading
        if (tbody) tbody.innerHTML = '';
        if (loadingState) loadingState.style.display = 'flex';
        if (emptyState) emptyState.style.display = 'none';
        if (loginRequiredState) loginRequiredState.style.display = 'none';

        try {
            const params = new URLSearchParams({
                customer_email: this.shipper.email,
                page: this.currentPage,
                limit: this.limit
            });

            if (this.filters.status) params.append('status', this.filters.status);
            if (this.filters.shipping_type) params.append('shipping_type', this.filters.shipping_type);
            if (this.filters.search) params.append('search', this.filters.search);

            const response = await fetch(`${QUOTE_API_BASE}/api/shipper/biddings?${params}`);
            const data = await response.json();

            if (loadingState) loadingState.style.display = 'none';

            if (data.data.length === 0) {
                if (emptyState) emptyState.style.display = 'block';
                this.renderPagination(0, 0);
                return;
            }

            // Render rows
            if (tbody) tbody.innerHTML = data.data.map(item => this.renderRow(item)).join('');
            
            // Render pagination
            this.renderPagination(data.total, Math.ceil(data.total / this.limit));

        } catch (error) {
            console.error('Failed to load bidding list:', error);
            if (loadingState) loadingState.style.display = 'none';
            if (emptyState) {
                emptyState.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>데이터를 불러오는데 실패했습니다</h3>
                    <p>서버 연결을 확인하고 다시 시도해주세요.</p>
                `;
                emptyState.style.display = 'block';
            }
        }
    },

    /**
     * Render a table row
     */
    renderRow(item) {
        const isExpired = item.deadline && this.isDeadlinePassed(item.deadline);
        
        // Determine effective status
        let effectiveStatus = item.status;
        if (item.status === 'open' && isExpired) {
            effectiveStatus = 'expired';
        }
        
        // Determine action button
        let actionBtn = '';
        if (effectiveStatus === 'open' && item.bid_count > 0) {
            actionBtn = `<button class="action-btn primary" onclick="ShipperBidding.openBidSelectionModal('${item.bidding_no}')">
                <i class="fas fa-user-check"></i> 선정
            </button>`;
        } else if (effectiveStatus === 'open' && item.bid_count === 0) {
            actionBtn = `<span class="status-text waiting">대기중</span>`;
        } else if (effectiveStatus === 'awarded') {
            actionBtn = `<span class="status-badge awarded"><i class="fas fa-trophy"></i></span>`;
        } else {
            actionBtn = `-`;
        }

        // Format minimum bid price (KRW)
        const minPriceFormatted = item.min_bid_price_krw 
            ? `₩${Math.round(item.min_bid_price_krw).toLocaleString('ko-KR')}`
            : '-';

        // Format volume
        const volumeFormatted = item.volume || '-';

        // Format deadline with D-day badge
        const deadlineBadge = this.formatDeadlineBadge(item.deadline);

        const rowClass = isExpired ? 'expired-row' : '';

        return `
            <tr class="${rowClass}">
                <td>
                    <span class="bidding-no ${isExpired ? 'expired-text' : ''}">
                        ${item.bidding_no}
                    </span>
                </td>
                <td><span class="port-code">${item.pol || '-'}</span></td>
                <td><span class="port-code">${item.pod || '-'}</span></td>
                <td>
                    <span class="type-badge ${item.shipping_type}">
                        <i class="fas fa-${this.getShippingIcon(item.shipping_type)}"></i>
                        ${item.shipping_type.toUpperCase()} / ${item.load_type}
                    </span>
                </td>
                <td><span class="volume-cell">${volumeFormatted}</span></td>
                <td>${this.formatDate(item.etd)}</td>
                <td>${deadlineBadge}</td>
                <td>
                    <span class="status-badge ${effectiveStatus}">${this.getStatusLabel(effectiveStatus)}</span>
                </td>
                <td>
                    <span class="bid-count ${item.bid_count > 0 ? 'has-bids' : ''}">${item.bid_count}</span>
                </td>
                <td>
                    <span class="min-price">${minPriceFormatted}</span>
                </td>
                <td>${actionBtn}</td>
            </tr>
        `;
    },

    /**
     * Format deadline with D-day badge
     */
    formatDeadlineBadge(deadline) {
        if (!deadline) return '-';
        
        const deadlineDate = new Date(deadline);
        const now = new Date();
        const diffTime = deadlineDate - now;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        const dateStr = this.formatDate(deadline);
        
        if (diffDays < 0) {
            return `<span class="deadline-badge expired">${dateStr} <span class="d-day">마감</span></span>`;
        } else if (diffDays === 0) {
            return `<span class="deadline-badge urgent">${dateStr} <span class="d-day">D-Day</span></span>`;
        } else if (diffDays <= 3) {
            return `<span class="deadline-badge warning">${dateStr} <span class="d-day">D-${diffDays}</span></span>`;
        } else {
            return `<span class="deadline-badge">${dateStr} <span class="d-day">D-${diffDays}</span></span>`;
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
     * Render pagination
     */
    renderPagination(total, totalPages) {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let html = `
            <button class="pagination-btn" onclick="ShipperBidding.goToPage(${this.currentPage - 1})" 
                    ${this.currentPage === 1 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i>
            </button>
        `;

        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        if (startPage > 1) {
            html += `<button class="pagination-btn" onclick="ShipperBidding.goToPage(1)">1</button>`;
            if (startPage > 2) html += `<span class="pagination-info">...</span>`;
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                        onclick="ShipperBidding.goToPage(${i})">${i}</button>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) html += `<span class="pagination-info">...</span>`;
            html += `<button class="pagination-btn" onclick="ShipperBidding.goToPage(${totalPages})">${totalPages}</button>`;
        }

        html += `
            <span class="pagination-info">총 ${total}건</span>
            <button class="pagination-btn" onclick="ShipperBidding.goToPage(${this.currentPage + 1})" 
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
     * Open bid selection modal
     */
    async openBidSelectionModal(biddingNo) {
        if (!this.shipper) {
            alert('로그인이 필요합니다.');
            return;
        }

        try {
            const response = await fetch(
                `${QUOTE_API_BASE}/api/shipper/bidding/${biddingNo}/bids?customer_email=${encodeURIComponent(this.shipper.email)}`
            );
            
            if (!response.ok) {
                throw new Error('Failed to load bids');
            }
            
            const data = await response.json();
            this.currentBidding = data;

            // Update modal header
            document.getElementById('modalBiddingNo').textContent = data.bidding_no;
            document.getElementById('modalRoute').textContent = `${data.pol} → ${data.pod}`;
            document.getElementById('modalEtd').textContent = `ETD: ${this.formatDate(data.etd)}`;

            // Render bid list
            const tbody = document.getElementById('bidListBody');
            const noBidsState = document.getElementById('noBidsState');

            if (data.bids.length === 0) {
                tbody.innerHTML = '';
                noBidsState.style.display = 'block';
            } else {
                noBidsState.style.display = 'none';
                tbody.innerHTML = data.bids.map(bid => this.renderBidRow(bid)).join('');
            }

            // Show modal
            document.getElementById('bidSelectionModal').classList.add('active');

        } catch (error) {
            console.error('Failed to load bids:', error);
            alert('입찰 목록을 불러오는데 실패했습니다.');
        }
    },

    /**
     * Render a bid row with detail accordion
     */
    renderBidRow(bid) {
        // Render rating stars
        const ratingStars = this.renderRatingStars(bid.rating);
        
        // Format KRW price
        const priceFormatted = `₩${Math.round(bid.total_amount_krw).toLocaleString('ko-KR')}`;
        
        // Format schedule
        const etdStr = bid.etd ? this.formatDate(bid.etd) : '-';
        const etaStr = bid.eta ? this.formatDate(bid.eta) : '-';
        const scheduleStr = `${etdStr}<br><span class="text-muted">→ ${etaStr}</span>`;
        
        // Rank badge class
        const rankClass = bid.rank === 1 ? 'rank-1' : (bid.rank === 2 ? 'rank-2' : (bid.rank === 3 ? 'rank-3' : ''));

        // Format validity date
        const validityStr = bid.validity_date ? this.formatDate(bid.validity_date) : '-';

        // Column count for detail row
        const colSpan = 9;

        return `
            <tr data-bid-id="${bid.id}" class="bid-main-row">
                <td class="col-rank">
                    <span class="rank-badge ${rankClass}">${bid.rank}</span>
                </td>
                <td class="col-company">
                    <span class="company-masked">${bid.company_masked}</span>
                </td>
                <td class="col-rating">
                    <div class="rating-display">
                        ${ratingStars}
                        <span class="rating-value">${bid.rating.toFixed(1)}</span>
                        <span class="rating-count">(${bid.rating_count})</span>
                    </div>
                </td>
                <td class="col-price">
                    <span class="bid-price">${priceFormatted}</span>
                </td>
                <td class="col-schedule">
                    ${scheduleStr}
                </td>
                <td class="col-transit">
                    ${bid.transit_time || '-'}
                </td>
                <td class="col-carrier">
                    ${bid.carrier || '-'}
                </td>
                <td class="col-action">
                    <button class="action-btn award-btn" onclick="ShipperBidding.selectBid(${bid.id}, '${bid.company_masked}', ${bid.total_amount_krw})">
                        <i class="fas fa-check"></i> 선정
                    </button>
                </td>
                <td class="col-detail">
                    <button class="btn-toggle-detail" onclick="ShipperBidding.toggleBidDetail(${bid.id})" title="상세보기">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </td>
            </tr>
            <tr class="bid-detail-row" id="bidDetail_${bid.id}" style="display: none;">
                <td colspan="${colSpan}">
                    <div class="bid-detail-content">
                        <div class="detail-section">
                            <h5 class="detail-title"><i class="fas fa-file-invoice-dollar"></i> 견적 상세</h5>
                            <div class="detail-breakdown">
                                <div class="breakdown-item">
                                    <span class="breakdown-label">운임 (Freight)</span>
                                    <span class="breakdown-value">${bid.freight_charge ? `₩${Math.round(bid.freight_charge).toLocaleString('ko-KR')}` : '-'}</span>
                                </div>
                                <div class="breakdown-item">
                                    <span class="breakdown-label">로컬비 (Local)</span>
                                    <span class="breakdown-value">${bid.local_charge ? `₩${Math.round(bid.local_charge).toLocaleString('ko-KR')}` : '-'}</span>
                                </div>
                                <div class="breakdown-item">
                                    <span class="breakdown-label">기타 (Other)</span>
                                    <span class="breakdown-value">${bid.other_charge ? `₩${Math.round(bid.other_charge).toLocaleString('ko-KR')}` : '-'}</span>
                                </div>
                                <div class="breakdown-item total">
                                    <span class="breakdown-label">합계</span>
                                    <span class="breakdown-value">${priceFormatted}</span>
                                </div>
                            </div>
                        </div>
                        <div class="detail-section">
                            <h5 class="detail-title"><i class="fas fa-info-circle"></i> 추가 정보</h5>
                            <div class="detail-info-grid">
                                <div class="info-item">
                                    <span class="info-label">견적 유효기간</span>
                                    <span class="info-value">${validityStr}</span>
                                </div>
                                <div class="info-item remark">
                                    <span class="info-label">비고</span>
                                    <span class="info-value">${bid.remark || '-'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    },

    /**
     * Toggle bid detail accordion
     */
    toggleBidDetail(bidId) {
        const detailRow = document.getElementById(`bidDetail_${bidId}`);
        const mainRow = document.querySelector(`tr[data-bid-id="${bidId}"]`);
        const toggleBtn = mainRow?.querySelector('.btn-toggle-detail i');
        
        if (!detailRow) return;
        
        const isVisible = detailRow.style.display !== 'none';
        
        if (isVisible) {
            detailRow.style.display = 'none';
            mainRow?.classList.remove('expanded');
            if (toggleBtn) toggleBtn.className = 'fas fa-chevron-down';
        } else {
            detailRow.style.display = 'table-row';
            mainRow?.classList.add('expanded');
            if (toggleBtn) toggleBtn.className = 'fas fa-chevron-up';
        }
    },

    /**
     * Render rating stars (0.5 단위)
     */
    renderRatingStars(rating) {
        let html = '';
        const fullStars = Math.floor(rating);
        const hasHalfStar = (rating % 1) >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

        // Full stars
        for (let i = 0; i < fullStars; i++) {
            html += '<i class="fas fa-star"></i>';
        }
        
        // Half star
        if (hasHalfStar) {
            html += '<i class="fas fa-star-half-alt"></i>';
        }
        
        // Empty stars
        for (let i = 0; i < emptyStars; i++) {
            html += '<i class="far fa-star"></i>';
        }

        return `<div class="stars">${html}</div>`;
    },

    /**
     * Close bid selection modal
     */
    closeModal() {
        document.getElementById('bidSelectionModal').classList.remove('active');
        this.currentBidding = null;
    },

    /**
     * Select a bid for awarding
     */
    selectBid(bidId, companyMasked, priceKrw) {
        this.selectedBid = {
            id: bidId,
            company: companyMasked,
            price: priceKrw
        };

        // Update confirm modal
        const confirmDetails = document.getElementById('confirmDetails');
        confirmDetails.innerHTML = `
            <div class="confirm-detail-item">
                <span class="detail-label">업체</span>
                <span class="detail-value">${companyMasked}</span>
            </div>
            <div class="confirm-detail-item">
                <span class="detail-label">입찰가</span>
                <span class="detail-value highlight">₩${Math.round(priceKrw).toLocaleString('ko-KR')}</span>
            </div>
        `;

        // Show confirm modal
        document.getElementById('confirmModal').classList.add('active');
    },

    /**
     * Close confirm modal
     */
    closeConfirmModal() {
        document.getElementById('confirmModal').classList.remove('active');
        this.selectedBid = null;
    },

    /**
     * Confirm award
     */
    async confirmAward() {
        if (!this.selectedBid || !this.currentBidding) {
            alert('선정할 입찰을 선택해주세요.');
            return;
        }

        const confirmBtn = document.getElementById('confirmAwardBtn');
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 처리중...';

        try {
            const response = await fetch(
                `${QUOTE_API_BASE}/api/shipper/bidding/${this.currentBidding.bidding_no}/award/${this.selectedBid.id}?customer_email=${encodeURIComponent(this.shipper.email)}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Failed to award bid');
            }

            // Success
            alert('운송사가 선정되었습니다!\n선정된 운송사에 알림이 발송되었습니다.');
            
            this.closeConfirmModal();
            this.closeModal();
            this.refresh();

        } catch (error) {
            console.error('Failed to award bid:', error);
            alert('운송사 선정에 실패했습니다: ' + error.message);
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-check"></i> 선정하기';
        }
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
            'open': '입찰중',
            'closing_soon': '마감예정',
            'expired': '마감',
            'awarded': '선정완료',
            'closed': '유찰',
            'cancelled': '취소',
            'failed': '유찰'
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
    }
};

// Export for global access
window.ShipperBidding = ShipperBidding;
