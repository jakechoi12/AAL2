/**
 * Authentication Module
 * 사용자 인증 (로그인/회원가입) 기능
 */

const AUTH_API_BASE = 'http://localhost:5000/api/auth';
const QUOTE_API_BASE = 'http://localhost:8001';

const Auth = {
    // State
    user: null,
    currentView: 'login-type', // login-type, login, register, register-form
    selectedUserType: null, // shipper, forwarder
    selectedLoginType: null, // shipper, forwarder (로그인 시 선택한 타입)
    
    /**
     * Initialize the module
     */
    init() {
        console.log('🔐 Auth module initialized');
        
        // Load stored session
        this.loadSession();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Update UI based on login state
        this.updateAuthUI();
    },
    
    /**
     * Load stored session from localStorage
     */
    loadSession() {
        const stored = localStorage.getItem('aal_user');
        if (stored) {
            try {
                this.user = JSON.parse(stored);
                console.log('✅ Session restored for:', this.user.email);
            } catch (e) {
                localStorage.removeItem('aal_user');
            }
        }
    },
    
    /**
     * Save session to localStorage
     */
    saveSession() {
        if (this.user) {
            localStorage.setItem('aal_user', JSON.stringify(this.user));
        }
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Close modal on overlay click
        const overlay = document.getElementById('authModalOverlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.closeModal();
                }
            });
        }
        
        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
        
        // Password toggle buttons
        document.querySelectorAll('.password-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const input = e.target.closest('.password-field').querySelector('input');
                const icon = e.target.closest('.password-toggle').querySelector('i');
                
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.replace('fa-eye', 'fa-eye-slash');
                } else {
                    input.type = 'password';
                    icon.classList.replace('fa-eye-slash', 'fa-eye');
                }
            });
        });
    },
    
    /**
     * Update auth UI based on login state
     */
    updateAuthUI() {
        const authContainer = document.getElementById('headerAuthContainer');
        if (!authContainer) return;
        
        if (this.user) {
            // Logged in state
            const userTypeLabel = this.user.user_type === 'shipper' ? '화주' : '포워더';
            authContainer.innerHTML = `
                <div class="header-user-info">
                    <div class="user-avatar">${this.user.company.charAt(0).toUpperCase()}</div>
                    <div class="user-details">
                        <span class="user-name">${this.user.company}</span>
                        <span class="user-type">${userTypeLabel}</span>
                    </div>
                </div>
                <button class="header-logout-btn" onclick="Auth.logout()">
                    <i class="fas fa-sign-out-alt"></i> 로그아웃
                </button>
            `;
        } else {
            // Logged out state
            authContainer.innerHTML = `
                <button class="header-auth-btn" onclick="Auth.openModal()">
                    <i class="fas fa-sign-in-alt"></i> 로그인
                </button>
            `;
        }
    },
    
    /**
     * Open auth modal
     */
    openModal() {
        const overlay = document.getElementById('authModalOverlay');
        if (overlay) {
            overlay.classList.add('active');
            this.showLoginTypeView();
        }
    },
    
    /**
     * Close auth modal
     */
    closeModal() {
        const overlay = document.getElementById('authModalOverlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
        this.clearErrors();
    },
    
    /**
     * Show login type selection view
     */
    showLoginTypeView() {
        this.currentView = 'login-type';
        this.selectedLoginType = null;
        document.getElementById('authModalTitle').textContent = '로그인';
        document.getElementById('loginTypeView').style.display = 'block';
        document.getElementById('loginView').style.display = 'none';
        document.getElementById('registerTypeView').style.display = 'none';
        document.getElementById('registerFormView').style.display = 'none';
        this.updateStepIndicator(1);
        
        // Reset login type selection
        document.querySelectorAll('#loginTypeView .user-type-option').forEach(opt => {
            opt.classList.remove('selected');
        });
    },
    
    /**
     * Select login type and proceed to login form
     */
    selectLoginType(type) {
        this.selectedLoginType = type;
        
        // Update selection UI
        document.querySelectorAll('#loginTypeView .user-type-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        event.currentTarget.classList.add('selected');
        
        // Show login form after a short delay
        setTimeout(() => {
            this.showLoginView();
        }, 200);
    },
    
    /**
     * Go back to login type selection
     */
    goBackToLoginType() {
        this.showLoginTypeView();
    },
    
    /**
     * Show login view (form)
     */
    showLoginView() {
        this.currentView = 'login';
        const typeLabel = this.selectedLoginType === 'shipper' ? '화주' : '포워더';
        document.getElementById('authModalTitle').textContent = `${typeLabel} 로그인`;
        document.getElementById('loginTypeView').style.display = 'none';
        document.getElementById('loginView').style.display = 'block';
        document.getElementById('registerTypeView').style.display = 'none';
        document.getElementById('registerFormView').style.display = 'none';
        this.updateStepIndicator(2);
    },
    
    /**
     * Show register type selection view
     */
    showRegisterTypeView() {
        this.currentView = 'register';
        this.selectedUserType = null;
        document.getElementById('authModalTitle').textContent = '회원가입';
        document.getElementById('loginTypeView').style.display = 'none';
        document.getElementById('loginView').style.display = 'none';
        document.getElementById('registerTypeView').style.display = 'block';
        document.getElementById('registerFormView').style.display = 'none';
        this.updateStepIndicator(1);
        
        // Reset user type selection
        document.querySelectorAll('#registerTypeView .user-type-option').forEach(opt => {
            opt.classList.remove('selected');
        });
    },
    
    /**
     * Select user type and proceed to form
     */
    selectUserType(type) {
        this.selectedUserType = type;
        
        // Update selection UI
        document.querySelectorAll('.user-type-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        event.currentTarget.classList.add('selected');
        
        // Show register form after a short delay
        setTimeout(() => {
            this.showRegisterFormView();
        }, 200);
    },
    
    /**
     * Show register form view
     */
    showRegisterFormView() {
        this.currentView = 'register-form';
        const typeLabel = this.selectedUserType === 'shipper' ? '화주' : '포워더';
        document.getElementById('authModalTitle').textContent = `${typeLabel} 회원가입`;
        document.getElementById('loginTypeView').style.display = 'none';
        document.getElementById('loginView').style.display = 'none';
        document.getElementById('registerTypeView').style.display = 'none';
        document.getElementById('registerFormView').style.display = 'block';
        this.updateStepIndicator(2);
    },
    
    /**
     * Update step indicator
     */
    updateStepIndicator(step) {
        document.querySelectorAll('.auth-step').forEach((el, idx) => {
            if (idx < step) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
    },
    
    /**
     * Go back to previous view
     */
    goBack() {
        if (this.currentView === 'register-form') {
            this.showRegisterTypeView();
        } else if (this.currentView === 'register') {
            this.showLoginTypeView();
        } else if (this.currentView === 'login') {
            this.showLoginTypeView();
        }
    },
    
    /**
     * Clear error/success messages
     */
    clearErrors() {
        document.querySelectorAll('.auth-error, .auth-success').forEach(el => {
            el.classList.remove('show');
            el.textContent = '';
        });
    },
    
    /**
     * Show error message
     */
    showError(message, viewId = null) {
        this.clearErrors();
        const errorEl = viewId 
            ? document.querySelector(`#${viewId} .auth-error`)
            : document.querySelector('.auth-error');
        
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.add('show');
        }
    },
    
    /**
     * Show success message
     */
    showSuccess(message, viewId = null) {
        this.clearErrors();
        const successEl = viewId 
            ? document.querySelector(`#${viewId} .auth-success`)
            : document.querySelector('.auth-success');
        
        if (successEl) {
            successEl.textContent = message;
            successEl.classList.add('show');
        }
    },
    
    /**
     * Submit login
     */
    async submitLogin() {
        const email = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value;
        
        if (!email || !password) {
            this.showError('이메일과 비밀번호를 입력해주세요.', 'loginView');
            return;
        }
        
        const submitBtn = document.getElementById('loginSubmitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 로그인 중...';
        
        try {
            let response, data;
            
            if (this.selectedLoginType === 'forwarder') {
                // 포워더 로그인 - quote_backend 사용
                response = await fetch(`${QUOTE_API_BASE}/api/forwarder/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || '로그인에 실패했습니다.');
                }
                
                // 포워더 데이터를 통합 형식으로 변환
                this.user = {
                    id: data.forwarder.id,
                    user_type: 'forwarder',
                    company: data.forwarder.company,
                    name: data.forwarder.name,
                    email: data.forwarder.email,
                    phone: data.forwarder.phone,
                    business_no: data.forwarder.business_no
                };
            } else {
                // 화주 로그인 - auth 백엔드 사용
                response = await fetch(`${AUTH_API_BASE}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                
                data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || '로그인에 실패했습니다.');
                }
                
                this.user = data.user;
            }
            
            this.saveSession();
            this.closeModal();
            this.updateAuthUI();
            
            // Show welcome message
            this.showToast(`환영합니다, ${this.user.name}님!`);
            
        } catch (error) {
            console.error('Login error:', error);
            this.showError(error.message, 'loginView');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '로그인';
        }
    },
    
    /**
     * Submit registration
     */
    async submitRegister() {
        const formData = {
            user_type: this.selectedUserType,
            company: document.getElementById('regCompany').value.trim(),
            name: document.getElementById('regName').value.trim(),
            business_no: document.getElementById('regBusinessNo').value.trim() || null,
            email: document.getElementById('regEmail').value.trim(),
            password: document.getElementById('regPassword').value,
            phone: document.getElementById('regPhone').value.trim()
        };
        
        // Validation
        if (!formData.company || !formData.name || !formData.email || !formData.password || !formData.phone) {
            this.showError('필수 항목을 모두 입력해주세요.', 'registerFormView');
            return;
        }
        
        // Password confirmation
        const passwordConfirm = document.getElementById('regPasswordConfirm').value;
        if (formData.password !== passwordConfirm) {
            this.showError('비밀번호가 일치하지 않습니다.', 'registerFormView');
            return;
        }
        
        // Password length validation
        if (formData.password.length < 6) {
            this.showError('비밀번호는 최소 6자 이상이어야 합니다.', 'registerFormView');
            return;
        }
        
        const submitBtn = document.getElementById('registerSubmitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 등록 중...';
        
        try {
            let response, data;
            
            if (this.selectedUserType === 'forwarder') {
                // 포워더 회원가입 - quote_backend 사용
                response = await fetch(`${QUOTE_API_BASE}/api/forwarder/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        company: formData.company,
                        name: formData.name,
                        business_no: formData.business_no,
                        email: formData.email,
                        password: formData.password,
                        phone: formData.phone
                    })
                });
                
                data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || '회원가입에 실패했습니다.');
                }
                
                // 포워더 데이터를 통합 형식으로 변환
                this.user = {
                    id: data.forwarder.id,
                    user_type: 'forwarder',
                    company: data.forwarder.company,
                    name: data.forwarder.name,
                    email: data.forwarder.email,
                    phone: data.forwarder.phone,
                    business_no: data.forwarder.business_no
                };
            } else {
                // 화주 회원가입 - auth 백엔드 사용
                response = await fetch(`${AUTH_API_BASE}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || '회원가입에 실패했습니다.');
                }
                
                this.user = data.user;
            }
            
            this.saveSession();
            this.closeModal();
            this.updateAuthUI();
            
            // Show success message
            this.showToast(`회원가입이 완료되었습니다. 환영합니다, ${this.user.name}님!`);
            
        } catch (error) {
            console.error('Registration error:', error);
            this.showError(error.message, 'registerFormView');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> 회원가입';
        }
    },
    
    /**
     * Logout
     */
    logout() {
        if (confirm('로그아웃 하시겠습니까?')) {
            this.user = null;
            localStorage.removeItem('aal_user');
            this.updateAuthUI();
            this.showToast('로그아웃 되었습니다.');
        }
    },
    
    /**
     * Check if user is logged in
     */
    isLoggedIn() {
        return this.user !== null;
    },
    
    /**
     * Get current user
     */
    getUser() {
        return this.user;
    },
    
    /**
     * Show toast notification
     */
    showToast(message) {
        // Check for existing toast or create new one
        let toast = document.getElementById('authToast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'authToast';
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                background: linear-gradient(135deg, var(--accent-color), #4f46e5);
                color: white;
                border-radius: 10px;
                font-weight: 500;
                z-index: 10001;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                transform: translateY(100px);
                opacity: 0;
                transition: all 0.3s ease;
            `;
            document.body.appendChild(toast);
        }
        
        toast.textContent = message;
        
        // Show toast
        setTimeout(() => {
            toast.style.transform = 'translateY(0)';
            toast.style.opacity = '1';
        }, 10);
        
        // Hide toast after 3 seconds
        setTimeout(() => {
            toast.style.transform = 'translateY(100px)';
            toast.style.opacity = '0';
        }, 3000);
    }
};

// Export for global access
window.Auth = Auth;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    Auth.init();
});
