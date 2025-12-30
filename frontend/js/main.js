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
    document.querySelectorAll('.product-menu li').forEach(li => {
        let searchText = '';
        if (productName === 'exchange-rate') {
            searchText = 'Exchange Rate';
        } else if (productName === 'interest-rates') {
            searchText = 'Interest Rates';
        } else if (productName === 'inflation') {
            searchText = 'Inflation';
        } else if (productName === 'gdp') {
            searchText = '주요 지표';
        } else if (productName === 'gdp-growth') {
            searchText = 'Economy Growth Rate';
        }
        
        if (searchText && li.textContent.includes(searchText)) {
            li.classList.add('selected');
        }
    });
    
    // Hide all product panels and submenu
    const panels = {
        'exchange-rate': document.getElementById('economy-panel'),
        'interest-rates': document.getElementById('interest-rates-panel'),
        'inflation': document.getElementById('inflation-panel'),
        'gdp': document.getElementById('gdp-panel'),
        'trade': document.getElementById('trade-panel'),
        'employment': document.getElementById('employment-panel'),
        'gdp-growth': document.getElementById('gdp-growth-panel')
    };
    const gdpSubmenu = document.getElementById('gdp-submenu');
    
    // GDP 패널이 이미 표시되어 있는지 확인
    const gdpPanel = panels['gdp'];
    const isGDPPanelVisible = productName === 'gdp' && gdpPanel && gdpPanel.style.display !== 'none';
    
    // Hide all panels
    Object.values(panels).forEach(panel => {
        if (panel) {
            panel.style.display = 'none';
        }
    });
    
    // Update menu item selected state
    const productDisplayNames = {
        'exchange-rate': 'Exchange Rate',
        'interest-rates': 'Interest Rates',
        'inflation': 'Inflation',
        'gdp': '주요 지표',
        'trade': '수출입 통계',
        'employment': '고용 통계',
        'gdp-growth': 'Economy Growth Rate'
    };
    
    document.querySelectorAll('.product-menu li').forEach(li => {
        li.classList.remove('selected');
        const displayName = productDisplayNames[productName];
        if (displayName && li.textContent.includes(displayName)) {
            li.classList.add('selected');
        }
    });
    
    // Show selected panel/submenu and initialize if needed
    if (productName === 'exchange-rate' && panels['exchange-rate']) {
        if (gdpSubmenu) gdpSubmenu.style.display = 'none';
        panels['exchange-rate'].style.display = 'block';
    } else if (productName === 'interest-rates' && panels['interest-rates']) {
        if (gdpSubmenu) gdpSubmenu.style.display = 'none';
        panels['interest-rates'].style.display = 'block';
        if (!window.interestDataLoaded && typeof initInterestRates === 'function') {
            initInterestRates();
        }
    } else if (productName === 'inflation' && panels['inflation']) {
        if (gdpSubmenu) gdpSubmenu.style.display = 'none';
        panels['inflation'].style.display = 'block';
        if (!window.inflationDataLoaded && typeof initInflation === 'function') {
            initInflation();
        }
    } else if (productName === 'gdp') {
        if (gdpPanel) {
            gdpPanel.style.display = 'block';
            if (!window.gdpDataLoaded && typeof initGDP === 'function') {
                initGDP();
            }
        }
        
        if (isGDPPanelVisible) {
            if (gdpSubmenu) {
                gdpSubmenu.classList.toggle('show');
                if (gdpSubmenu.classList.contains('show') && typeof updateGDPSubmenuPosition === 'function') {
                    updateGDPSubmenuPosition();
                }
            }
        } else {
            if (gdpSubmenu) {
                gdpSubmenu.classList.add('show');
                if (typeof updateGDPSubmenuPosition === 'function') {
                    updateGDPSubmenuPosition();
                }
            }
        }
    } else if (productName === 'trade' && panels['trade']) {
        if (gdpSubmenu) gdpSubmenu.classList.remove('show');
        panels['trade'].style.display = 'block';
        if (!window.tradeDataLoaded && typeof initTrade === 'function') {
            initTrade();
        }
    } else if (productName === 'employment' && panels['employment']) {
        if (gdpSubmenu) gdpSubmenu.classList.remove('show');
        panels['employment'].style.display = 'block';
        if (!window.employmentDataLoaded && typeof initEmployment === 'function') {
            initEmployment();
        }
    } else if (productName === 'gdp-growth' && panels['gdp-growth']) {
        if (gdpSubmenu) gdpSubmenu.classList.remove('show');
        panels['gdp-growth'].style.display = 'block';
        if (!window.gdpGrowthDataLoaded && typeof initGDPGrowth === 'function') {
            initGDPGrowth();
        }
    } else {
        if (gdpSubmenu) gdpSubmenu.classList.remove('show');
    }
}

function updateGDPSubmenuPosition() {
    const gdpSubmenu = document.getElementById('gdp-submenu');
    if (!gdpSubmenu) return;
    
    const gdpMenuItem = Array.from(document.querySelectorAll('.product-menu li')).find(li => 
        li.textContent.includes('주요 지표')
    );
    if (gdpMenuItem) {
        const rect = gdpMenuItem.getBoundingClientRect();
        const sidebar = gdpMenuItem.closest('.product-sidebar');
        if (sidebar) {
            const sidebarRect = sidebar.getBoundingClientRect();
            gdpSubmenu.style.top = `${rect.top - sidebarRect.top}px`;
        }
    }
}

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
window.updateGDPSubmenuPosition = updateGDPSubmenuPosition;
window.initScrollReveal = initScrollReveal;

