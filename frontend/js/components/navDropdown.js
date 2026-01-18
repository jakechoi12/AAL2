/**
 * Navigation Dropdown Module
 * 상단 네비게이션 드롭다운 메뉴 기능
 */

const NavDropdown = {
    /**
     * 초기화
     */
    init() {
        this.bindEvents();
        this.highlightCurrentPage();
    },

    /**
     * 이벤트 바인딩
     */
    bindEvents() {
        // 드롭다운 토글 버튼 클릭
        document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleDropdown(toggle.closest('.nav-item'));
            });
        });

        // 외부 클릭 시 닫기
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.nav-item.has-dropdown')) {
                this.closeAllDropdowns();
            }
        });

        // ESC 키로 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllDropdowns();
            }
        });

        // coming-soon 링크 클릭 방지
        document.querySelectorAll('.coming-soon').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
            });
        });
    },

    /**
     * 드롭다운 토글
     * @param {HTMLElement} navItem - .nav-item 요소
     */
    toggleDropdown(navItem) {
        const isOpen = navItem.classList.contains('open');
        
        // 다른 열린 드롭다운 닫기
        this.closeAllDropdowns();
        
        // 현재 드롭다운 토글
        if (!isOpen) {
            navItem.classList.add('open');
        }
    },

    /**
     * 모든 드롭다운 닫기
     */
    closeAllDropdowns() {
        document.querySelectorAll('.nav-item.open').forEach(item => {
            item.classList.remove('open');
        });
    },

    /**
     * 현재 페이지 하이라이트
     */
    highlightCurrentPage() {
        const currentPath = window.location.pathname;
        const currentPage = currentPath.split('/').pop() || 'index.html';
        
        // 모든 네비게이션 링크 확인
        document.querySelectorAll('nav .dropdown-menu a, nav .nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (!href || href === '#') return;
            
            const linkPage = href.split('/').pop();
            
            if (currentPage === linkPage || 
                (currentPage === '' && linkPage === 'ai_studio_code_F2.html') ||
                (currentPage === 'index.html' && linkPage === 'ai_studio_code_F2.html')) {
                link.classList.add('active');
                
                // 부모 nav-item도 active 표시
                const parentNavItem = link.closest('.nav-item');
                if (parentNavItem) {
                    parentNavItem.classList.add('active');
                }
            }
        });
    }
};

// DOM 로드 후 초기화
document.addEventListener('DOMContentLoaded', () => {
    NavDropdown.init();
});

// 전역 접근 가능하도록 export
window.NavDropdown = NavDropdown;
