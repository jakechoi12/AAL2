/**
 * Shipper Bidding Management Module
 * 화주를 위한 운송 요청 및 입찰 관리 기능
 * Dashboard 2-Column Layout Version
 */

const ShipperBidding = {
    // State
    shipper: null,  // 현재 로그인한 화주 (customer)
    currentPage: 1,
    limit: 15,
    filters: {
        status: '',
        shipping_type: '',
        search: ''
    },
    biddingList: [],          // 비딩 목록 데이터
    selectedBiddingNo: null,  // 현재 선택된 비딩 번호
    currentBidding: null,     // 현재 선택된 비딩 상세 데이터
    selectedBid: null,        // 선정하려는 입찰
    currentForwarderId: null, // 프로필 모달용 포워더 ID

    /**
     * Initialize the module
     */
    init() {
        console.log('🚀 ShipperBidding module initialized (Dashboard Mode)');
        
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
                this.closeForwarderProfile();
            }
        });
    },

    /**
     * Update auth UI based on login state
     */
    updateAuthUI() {
        const loginRequiredState = document.getElementById('loginRequiredState');
        const dashboardLayout = document.querySelector('.dashboard-layout');
        const emptyState = document.getElementById('emptyState');
        const cardsContainer = document.getElementById('biddingCardsContainer');

        if (this.shipper) {
            // Logged in state
            if (loginRequiredState) loginRequiredState.style.display = 'none';
            if (dashboardLayout) dashboardLayout.style.display = 'grid';
        } else {
            // Logged out state
            if (cardsContainer) cardsContainer.innerHTML = '';
            if (emptyState) emptyState.style.display = 'none';
            if (dashboardLayout) dashboardLayout.style.display = 'none';
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
        this.selectedBiddingNo = null;
        this.loadBiddingList();
    },

    /**
     * Load bidding list and render as cards
     */
    async loadBiddingList() {
        if (!this.shipper) return;
        
        const cardsContainer = document.getElementById('biddingCardsContainer');
        const emptyState = document.getElementById('emptyState');
        const loadingState = document.getElementById('loadingState');
        const biddingCount = document.getElementById('biddingCount');

        // Show loading
        if (cardsContainer) cardsContainer.innerHTML = '';
        if (loadingState) loadingState.style.display = 'flex';
        if (emptyState) emptyState.style.display = 'none';

        // Reset detail panel
        this.showDetailPlaceholder();

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

            this.biddingList = data.data;

            if (data.data.length === 0) {
                if (emptyState) emptyState.style.display = 'block';
                if (biddingCount) biddingCount.textContent = '0건';
                this.renderPagination(0, 0);
                return;
            }

            // Update count
            if (biddingCount) biddingCount.textContent = `${data.total}건`;

            // Render cards
            this.renderBiddingCards(data.data);
            
            // Render pagination
            this.renderPagination(data.total, Math.ceil(data.total / this.limit));

            // Auto-select first card if none selected
            if (!this.selectedBiddingNo && data.data.length > 0) {
                this.selectBidding(data.data[0].bidding_no);
            }

        } catch (error) {
            console.error('Failed to load bidding list:', error);
            if (loadingState) loadingState.style.display = 'none';
            if (emptyState) {
                emptyState.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>데이터를 불러오는데 실패했습니다</p>
                `;
                emptyState.style.display = 'block';
            }
        }
    },

    /**
     * Render bidding cards in left panel
     */
    renderBiddingCards(biddings) {
        const container = document.getElementById('biddingCardsContainer');
        if (!container) return;
        
        container.innerHTML = biddings.map(item => {
            const isExpired = item.deadline && this.isDeadlinePassed(item.deadline);
        let effectiveStatus = item.status;
        if (item.status === 'open' && isExpired) {
            effectiveStatus = 'expired';
        }
        
            const isSelected = this.selectedBiddingNo === item.bidding_no;

            return `
                <div class="bidding-card ${isSelected ? 'selected' : ''}" 
                     onclick="ShipperBidding.selectBidding('${item.bidding_no}')"
                     data-bidding-no="${item.bidding_no}">
                    <div class="card-header">
                        <span class="card-bidding-no">${item.bidding_no}</span>
                        <span class="card-status ${effectiveStatus}">${this.getStatusLabel(effectiveStatus)}</span>
                    </div>
                    <div class="card-route">
                        <span class="port">${item.pol || '-'}</span>
                        <span class="arrow"><i class="fas fa-arrow-right"></i></span>
                        <span class="port">${item.pod || '-'}</span>
                    </div>
                    <div class="card-footer">
                        <span class="card-type">
                            <i class="fas fa-${this.getShippingIcon(item.shipping_type)}"></i>
                            ${item.shipping_type?.toUpperCase() || '-'}
                        </span>
                        <span class="card-bids ${item.bid_count > 0 ? 'has-bids' : ''}">
                            <i class="fas fa-users"></i> ${item.bid_count}건
                        </span>
                    </div>
                </div>
            `;
        }).join('');
    },

    /**
     * Select a bidding and load detail in right panel
     */
    async selectBidding(biddingNo) {
        // Update selected state
        this.selectedBiddingNo = biddingNo;

        // Update card selection UI
        document.querySelectorAll('.bidding-card').forEach(card => {
            card.classList.toggle('selected', card.dataset.biddingNo === biddingNo);
        });

        // Find bidding data from list
        const biddingData = this.biddingList.find(b => b.bidding_no === biddingNo);
        if (!biddingData) return;

        // Load bids for this bidding
        await this.loadBiddingDetail(biddingNo, biddingData);
    },

    /**
     * Load bidding detail and bids for right panel
     */
    async loadBiddingDetail(biddingNo, biddingData) {
        try {
            const response = await fetch(
                `${QUOTE_API_BASE}/api/shipper/bidding/${biddingNo}/bids?customer_email=${encodeURIComponent(this.shipper.email)}`
            );
            
            if (!response.ok) {
                throw new Error('Failed to load bids');
            }
            
            const data = await response.json();
            this.currentBidding = data;

            // Show detail content
            this.showDetailContent();

            // Update header
            document.getElementById('detailBiddingNo').textContent = data.bidding_no;
            document.getElementById('detailRoute').textContent = `${data.pol} → ${data.pod}`;
            
            // Update type badge
            const typeBadge = document.getElementById('detailTypeBadge');
            typeBadge.className = `detail-type-badge ${data.shipping_type}`;
            typeBadge.innerHTML = `<i class="fas fa-${this.getShippingIcon(data.shipping_type)}"></i> ${data.shipping_type?.toUpperCase()}`;

            // Update deadline
            const deadlineEl = document.getElementById('detailDeadline');
            if (data.deadline) {
                const dDays = this.getDaysUntilDeadline(data.deadline);
                deadlineEl.textContent = dDays < 0 ? '마감' : (dDays === 0 ? 'D-Day' : `D-${dDays}`);
        } else {
                deadlineEl.textContent = '-';
            }

            // Update summary cards
            this.updateSummaryCards(data);

            // Render bids table
            this.renderBidsTable(data.bids);

        } catch (error) {
            console.error('Failed to load bidding detail:', error);
        }
    },

    /**
     * Show detail placeholder (nothing selected)
     */
    showDetailPlaceholder() {
        const placeholder = document.getElementById('detailPlaceholder');
        const content = document.getElementById('detailContent');
        if (placeholder) placeholder.style.display = 'flex';
        if (content) content.style.display = 'none';
    },

    /**
     * Show detail content
     */
    showDetailContent() {
        const placeholder = document.getElementById('detailPlaceholder');
        const content = document.getElementById('detailContent');
        if (placeholder) placeholder.style.display = 'none';
        if (content) content.style.display = 'flex';
    },

    /**
     * Update summary cards in detail panel
     */
    updateSummaryCards(data) {
        // Participants count
        document.getElementById('summaryBidCount').textContent = data.bid_count || 0;

        // Calculate lowest and average price
        if (data.bids && data.bids.length > 0) {
            const prices = data.bids.map(b => b.total_amount_krw).filter(p => p > 0);
            if (prices.length > 0) {
                const lowestPrice = Math.min(...prices);
                const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
                
                document.getElementById('summaryLowestPrice').textContent = 
                    `₩${Math.round(lowestPrice).toLocaleString('ko-KR')}`;
                document.getElementById('summaryAvgPrice').textContent = 
                    `₩${Math.round(avgPrice).toLocaleString('ko-KR')}`;
            } else {
                document.getElementById('summaryLowestPrice').textContent = '-';
                document.getElementById('summaryAvgPrice').textContent = '-';
            }
        } else {
            document.getElementById('summaryLowestPrice').textContent = '-';
            document.getElementById('summaryAvgPrice').textContent = '-';
        }

        // Status
        document.getElementById('summaryStatus').textContent = this.getStatusLabel(data.bidding_status);
    },

    /**
     * Render bids table in detail panel
     */
    renderBidsTable(bids) {
        const tbody = document.getElementById('bidsTableBody');
        const noBidsMsg = document.getElementById('noBidsMessage');

        if (!bids || bids.length === 0) {
            if (tbody) tbody.innerHTML = '';
            if (noBidsMsg) noBidsMsg.style.display = 'block';
            return;
        }

        if (noBidsMsg) noBidsMsg.style.display = 'none';

        tbody.innerHTML = bids.map(bid => {
            const ratingStars = this.renderRatingStars(bid.rating);
            const priceFormatted = `₩${Math.round(bid.total_amount_krw).toLocaleString('ko-KR')}`;
            const rankClass = bid.rank === 1 ? 'rank-1' : (bid.rank === 2 ? 'rank-2' : (bid.rank === 3 ? 'rank-3' : ''));
            const etdStr = bid.etd ? this.formatDateShort(bid.etd) : '-';
            const etaStr = bid.eta ? this.formatDateShort(bid.eta) : '-';

            // Check if bidding is still open
            const canSelect = this.currentBidding?.bidding_status === 'open';

        return `
                <tr data-bid-id="${bid.id}">
                    <td class="col-rank">
                        <span class="rank-badge ${rankClass}">${bid.rank}</span>
                </td>
                    <td class="col-company">
                        <span class="company-link" onclick="ShipperBidding.openForwarderProfile(${bid.id}, '${bid.company_masked}')">
                            ${bid.company_masked}
                    </span>
                </td>
                    <td class="col-rating">
                        <div class="rating-display">
                            ${ratingStars}
                            <span class="rating-value">${bid.rating.toFixed(1)}</span>
                        </div>
                </td>
                    <td class="col-etd">${etdStr}</td>
                    <td class="col-eta">${etaStr}</td>
                    <td class="col-price">
                        <span class="bid-price">${priceFormatted}</span>
                </td>
                    <td class="col-action">
                        ${canSelect ? `
                            <button class="action-btn award-btn" onclick="ShipperBidding.selectBid(${bid.id}, '${bid.company_masked}', ${bid.total_amount_krw})">
                                <i class="fas fa-check"></i>
                            </button>
                        ` : '-'}
                </td>
            </tr>
        `;
        }).join('');
    },

    /**
     * Get days until deadline
     */
    getDaysUntilDeadline(deadline) {
        if (!deadline) return null;
        const deadlineDate = new Date(deadline);
        const now = new Date();
        const diffTime = deadlineDate - now;
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
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
            pagination.innerHTML = `<span class="pagination-info">총 ${total}건</span>`;
            return;
        }

        let html = `
            <button class="pagination-btn" onclick="ShipperBidding.goToPage(${this.currentPage - 1})" 
                    ${this.currentPage === 1 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i>
            </button>
        `;

        // Show current page / total pages
        html += `<span class="pagination-info">${this.currentPage} / ${totalPages}</span>`;

            html += `
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
        this.selectedBiddingNo = null;
        this.loadBiddingList();
    },

    /**
     * Refresh data
     */
    refresh() {
        this.loadStats();
        this.loadBiddingList();
    },

    // ==========================================
    // FORWARDER PROFILE MODAL
    // ==========================================

    /**
     * Open forwarder profile modal
     */
    async openForwarderProfile(bidId, companyMasked) {
        // Find forwarder_id from current bidding bids
        const bid = this.currentBidding?.bids?.find(b => b.id === bidId);
        if (!bid) {
            console.warn('Bid not found for profile');
            return;
        }

        // Store for later use (selection)
        this.currentForwarderId = bid.forwarder_id;
        this.currentProfileBid = bid;

        // Show modal with loading state
        const modal = document.getElementById('forwarderProfileModal');
        modal.classList.add('active');

        // Update basic info first
        document.getElementById('profileCompany').textContent = companyMasked;
        document.getElementById('profileAvatar').textContent = companyMasked.charAt(0);
        document.getElementById('profileStars').innerHTML = this.renderRatingStars(bid.rating);
        document.getElementById('profileRatingValue').textContent = bid.rating.toFixed(1);
        document.getElementById('profileRatingCount').textContent = `(${bid.rating_count})`;

        // Try to fetch detailed profile using forwarder_id
        if (bid.forwarder_id) {
            try {
                const response = await fetch(`${QUOTE_API_BASE}/api/forwarders/${bid.forwarder_id}/profile`);
                if (response.ok) {
                    const profileData = await response.json();
                    this.renderForwarderProfile(profileData);
                    return;
                }
            } catch (error) {
                console.error('Failed to load forwarder profile:', error);
            }
        }

        // Fallback: display what we have from the bid data
        this.renderProfileWithBidData(bid);
    },

    /**
     * Render forwarder profile with full API data
     */
    renderForwarderProfile(profile) {
        // Stats row
        document.getElementById('profileTotalBids').textContent = profile.total_bids || 0;
        document.getElementById('profileTotalAwarded').textContent = profile.total_awarded || 0;
        document.getElementById('profileAwardRate').textContent = `${profile.award_rate || 0}%`;
        
        if (profile.member_since) {
            const date = new Date(profile.member_since);
            document.getElementById('profileMemberSince').textContent = 
                date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short' });
        } else {
            document.getElementById('profileMemberSince').textContent = '-';
        }

        // Score breakdown
        const scoreMapping = [
            { type: 'price', value: profile.avg_price_score },
            { type: 'service', value: profile.avg_service_score },
            { type: 'punctuality', value: profile.avg_punctuality_score },
            { type: 'communication', value: profile.avg_communication_score }
        ];
        
        scoreMapping.forEach(({ type, value }) => {
            const bar = document.getElementById(`${type}ScoreBar`);
            const valueEl = document.getElementById(`${type}ScoreValue`);
            if (value) {
                const percentage = (value / 5) * 100;
                if (bar) bar.style.width = `${percentage}%`;
                if (valueEl) valueEl.textContent = value.toFixed(1);
            } else {
                if (bar) bar.style.width = '0%';
                if (valueEl) valueEl.textContent = '-';
            }
        });

        // Top routes
        const routesList = document.getElementById('topRoutesList');
        if (profile.top_routes && profile.top_routes.length > 0) {
            routesList.innerHTML = profile.top_routes.map(route => `
                <div class="route-item">
                    <div class="route-info">
                        <span class="pol">${route.pol}</span>
                        <span class="arrow"><i class="fas fa-arrow-right"></i></span>
                        <span class="pod">${route.pod}</span>
                    </div>
                    <div class="route-stats">
                        <span>${route.count}건</span>
                        <span class="awarded">낙찰 ${route.awarded_count}</span>
                    </div>
                </div>
            `).join('');
        } else {
            routesList.innerHTML = '<div class="empty-data">데이터 없음</div>';
        }

        // Shipping mode stats
        const modeChart = document.getElementById('shippingModeChart');
        if (profile.shipping_mode_stats && profile.shipping_mode_stats.length > 0) {
            modeChart.innerHTML = profile.shipping_mode_stats.map(mode => `
                <div class="mode-item ${mode.shipping_type}">
                    <div class="mode-icon">
                        <i class="fas fa-${this.getShippingIcon(mode.shipping_type)}"></i>
                    </div>
                    <div class="mode-info">
                        <span class="mode-name">${mode.shipping_type.toUpperCase()}</span>
                        <span class="mode-stats">${mode.count}건 (${mode.percentage}%)</span>
                    </div>
                </div>
            `).join('');
        } else {
            modeChart.innerHTML = '<div class="empty-data">데이터 없음</div>';
        }

        // Reviews
        const reviewsList = document.getElementById('reviewsList');
        if (profile.reviews && profile.reviews.length > 0) {
            reviewsList.innerHTML = profile.reviews.map(review => `
                <div class="review-item">
                    <div class="review-header">
                        <span class="review-customer">${review.customer_company_masked}</span>
                        <div class="review-score">
                            ${this.renderRatingStars(review.score)}
                            <span>${review.score.toFixed(1)}</span>
                        </div>
                    </div>
                    <div class="review-meta">
                        <span>${review.bidding_no}</span>
                        <span>${review.pol} → ${review.pod}</span>
                        <span>${this.formatDate(review.created_at)}</span>
                    </div>
                    ${review.comment ? `<div class="review-comment">${review.comment}</div>` : ''}
                </div>
            `).join('');
        } else {
            reviewsList.innerHTML = '<div class="empty-data">리뷰가 없습니다</div>';
        }

        // Enable/disable select button
        const selectBtn = document.getElementById('profileSelectBtn');
        if (this.currentBidding?.bidding_status === 'open') {
            selectBtn.disabled = false;
            selectBtn.style.display = 'inline-flex';
        } else {
            selectBtn.style.display = 'none';
        }
    },

    /**
     * Render profile using bid data (fallback when full API not available)
     */
    renderProfileWithBidData(bid) {
        // Stats row - show available data
        document.getElementById('profileTotalBids').textContent = '-';
        document.getElementById('profileTotalAwarded').textContent = '-';
        document.getElementById('profileAwardRate').textContent = '-';
        document.getElementById('profileMemberSince').textContent = '-';

        // Score breakdown - placeholder
        const scoreItems = ['price', 'service', 'punctuality', 'communication'];
        scoreItems.forEach(type => {
            const bar = document.getElementById(`${type}ScoreBar`);
            const value = document.getElementById(`${type}ScoreValue`);
            if (bar) bar.style.width = '0%';
            if (value) value.textContent = '-';
        });

        // Top routes - placeholder
        document.getElementById('topRoutesList').innerHTML = `
            <div class="route-item">
                <div class="route-info">
                    <span class="pol">${this.currentBidding?.pol || '-'}</span>
                    <span class="arrow"><i class="fas fa-arrow-right"></i></span>
                    <span class="pod">${this.currentBidding?.pod || '-'}</span>
                </div>
                <div class="route-stats">
                    <span>현재 입찰 중</span>
                </div>
            </div>
        `;

        // Shipping mode - from current bidding
        const shippingType = this.currentBidding?.shipping_type || 'ocean';
        document.getElementById('shippingModeChart').innerHTML = `
            <div class="mode-item ${shippingType}">
                <div class="mode-icon">
                    <i class="fas fa-${this.getShippingIcon(shippingType)}"></i>
                </div>
                <div class="mode-info">
                    <span class="mode-name">${shippingType.toUpperCase()}</span>
                    <span class="mode-stats">현재 입찰</span>
                </div>
            </div>
        `;

        // Reviews - placeholder
        document.getElementById('reviewsList').innerHTML = `
            <div class="empty-data">리뷰 정보를 불러올 수 없습니다</div>
        `;

        // Enable/disable select button based on bidding status
        const selectBtn = document.getElementById('profileSelectBtn');
        if (this.currentBidding?.bidding_status === 'open') {
            selectBtn.disabled = false;
            selectBtn.style.display = 'inline-flex';
        } else {
            selectBtn.style.display = 'none';
        }
    },

    /**
     * Close forwarder profile modal
     */
    closeForwarderProfile() {
        document.getElementById('forwarderProfileModal').classList.remove('active');
        this.currentForwarderId = null;
        this.currentProfileBid = null;
    },

    /**
     * Select forwarder from profile modal
     */
    selectFromProfile() {
        if (!this.currentProfileBid) return;
        
        const bid = this.currentProfileBid;
        this.closeForwarderProfile();
        this.selectBid(bid.id, bid.company_masked, bid.total_amount_krw);
    },

    // ==========================================
    // BID SELECTION MODAL (Legacy support)
    // ==========================================

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
     * Render a bid row with detail accordion (legacy modal)
     */
    renderBidRow(bid) {
        const ratingStars = this.renderRatingStars(bid.rating);
        const priceFormatted = `₩${Math.round(bid.total_amount_krw).toLocaleString('ko-KR')}`;
        const etdStr = bid.etd ? this.formatDate(bid.etd) : '-';
        const etaStr = bid.eta ? this.formatDate(bid.eta) : '-';
        const scheduleStr = `${etdStr}<br><span class="text-muted">→ ${etaStr}</span>`;
        const rankClass = bid.rank === 1 ? 'rank-1' : (bid.rank === 2 ? 'rank-2' : (bid.rank === 3 ? 'rank-3' : ''));
        const validityStr = bid.validity_date ? this.formatDate(bid.validity_date) : '-';
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

        for (let i = 0; i < fullStars; i++) {
            html += '<i class="fas fa-star"></i>';
        }
        
        if (hasHalfStar) {
            html += '<i class="fas fa-star-half-alt"></i>';
        }
        
        for (let i = 0; i < emptyStars; i++) {
            html += '<i class="far fa-star"></i>';
        }

        return `<div class="stars">${html}</div>`;
    },

    /**
     * Close bid selection modal
     */
    closeModal() {
        document.getElementById('bidSelectionModal')?.classList.remove('active');
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

    formatDateShort(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ko-KR', {
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
