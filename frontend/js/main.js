/**
 * AAL Application - Main Entry Point
 * 공통 UI 로직 및 초기화 코드
 */

// ============================================================
// SCROLL REVEAL ANIMATION
// ============================================================

function initScrollReveal() {
    const revealElements = document.querySelectorAll('.reveal');
    const revealOnScroll = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: "0px 0px -50px 0px" });
    revealElements.forEach(el => revealOnScroll.observe(el));
}

// ============================================================
// TAB & PRODUCT SWITCHING
// ============================================================

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.market-content').forEach(panel => panel.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById(tabName + '-panel').classList.add('active');
}

function switchProduct(productName) {
    // Update sidebar menu
    document.querySelectorAll('.product-menu li').forEach(li => li.classList.remove('selected'));
    
    // Product display names mapping
    const productDisplayNames = {
        'exchange-rate': 'Exchange Rate',
        'interest-rates': 'Interest Rates',
        'inflation': 'Inflation',
        'gdp-indicator': 'GDP',
        'gdp-per-capita': 'GDP per Capita',
        'gni': 'GNI',
        'trade': 'Export x Import',
        'employment': 'Employment',
        'gdp-growth': 'Economy Growth Rate',
        'global-stocks': 'Global Stocks'
    };
    
    document.querySelectorAll('.product-menu li').forEach(li => {
        const displayName = productDisplayNames[productName];
        // Use exact match (trim whitespace) to prevent "GDP" from matching "GDP per Capita"
        if (displayName && li.textContent.trim() === displayName) {
            li.classList.add('selected');
        }
    });
    
    // Hide all product panels and submenu
    const panels = {
        'exchange-rate': document.getElementById('economy-panel'),
        'interest-rates': document.getElementById('interest-rates-panel'),
        'inflation': document.getElementById('inflation-panel'),
        'gdp-indicator': document.getElementById('gdp-indicator-panel'),
        'gdp-per-capita': document.getElementById('gdp-per-capita-panel'),
        'gni': document.getElementById('gni-panel'),
        'trade': document.getElementById('trade-panel'),
        'employment': document.getElementById('employment-panel'),
        'gdp-growth': document.getElementById('gdp-growth-panel'),
        'global-stocks': document.getElementById('global-stocks-panel')
    };
    const gdpSubmenu = document.getElementById('gdp-submenu');
    
    // Hide all panels
    Object.values(panels).forEach(panel => {
        if (panel) {
            panel.style.display = 'none';
        }
    });
    
    // Hide GDP submenu by default
    if (gdpSubmenu) gdpSubmenu.classList.remove('show');
    
    // Show selected panel and initialize if needed
    if (productName === 'exchange-rate' && panels['exchange-rate']) {
        panels['exchange-rate'].style.display = 'block';
    } else if (productName === 'interest-rates' && panels['interest-rates']) {
        panels['interest-rates'].style.display = 'block';
        if (!window.interestDataLoaded && typeof initInterestRates === 'function') {
            initInterestRates();
        }
    } else if (productName === 'inflation' && panels['inflation']) {
        panels['inflation'].style.display = 'block';
        if (!window.inflationDataLoaded && typeof initInflation === 'function') {
            initInflation();
        }
    } else if (productName === 'gdp-indicator' && panels['gdp-indicator']) {
        panels['gdp-indicator'].style.display = 'block';
        if (!window.gdpIndicatorDataLoaded && typeof initGDPIndicator === 'function') {
            initGDPIndicator();
        }
    } else if (productName === 'gdp-per-capita' && panels['gdp-per-capita']) {
        panels['gdp-per-capita'].style.display = 'block';
        if (!window.gdpPerCapitaDataLoaded && typeof initGDPPerCapita === 'function') {
            initGDPPerCapita();
        }
    } else if (productName === 'gni' && panels['gni']) {
        panels['gni'].style.display = 'block';
        if (!window.gniDataLoaded && typeof initGNI === 'function') {
            initGNI();
        }
    } else if (productName === 'trade' && panels['trade']) {
        panels['trade'].style.display = 'block';
        if (!window.tradeDataLoaded && typeof initTrade === 'function') {
            initTrade();
        }
    } else if (productName === 'employment' && panels['employment']) {
        panels['employment'].style.display = 'block';
        if (!window.employmentDataLoaded && typeof initEmployment === 'function') {
            initEmployment();
        }
    } else if (productName === 'gdp-growth' && panels['gdp-growth']) {
        panels['gdp-growth'].style.display = 'block';
        if (!window.gdpGrowthDataLoaded && typeof initGDPGrowth === 'function') {
            initGDPGrowth();
        }
    } else if (productName === 'global-stocks' && panels['global-stocks']) {
        panels['global-stocks'].style.display = 'block';
        if (!window.globalStocksDataLoaded && typeof initGlobalStocks === 'function') {
            initGlobalStocks();
        }
    }
}

// updateGDPSubmenuPosition removed - 주요 지표 tab has been removed

// ============================================================
// INITIALIZATION
// ============================================================

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 스크롤 애니메이션
    initScrollReveal();
    
    // 초기 날짜 설정 (Exchange Rate)
    if (typeof initDateInputs === 'function') {
        initDateInputs();
    }
    
    // 환율 데이터 로드
    if (typeof fetchExchangeRateData === 'function') {
        fetchExchangeRateData();
    }
    if (typeof fetchAllCurrencyRates === 'function') {
        fetchAllCurrencyRates();
    }
    
    console.log('✅ AAL Application initialized');
});

// Expose to window for backwards compatibility
window.switchTab = switchTab;
window.switchProduct = switchProduct;
window.initScrollReveal = initScrollReveal;

