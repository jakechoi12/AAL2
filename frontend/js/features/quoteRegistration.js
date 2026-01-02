/**
 * Quote Registration Module
 * 포워더 견적 등록/작성 페이지 기능
 * Reference Image 기반 전면 재설계
 */

const QUOTE_API_BASE = 'http://localhost:8001';

// 표준 Freight Codes
const FREIGHT_CODES = [
    { code: 'OFR', category: 'Ocean Freight', defaultCurrency: 'USD' },
    { code: 'AFR', category: 'Air Freight', defaultCurrency: 'USD' },
    { code: 'FRT', category: 'Local Charge', defaultCurrency: 'USD' },
    { code: 'BAF', category: 'Inland Charge', defaultCurrency: 'USD' },
    { code: 'DOC', category: 'Ocean Freight', defaultCurrency: 'KRW' },
    { code: 'THC', category: 'Terminal Handling Charge', defaultCurrency: 'USD' },
    { code: 'WFG', category: 'Wharfage', defaultCurrency: 'USD' },
    { code: 'CFS', category: 'CFS Charge', defaultCurrency: 'USD' },
    { code: 'SEAL', category: 'Seal Fee', defaultCurrency: 'USD' },
    { code: 'AMS', category: 'AMS Fee', defaultCurrency: 'USD' },
    { code: 'ENS', category: 'ENS Fee', defaultCurrency: 'USD' },
    { code: 'LSS', category: 'Low Sulphur Surcharge', defaultCurrency: 'USD' },
    { code: 'EBS', category: 'Emergency Bunker Surcharge', defaultCurrency: 'USD' },
    { code: 'CIC', category: 'Container Imbalance Charge', defaultCurrency: 'USD' },
    { code: 'PSS', category: 'Peak Season Surcharge', defaultCurrency: 'USD' },
    { code: 'CAF', category: 'Currency Adjustment Factor', defaultCurrency: 'USD' },
    { code: 'INLAND', category: 'Inland Transport', defaultCurrency: 'USD' },
    { code: 'CUSTOMS', category: 'Customs Clearance', defaultCurrency: 'KRW' },
    { code: 'TRUCKING', category: 'Trucking', defaultCurrency: 'KRW' },
    { code: 'HANDLING', category: 'Handling Fee', defaultCurrency: 'USD' },
    { code: 'OTHER', category: 'Other Charges', defaultCurrency: 'USD' }
];

const UNIT_OPTIONS = ['20DC', '40DC', '40HC', '45HC', 'CBM', 'KG', 'BL', 'CNTR', 'SHPT', 'RT'];
const CURRENCY_OPTIONS = ['USD', 'KRW', 'EUR', 'JPY', 'CNY'];
const TAX_OPTIONS = ['영세', '과세'];

// Exchange Rates (실제로는 API에서 가져와야 함)
const EXCHANGE_RATES = {
    'USD': 1366.50,
    'EUR': 1480.20,
    'JPY': 9.12,
    'CNY': 187.50,
    'KRW': 1
};

const QuoteReg = {
    // State
    forwarder: null,
    currentBidding: null,
    quoteList: [],
    currentQuoteIndex: 0,
    rateLines: [],
    exchangeRate: 1366.50,
    displayCurrency: 'KRW',
    isAdditionalExpanded: false,

    /**
     * Initialize the module
     */
    init() {
        console.log('🚀 QuoteReg module initialized');
        
        // Load forwarder session
        this.loadSession();
        
        // Get bidding info from URL
        this.loadBiddingFromURL();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize default rate lines
        this.initializeRateLines();
        
        // Render initial state
        this.renderRatesTable();
        this.calculateTotals();
        
        // Update UI
        this.updateUI();
    },

    /**
     * Load stored forwarder session
     */
    loadSession() {
        const stored = localStorage.getItem('forwarder');
        if (stored) {
            try {
                this.forwarder = JSON.parse(stored);
                document.getElementById('userCompany').textContent = this.forwarder.company;
                document.getElementById('userEmail').textContent = this.forwarder.email;
            } catch (e) {
                console.error('Session load error:', e);
            }
        }
    },

    /**
     * Load bidding info from URL parameters
     */
    async loadBiddingFromURL() {
        const params = new URLSearchParams(window.location.search);
        const biddingNo = params.get('bidding_no');
        
        if (biddingNo) {
            await this.loadBiddingDetail(biddingNo);
        }
    },

    /**
     * Load bidding detail from API
     */
    async loadBiddingDetail(biddingNo) {
        try {
            const forwarderId = this.forwarder ? this.forwarder.id : null;
            const url = forwarderId 
                ? `${QUOTE_API_BASE}/api/bidding/${biddingNo}/detail?forwarder_id=${forwarderId}`
                : `${QUOTE_API_BASE}/api/bidding/${biddingNo}/detail`;
            
            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) throw new Error(data.detail);

            this.currentBidding = data;
            this.populateBiddingInfo(data);
            
            // If has existing bid, load it
            if (data.my_bid) {
                this.loadExistingBid(data.my_bid);
            }

        } catch (error) {
            console.error('Failed to load bidding detail:', error);
            this.showToast('입찰 정보를 불러오는데 실패했습니다.', 'error');
        }
    },

    /**
     * Populate bidding information to UI
     */
    populateBiddingInfo(data) {
        // Quote Number
        document.getElementById('quoteNo').textContent = data.bidding_no || 'NHPS000000';
        
        // Customer Info
        document.getElementById('customerName').value = data.customer_company || '';
        
        // Request Details Table
        document.getElementById('detailIncoterms').textContent = data.incoterms || '-';
        document.getElementById('detailShippingMode').textContent = data.shipping_type ? data.shipping_type.charAt(0).toUpperCase() + data.shipping_type.slice(1) : '-';
        document.getElementById('detailTradeMode').textContent = data.trade_mode ? data.trade_mode.charAt(0).toUpperCase() + data.trade_mode.slice(1) : '-';
        document.getElementById('detailLoadType').textContent = data.load_type || '-';
        
        // DG Checkbox
        const dgCheckbox = document.getElementById('detailDG').querySelector('input');
        if (dgCheckbox) {
            dgCheckbox.checked = data.is_dg || false;
        }
        
        document.getElementById('detailPOL').textContent = data.pol || '-';
        document.getElementById('detailPOD').textContent = data.pod || '-';
        document.getElementById('detailContainer').textContent = data.container_type ? `${data.container_type}(${data.container_qty || 1})` : '-';
        document.getElementById('detailTotalQty').textContent = data.total_qty || '-';
        document.getElementById('detailTotalWeight').textContent = data.total_weight ? this.formatNumber(data.total_weight) : '-';
        document.getElementById('detailTotalMeasure').textContent = data.total_cbm ? this.formatNumber(data.total_cbm) : '-';
        document.getElementById('detailInvoiceValue').textContent = data.invoice_value ? this.formatNumber(data.invoice_value) : '-';

        // Additional Information
        this.updateAdditionalInfo(data);
        
        // Update default rate line unit based on load type
        if (data.load_type && this.rateLines.length > 0) {
            this.rateLines[0].selling.unit = data.load_type;
            this.rateLines[0].buying.unit = data.load_type;
        }
    },

    /**
     * Update Additional Information section
     */
    updateAdditionalInfo(data) {
        // Export CC
        const exportRequired = data.export_cc === true;
        document.getElementById('exportCCStatus').style.display = exportRequired ? 'flex' : 'none';
        document.getElementById('exportCCStatusNo').style.display = exportRequired ? 'none' : 'flex';

        // Import CC
        const importRequired = data.import_cc === true;
        document.getElementById('importCCStatus').style.display = importRequired ? 'flex' : 'none';
        document.getElementById('importCCStatusNo').style.display = importRequired ? 'none' : 'flex';

        // Pickup
        const pickupRequired = data.pickup_required === true;
        document.getElementById('pickupStatus').style.display = pickupRequired ? 'flex' : 'none';
        document.getElementById('pickupStatusNo').style.display = pickupRequired ? 'none' : 'flex';
        document.getElementById('pickupAddress').textContent = data.pickup_address || 'Address';
        document.getElementById('pickupAddress').style.display = pickupRequired && data.pickup_address ? 'inline' : 'none';

        // Delivery
        const deliveryRequired = data.delivery_required === true;
        document.getElementById('deliveryStatus').style.display = deliveryRequired ? 'flex' : 'none';
        document.getElementById('deliveryStatusNo').style.display = deliveryRequired ? 'none' : 'flex';
        document.getElementById('deliveryAddress').textContent = data.delivery_address || 'Address';
        document.getElementById('deliveryAddress').style.display = deliveryRequired && data.delivery_address ? 'inline' : 'none';

        // Update tags
        const tags = document.querySelectorAll('.qr-additional-tags .tag');
        tags.forEach((tag, idx) => {
            const tagText = tag.textContent;
            let isRequired = false;
            
            switch(tagText) {
                case 'Export Customs Clearance': isRequired = exportRequired; break;
                case 'Import Customs Clearance': isRequired = importRequired; break;
                case 'Pickup': isRequired = pickupRequired; break;
                case 'Delivery': isRequired = deliveryRequired; break;
            }
            
            tag.style.background = isRequired ? '#dbeafe' : '';
            tag.style.borderColor = isRequired ? '#3b82f6' : '';
            tag.style.color = isRequired ? '#3b82f6' : '';
        });
    },

    /**
     * Load existing bid data
     */
    loadExistingBid(bid) {
        // If line_items exist, load them
        if (bid.line_items && bid.line_items.length > 0) {
            this.rateLines = bid.line_items.map(item => ({
                id: item.id || this.generateId(),
                code: item.code,
                category: item.category,
                selling: {
                    unit: item.unit || '',
                    qty: item.qty || 1,
                    rate: item.rate || 0,
                    currency: item.currency || 'USD',
                    tax: item.tax_type || '영세',
                    vat: item.vat_percent || 0
                },
                buying: {
                    customer: item.buying_customer || '',
                    rate: item.buying_rate || 0,
                    currency: item.buying_currency || 'USD',
                    tax: item.buying_tax_type || '영세',
                    vat: item.buying_vat_percent || 0
                }
            }));
        } else {
            // Convert legacy data to new format
            this.convertLegacyBid(bid);
        }

        this.renderRatesTable();
        this.calculateTotals();
    },

    /**
     * Convert legacy bid format to new rate lines
     */
    convertLegacyBid(bid) {
        this.rateLines = [];
        const loadType = this.currentBidding?.load_type || '20DC';

        if (bid.freight_charge && bid.freight_charge > 0) {
            this.rateLines.push({
                id: this.generateId(),
                code: 'OFR',
                category: 'Ocean Freight',
                selling: { unit: loadType, qty: 1, rate: bid.freight_charge, currency: 'USD', tax: '영세', vat: 0 },
                buying: { customer: '', rate: 0, currency: 'USD', tax: '영세', vat: 0 }
            });
        }

        if (bid.local_charge && bid.local_charge > 0) {
            this.rateLines.push({
                id: this.generateId(),
                code: 'THC',
                category: 'Terminal Handling Charge',
                selling: { unit: loadType, qty: 1, rate: bid.local_charge, currency: 'USD', tax: '영세', vat: 0 },
                buying: { customer: '', rate: 0, currency: 'USD', tax: '영세', vat: 0 }
            });
        }

        if (bid.other_charge && bid.other_charge > 0) {
            this.rateLines.push({
                id: this.generateId(),
                code: 'OTHER',
                category: 'Other Charges',
                selling: { unit: 'SHPT', qty: 1, rate: bid.other_charge, currency: 'USD', tax: '영세', vat: 0 },
                buying: { customer: '', rate: 0, currency: 'USD', tax: '영세', vat: 0 }
            });
        }

        // If no lines, add default
        if (this.rateLines.length === 0) {
            this.initializeRateLines();
        }
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Currency display change
        const currencySelect = document.getElementById('displayCurrency');
        if (currencySelect) {
            currencySelect.addEventListener('change', (e) => {
                this.displayCurrency = e.target.value;
                this.calculateTotals();
            });
        }

        // Quote list item click
        document.querySelectorAll('.qr-quote-item').forEach(item => {
            item.addEventListener('click', () => {
                const quoteNo = item.dataset.quoteNo;
                this.selectQuote(quoteNo);
            });
        });

        // Navigation buttons
        document.getElementById('btnPrevious')?.addEventListener('click', () => this.navigateQuote(-1));
        document.getElementById('btnNext')?.addEventListener('click', () => this.navigateQuote(1));
    },

    /**
     * Initialize default rate lines
     */
    initializeRateLines() {
        const defaultUnit = this.currentBidding?.load_type || '20DC';
        
        this.rateLines = [
            {
                id: this.generateId(),
                code: 'FRT',
                category: 'Local Charge',
                selling: { unit: defaultUnit, qty: 1, rate: 200, currency: 'USD', tax: '영세', vat: 10 },
                buying: { customer: 'Panstar Enterprise', rate: 200, currency: 'USD', tax: '영세', vat: 10 }
            },
            {
                id: this.generateId(),
                code: 'BAF',
                category: 'Inland Charge',
                selling: { unit: defaultUnit, qty: 1, rate: 80, currency: 'USD', tax: '영세', vat: 10 },
                buying: { customer: 'Panstar Enterprise', rate: 80, currency: 'USD', tax: '영세', vat: 10 }
            },
            {
                id: this.generateId(),
                code: 'DOC',
                category: 'Ocean Freight',
                selling: { unit: 'BL', qty: 1, rate: 40000, currency: 'KRW', tax: '영세', vat: 10 },
                buying: { customer: 'Huge Trucking', rate: 40000, currency: 'KRW', tax: '영세', vat: 10 }
            }
        ];
    },

    /**
     * Generate unique ID
     */
    generateId() {
        return 'line_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    /**
     * Toggle Additional Information section
     */
    toggleAdditionalInfo() {
        const content = document.getElementById('additionalContent');
        const icon = document.getElementById('additionalToggleIcon');
        
        this.isAdditionalExpanded = !this.isAdditionalExpanded;
        
        if (this.isAdditionalExpanded) {
            content.classList.add('show');
            icon.classList.add('expanded');
        } else {
            content.classList.remove('show');
            icon.classList.remove('expanded');
        }
    },

    /**
     * Render rates table
     */
    renderRatesTable() {
        const tbody = document.getElementById('ratesTableBody');
        if (!tbody) return;

        if (this.rateLines.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="18" style="text-align: center; padding: 2rem; color: var(--qr-text-muted);">
                        <i class="fas fa-file-invoice-dollar" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
                        비용 항목을 추가해주세요
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.rateLines.map((line, idx) => this.renderRateLine(line, idx)).join('');
    },

    /**
     * Render single rate line
     */
    renderRateLine(line, idx) {
        // Generate code options
        const codeOptions = FREIGHT_CODES.map(fc => 
            `<option value="${fc.code}" ${line.code === fc.code ? 'selected' : ''}>${fc.code}</option>`
        ).join('');

        // Generate unit options
        const unitOptions = UNIT_OPTIONS.map(u => 
            `<option value="${u}" ${line.selling.unit === u ? 'selected' : ''}>${u}</option>`
        ).join('');

        // Generate currency options (selling)
        const sellingCurrencyOptions = CURRENCY_OPTIONS.map(c => 
            `<option value="${c}" ${line.selling.currency === c ? 'selected' : ''}>${c}</option>`
        ).join('');

        // Generate currency options (buying)
        const buyingCurrencyOptions = CURRENCY_OPTIONS.map(c => 
            `<option value="${c}" ${line.buying.currency === c ? 'selected' : ''}>${c}</option>`
        ).join('');

        // Generate tax options
        const sellingTaxOptions = TAX_OPTIONS.map(t => 
            `<option value="${t}" ${line.selling.tax === t ? 'selected' : ''}>${t}</option>`
        ).join('');

        const buyingTaxOptions = TAX_OPTIONS.map(t => 
            `<option value="${t}" ${line.buying.tax === t ? 'selected' : ''}>${t}</option>`
        ).join('');

        // Calculate amounts
        const sellingAmount = this.calculateAmount(line.selling);
        const sellingAmountKRW = this.convertToKRW(sellingAmount, line.selling.currency);
        const buyingAmount = this.calculateAmount(line.buying);
        const buyingAmountKRW = this.convertToKRW(buyingAmount, line.buying.currency);

        return `
            <tr data-line-id="${line.id}">
                <!-- Action & Freight Code Section -->
                <td class="col-action">
                    <button class="btn-row-delete" onclick="QuoteReg.removeLine('${line.id}')" title="삭제">
                        <i class="fas fa-times"></i>
                    </button>
                </td>
                <td class="col-code">
                    <div style="display: flex; gap: 2px;">
                        <select class="qr-rate-select" onchange="QuoteReg.updateLine('${line.id}', 'code', this.value)" style="flex:1;">
                            ${codeOptions}
                        </select>
                        <button class="btn-code-search" title="코드 검색">
                            <i class="fas fa-search"></i>
                        </button>
                    </div>
                </td>
                <td class="col-category">
                    <input type="text" class="qr-rate-input" value="${line.category}" 
                           onchange="QuoteReg.updateLine('${line.id}', 'category', this.value)">
                </td>
                <td class="col-unit">
                    <select class="qr-rate-select" onchange="QuoteReg.updateLine('${line.id}', 'selling.unit', this.value)">
                        <option value="">-</option>
                        ${unitOptions}
                    </select>
                </td>

                <!-- Selling Rate Section -->
                <td class="col-qty">
                    <input type="number" class="qr-rate-input" value="${line.selling.qty}" min="1"
                           onchange="QuoteReg.updateLine('${line.id}', 'selling.qty', this.value)">
                </td>
                <td class="col-rate">
                    <input type="number" class="qr-rate-input" value="${line.selling.rate}" step="0.01"
                           onchange="QuoteReg.updateLine('${line.id}', 'selling.rate', this.value)"
                           style="${line.selling.rate === 0 ? 'border-color: var(--qr-red);' : ''}">
                </td>
                <td class="col-currency">
                    <select class="qr-rate-select" onchange="QuoteReg.updateLine('${line.id}', 'selling.currency', this.value)">
                        ${sellingCurrencyOptions}
                    </select>
                </td>
                <td class="col-tax">
                    <select class="qr-rate-select" onchange="QuoteReg.updateLine('${line.id}', 'selling.tax', this.value)">
                        ${sellingTaxOptions}
                    </select>
                </td>
                <td class="col-vat">
                    <input type="number" class="qr-rate-input" value="${line.selling.vat}" step="1" min="0" max="100"
                           onchange="QuoteReg.updateLine('${line.id}', 'selling.vat', this.value)"
                           ${line.selling.tax === '영세' ? 'disabled style="background:#f5f5f5;"' : ''}>
                </td>
                <td class="col-amount">
                    <span class="amount-display">${this.formatNumber(sellingAmount)}</span>
                </td>
                <td class="col-amount-krw">
                    <span class="amount-display krw">${this.formatNumber(sellingAmountKRW)}</span>
                </td>

                <!-- Buying Rate Section -->
                <td class="col-customer">
                    <div class="customer-input-wrapper">
                        <input type="text" class="qr-rate-input" value="${line.buying.customer}" 
                               onchange="QuoteReg.updateLine('${line.id}', 'buying.customer', this.value)"
                               placeholder="Customer">
                        <button class="btn-code-search" title="거래처 검색">
                            <i class="fas fa-search"></i>
                        </button>
                    </div>
                </td>
                <td class="col-rate">
                    <input type="number" class="qr-rate-input" value="${line.buying.rate}" step="0.01"
                           onchange="QuoteReg.updateLine('${line.id}', 'buying.rate', this.value)">
                </td>
                <td class="col-currency">
                    <select class="qr-rate-select" onchange="QuoteReg.updateLine('${line.id}', 'buying.currency', this.value)">
                        ${buyingCurrencyOptions}
                    </select>
                </td>
                <td class="col-tax">
                    <select class="qr-rate-select" onchange="QuoteReg.updateLine('${line.id}', 'buying.tax', this.value)">
                        ${buyingTaxOptions}
                    </select>
                </td>
                <td class="col-vat">
                    <input type="number" class="qr-rate-input" value="${line.buying.vat}" step="1" min="0" max="100"
                           onchange="QuoteReg.updateLine('${line.id}', 'buying.vat', this.value)"
                           ${line.buying.tax === '영세' ? 'disabled style="background:#f5f5f5;"' : ''}>
                </td>
                <td class="col-amount">
                    <span class="amount-display">${this.formatNumber(buyingAmount)}</span>
                </td>
                <td class="col-amount-krw">
                    <span class="amount-display krw">${this.formatNumber(buyingAmountKRW)}</span>
                </td>
            </tr>
        `;
    },

    /**
     * Add new rate line
     */
    addRateLine() {
        const defaultUnit = this.currentBidding?.load_type || '20DC';
        
        this.rateLines.push({
            id: this.generateId(),
            code: 'OFR',
            category: 'Ocean Freight',
            selling: { unit: defaultUnit, qty: 1, rate: 0, currency: 'USD', tax: '영세', vat: 0 },
            buying: { customer: '', rate: 0, currency: 'USD', tax: '영세', vat: 0 }
        });

        this.renderRatesTable();
        this.calculateTotals();
    },

    /**
     * Remove rate line
     */
    removeLine(lineId) {
        if (this.rateLines.length <= 1) {
            this.showToast('최소 1개의 비용 항목이 필요합니다.', 'warning');
            return;
        }

        this.rateLines = this.rateLines.filter(line => line.id !== lineId);
        this.renderRatesTable();
        this.calculateTotals();
    },

    /**
     * Update rate line value
     */
    updateLine(lineId, field, value) {
        const line = this.rateLines.find(l => l.id === lineId);
        if (!line) return;

        const fields = field.split('.');
        
        if (fields.length === 1) {
            // Direct field (code, category)
            if (field === 'code') {
                const freightCode = FREIGHT_CODES.find(fc => fc.code === value);
                if (freightCode) {
                    line.code = value;
                    line.category = freightCode.category;
                    // Update default currency
                    line.selling.currency = freightCode.defaultCurrency;
                    line.buying.currency = freightCode.defaultCurrency;
                }
            } else {
                line[field] = value;
            }
        } else if (fields.length === 2) {
            // Nested field (selling.rate, buying.customer, etc.)
            const [section, prop] = fields;
            
            if (prop === 'tax') {
                line[section][prop] = value;
                if (value === '영세') {
                    line[section].vat = 0;
                } else {
                    line[section].vat = 10; // Default VAT 10%
                }
            } else if (['qty', 'rate', 'vat'].includes(prop)) {
                line[section][prop] = parseFloat(value) || 0;
            } else {
                line[section][prop] = value;
            }
        }

        this.renderRatesTable();
        this.calculateTotals();
    },

    /**
     * Calculate single rate amount
     */
    calculateAmount(rateData) {
        const base = (rateData.qty || 0) * (rateData.rate || 0);
        const vatAmount = rateData.tax === '과세' ? base * (rateData.vat || 0) / 100 : 0;
        return base + vatAmount;
    },

    /**
     * Convert amount to KRW
     */
    convertToKRW(amount, currency) {
        const rate = EXCHANGE_RATES[currency] || 1;
        return amount * rate;
    },

    /**
     * Calculate all totals
     */
    calculateTotals() {
        let totalSellingKRW = 0;
        let totalBuyingKRW = 0;

        this.rateLines.forEach(line => {
            const sellingAmount = this.calculateAmount(line.selling);
            const buyingAmount = this.calculateAmount(line.buying);
            
            totalSellingKRW += this.convertToKRW(sellingAmount, line.selling.currency);
            totalBuyingKRW += this.convertToKRW(buyingAmount, line.buying.currency);
        });

        const profitAmount = totalSellingKRW - totalBuyingKRW;
        const profitRatio = totalSellingKRW > 0 ? (profitAmount / totalSellingKRW * 100) : 0;

        // Update summary display
        document.getElementById('grandTotal').textContent = this.formatNumber(totalSellingKRW);
        document.getElementById('profitAmount').textContent = this.formatNumber(profitAmount);
        document.getElementById('profitRatio').textContent = profitRatio.toFixed(0) + '%';

        // Style profit based on positive/negative
        const profitEl = document.getElementById('profitAmount');
        if (profitAmount >= 0) {
            profitEl.style.color = 'var(--qr-green)';
        } else {
            profitEl.style.color = 'var(--qr-red)';
        }

        return { totalSellingKRW, totalBuyingKRW, profitAmount, profitRatio };
    },

    /**
     * Format number with commas
     */
    formatNumber(num) {
        if (num === null || num === undefined || isNaN(num)) return '0';
        return Math.round(num).toLocaleString('en-US');
    },

    /**
     * Select quote from list
     */
    selectQuote(quoteNo) {
        // Update active state
        document.querySelectorAll('.qr-quote-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.quoteNo === quoteNo) {
                item.classList.add('active');
            }
        });

        // Load quote data (would normally fetch from API)
        this.loadBiddingDetail(quoteNo);
    },

    /**
     * Navigate to previous/next quote
     */
    navigateQuote(direction) {
        const items = Array.from(document.querySelectorAll('.qr-quote-item'));
        const currentIndex = items.findIndex(item => item.classList.contains('active'));
        const newIndex = currentIndex + direction;

        if (newIndex >= 0 && newIndex < items.length) {
            const newQuoteNo = items[newIndex].dataset.quoteNo;
            this.selectQuote(newQuoteNo);
        }

        // Update button states
        document.getElementById('btnPrevious').disabled = newIndex <= 0;
        document.getElementById('btnNext').disabled = newIndex >= items.length - 1;
    },

    /**
     * Reload quote (reset to original)
     */
    reloadQuote() {
        if (confirm('입력한 내용을 초기화하시겠습니까?')) {
            this.initializeRateLines();
            this.renderRatesTable();
            this.calculateTotals();
            this.showToast('견적이 초기화되었습니다.', 'info');
        }
    },

    /**
     * Save quote (draft)
     */
    async saveQuote() {
        if (!this.forwarder) {
            this.showToast('로그인이 필요합니다.', 'error');
            return;
        }

        const quoteData = this.collectQuoteData();
        quoteData.status = 'draft';

        try {
            // API call would go here
            console.log('📤 Saving quote:', quoteData);
            
            this.showToast('견적이 저장되었습니다.', 'success');
        } catch (error) {
            console.error('Save error:', error);
            this.showToast('저장에 실패했습니다.', 'error');
        }
    },

    /**
     * Edit quote
     */
    editQuote() {
        // Enable editing mode
        document.querySelectorAll('.qr-rate-input, .qr-rate-select').forEach(el => {
            el.disabled = false;
        });
        this.showToast('수정 모드가 활성화되었습니다.', 'info');
    },

    /**
     * Submit quote (final)
     */
    async submitQuote() {
        if (!this.forwarder) {
            this.showToast('로그인이 필요합니다.', 'error');
            return;
        }

        // Validation
        const hasValidRate = this.rateLines.some(line => line.selling.rate > 0);
        if (!hasValidRate) {
            this.showToast('최소 1개 항목에 Rate를 입력해주세요.', 'warning');
            return;
        }

        if (!confirm('견적서를 제출하시겠습니까?')) return;

        const quoteData = this.collectQuoteData();
        quoteData.status = 'submitted';

        try {
            // API call would go here
            console.log('📤 Submitting quote:', quoteData);
            
            this.showToast('견적서가 제출되었습니다!', 'success');
            
            // Redirect to bidding list after success
            setTimeout(() => {
                window.location.href = 'bidding-list.html';
            }, 1500);

        } catch (error) {
            console.error('Submit error:', error);
            this.showToast('제출에 실패했습니다.', 'error');
        }
    },

    /**
     * Collect all quote data
     */
    collectQuoteData() {
        const totals = this.calculateTotals();

        // Categorize line items
        let freightCharge = 0;
        let localCharge = 0;
        let otherCharge = 0;

        const lineItems = this.rateLines.map((line, idx) => {
            const sellingAmount = this.calculateAmount(line.selling);
            const code = line.code.toUpperCase();
            
            // Categorize
            if (['OFR', 'AFR', 'BAF', 'CAF', 'LSS', 'EBS', 'PSS', 'CIC'].includes(code)) {
                freightCharge += sellingAmount;
            } else if (['THC', 'WFG', 'CFS', 'DOC', 'SEAL', 'AMS', 'ENS', 'HANDLING'].includes(code)) {
                localCharge += sellingAmount;
            } else {
                otherCharge += sellingAmount;
            }

            return {
                code: line.code,
                category: line.category,
                unit: line.selling.unit,
                qty: line.selling.qty,
                rate: line.selling.rate,
                currency: line.selling.currency,
                tax_type: line.selling.tax,
                vat_percent: line.selling.vat,
                buying_customer: line.buying.customer,
                buying_rate: line.buying.rate,
                buying_currency: line.buying.currency,
                buying_tax_type: line.buying.tax,
                buying_vat_percent: line.buying.vat,
                sort_order: idx
            };
        });

        return {
            bidding_id: this.currentBidding?.id,
            forwarder_id: this.forwarder?.id,
            total_amount: totals.totalSellingKRW,
            freight_charge: freightCharge,
            local_charge: localCharge,
            other_charge: otherCharge,
            profit_amount: totals.profitAmount,
            profit_ratio: totals.profitRatio,
            line_items: lineItems,
            expire_date: document.getElementById('expireDate')?.value || null
        };
    },

    /**
     * Update UI state
     */
    updateUI() {
        // Update quote list count
        const count = document.querySelectorAll('.qr-quote-item').length;
        document.getElementById('quoteListCount').textContent = count;
    },

    /**
     * Show toast message
     */
    showToast(message, type = 'info') {
        // Create toast element
        let toast = document.getElementById('qr-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'qr-toast';
            toast.style.cssText = `
                position: fixed;
                bottom: 30px;
                right: 30px;
                padding: 12px 20px;
                border-radius: 8px;
                color: white;
                font-size: 0.9rem;
                font-weight: 500;
                z-index: 10000;
                transform: translateX(120%);
                transition: transform 0.3s ease;
            `;
            document.body.appendChild(toast);
        }

        // Set color based on type
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        toast.style.background = colors[type] || colors.info;
        toast.textContent = message;

        // Show
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);

        // Hide after delay
        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
        }, 3000);
    }
};

// Export for global access
window.QuoteReg = QuoteReg;
