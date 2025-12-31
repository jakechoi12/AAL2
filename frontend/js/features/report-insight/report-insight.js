/**
 * Report & Insight - Frontend JavaScript
 * Handles API calls, rendering, filtering, and interactions
 */

// ============================================
// Configuration
// ============================================

const API_BASE = '/api/reports';
const PAGE_SIZE = 12;

// State
let currentPage = 1;
let currentCategory = 'all';
let currentSort = 'newest';
let currentSearch = '';
let selectedOrgs = [];
let selectedTags = [];
let dateFrom = '';
let dateTo = '';
let totalReports = 0;
let bookmarkedIds = new Set();

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Load bookmarks from localStorage
    loadBookmarks();
    
    // Initialize page
    initializePage();
    
    // Setup event listeners
    setupEventListeners();
});

async function initializePage() {
    try {
        // Load stats
        await loadStats();
        
        // Load filters
        await loadFilters();
        
        // Load featured reports
        await loadFeaturedReports();
        
        // Load reports
        await loadReports();
    } catch (error) {
        console.error('Error initializing page:', error);
        showToast('Failed to load data. Please refresh the page.', 'error');
    }
}

function setupEventListeners() {
    // Search input - Enter key
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchReports();
            }
        });
    }
    
    // Date filters
    const dateFromInput = document.getElementById('dateFrom');
    const dateToInput = document.getElementById('dateTo');
    
    if (dateFromInput) {
        dateFromInput.addEventListener('change', () => {
            dateFrom = dateFromInput.value;
            loadReports();
        });
    }
    
    if (dateToInput) {
        dateToInput.addEventListener('change', () => {
            dateTo = dateToInput.value;
            loadReports();
        });
    }
}

// ============================================
// API Functions
// ============================================

async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

// ============================================
// Data Loading Functions
// ============================================

async function loadStats() {
    try {
        const stats = await fetchAPI('/stats');
        
        document.getElementById('totalReports').textContent = stats.total_reports;
        document.getElementById('totalOrgs').textContent = stats.total_organizations;
        document.getElementById('thisMonth').textContent = stats.this_month;
        
        // Update category counts
        document.getElementById('count-all').textContent = stats.total_reports;
        
        stats.category_counts.forEach(cat => {
            const countEl = document.getElementById(`count-${cat.category}`);
            if (countEl) {
                countEl.textContent = cat.count;
            }
        });
        
        totalReports = stats.total_reports;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadFilters() {
    try {
        const filters = await fetchAPI('/filters');
        
        // Render organization filters
        const orgContainer = document.getElementById('orgFilters');
        if (orgContainer) {
            orgContainer.innerHTML = filters.organizations.slice(0, 8).map(org => `
                <div class="filter-option" onclick="toggleOrgFilter('${escapeHtml(org.name)}')">
                    <input type="checkbox" id="org-${escapeHtml(org.name)}" ${selectedOrgs.includes(org.name) ? 'checked' : ''}>
                    <label for="org-${escapeHtml(org.name)}">${escapeHtml(org.name)}</label>
                    <span class="filter-count">${org.count}</span>
                </div>
            `).join('');
        }
        
        // Render tag filters
        const tagContainer = document.getElementById('tagFilters');
        if (tagContainer) {
            tagContainer.innerHTML = filters.tags.slice(0, 10).map(tag => `
                <div class="filter-option" onclick="toggleTagFilter('${escapeHtml(tag.name)}')">
                    <input type="checkbox" id="tag-${escapeHtml(tag.name)}" ${selectedTags.includes(tag.name) ? 'checked' : ''}>
                    <label for="tag-${escapeHtml(tag.name)}">${escapeHtml(tag.name)}</label>
                    <span class="filter-count">${tag.count}</span>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

async function loadFeaturedReports() {
    try {
        const featured = await fetchAPI('/featured?limit=3');
        
        const container = document.getElementById('featuredGrid');
        if (!container) return;
        
        if (featured.length === 0) {
            document.getElementById('featuredSection').style.display = 'none';
            return;
        }
        
        container.innerHTML = featured.map(report => renderFeaturedCard(report)).join('');
    } catch (error) {
        console.error('Error loading featured reports:', error);
    }
}

async function loadReports() {
    try {
        // Build query params
        const params = new URLSearchParams({
            page: currentPage,
            page_size: PAGE_SIZE,
            sort: currentSort
        });
        
        if (currentCategory && currentCategory !== 'all') {
            params.append('category', currentCategory);
        }
        
        if (currentSearch) {
            params.append('search', currentSearch);
        }
        
        if (selectedOrgs.length === 1) {
            params.append('organization', selectedOrgs[0]);
        }
        
        if (selectedTags.length > 0) {
            params.append('tags', selectedTags.join(','));
        }
        
        if (dateFrom) {
            params.append('date_from', dateFrom);
        }
        
        if (dateTo) {
            params.append('date_to', dateTo);
        }
        
        const data = await fetchAPI(`?${params.toString()}`);
        
        // Update counts
        document.getElementById('showingCount').textContent = data.reports.length;
        document.getElementById('totalCount').textContent = data.total;
        
        // Render reports
        const container = document.getElementById('reportGrid');
        const emptyState = document.getElementById('emptyState');
        
        if (data.reports.length === 0) {
            container.innerHTML = '';
            emptyState.style.display = 'block';
        } else {
            emptyState.style.display = 'none';
            container.innerHTML = data.reports.map(report => renderReportCard(report)).join('');
        }
        
        // Render pagination
        renderPagination(data.page, data.total_pages);
        
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

async function loadReportDetail(reportId) {
    try {
        const report = await fetchAPI(`/${reportId}`);
        
        // Update page content
        document.getElementById('detailTitle').textContent = report.title;
        document.getElementById('detailOrg').textContent = report.organization;
        document.getElementById('detailDate').textContent = formatDate(report.published_date);
        document.getElementById('detailTags').textContent = report.tags.join(', ');
        document.getElementById('detailSummary').textContent = report.summary || 'No summary available.';
        
        // Update category badge
        const categoryEl = document.getElementById('detailCategory');
        categoryEl.textContent = formatCategory(report.category);
        categoryEl.className = `report-card-category ${report.category}`;
        
        // Update sidebar info
        document.getElementById('infoCategory').textContent = formatCategory(report.category);
        document.getElementById('infoOrg').textContent = report.organization;
        document.getElementById('infoDate').textContent = formatDate(report.published_date);
        document.getElementById('infoId').textContent = report.id;
        
        // Update bookmark button
        updateBookmarkButton(report.id, report.is_bookmarked || bookmarkedIds.has(report.id));
        
        // Update download button
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn && report.pdf_url) {
            downloadBtn.onclick = () => window.open(report.pdf_url, '_blank');
        }
        
        // Generate insights
        generateInsights(report);
        
        // Load related reports
        loadRelatedReports(reportId);
        
    } catch (error) {
        console.error('Error loading report detail:', error);
        document.getElementById('detailTitle').textContent = 'Report not found';
        document.getElementById('detailSummary').textContent = 'The requested report could not be found.';
    }
}

async function loadRelatedReports(reportId) {
    try {
        const related = await fetchAPI(`/${reportId}/related?limit=4`);
        
        const container = document.getElementById('relatedGrid');
        if (!container) return;
        
        if (related.length === 0) {
            container.innerHTML = '<p style="color: var(--text-sub);">No related reports found.</p>';
            return;
        }
        
        container.innerHTML = related.map(report => renderReportCard(report)).join('');
    } catch (error) {
        console.error('Error loading related reports:', error);
    }
}

// ============================================
// Rendering Functions
// ============================================

function renderFeaturedCard(report) {
    const isBookmarked = bookmarkedIds.has(report.id);
    
    return `
        <div class="featured-card" onclick="viewReport('${report.id}')">
            <div class="featured-card-image">
                <div class="featured-badge">Featured</div>
            </div>
            <div class="featured-card-content">
                <div class="featured-card-org">${escapeHtml(report.organization)}</div>
                <div class="featured-card-title">${escapeHtml(report.title)}</div>
                <div class="featured-card-meta">
                    <span><i class="fas fa-calendar"></i> ${formatDate(report.published_date)}</span>
                    <span><i class="fas fa-tag"></i> ${report.tags.slice(0, 2).join(', ')}</span>
                </div>
            </div>
        </div>
    `;
}

function renderReportCard(report) {
    const isBookmarked = bookmarkedIds.has(report.id);
    
    return `
        <div class="report-card" onclick="viewReport('${report.id}')">
            <div class="report-card-header ${report.category}">
                <i class="fas ${getCategoryIcon(report.category)} report-card-icon"></i>
                <div class="report-card-actions">
                    <button class="action-btn ${isBookmarked ? 'bookmarked' : ''}" 
                            onclick="event.stopPropagation(); toggleBookmark('${report.id}')"
                            title="${isBookmarked ? 'Remove Bookmark' : 'Add Bookmark'}">
                        <i class="${isBookmarked ? 'fas' : 'far'} fa-bookmark"></i>
                    </button>
                    <button class="action-btn" onclick="event.stopPropagation(); downloadReportPDF('${report.id}', '${report.pdf_url || ''}')" title="Download PDF">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
            <div class="report-card-body">
                <span class="report-card-category ${report.category}">${formatCategory(report.category)}</span>
                <div class="report-card-org">${escapeHtml(report.organization)}</div>
                <div class="report-card-title">${escapeHtml(report.title)}</div>
                <div class="report-card-summary">${escapeHtml(report.summary || '')}</div>
                <div class="report-card-footer">
                    <span class="report-card-date">
                        <i class="fas fa-calendar"></i>
                        ${formatDate(report.published_date)}
                    </span>
                    <div class="report-card-tags">
                        ${report.tags.slice(0, 2).map(tag => `<span class="report-tag">#${escapeHtml(tag)}</span>`).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderPagination(currentPage, totalPages) {
    const container = document.getElementById('pagination');
    if (!container || totalPages <= 1) {
        if (container) container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `<button class="pagination-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
        <i class="fas fa-chevron-left"></i>
    </button>`;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<button class="pagination-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) {
            html += `<span style="color: var(--text-sub);">...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<span style="color: var(--text-sub);">...</span>`;
        }
        html += `<button class="pagination-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }
    
    // Next button
    html += `<button class="pagination-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
        <i class="fas fa-chevron-right"></i>
    </button>`;
    
    container.innerHTML = html;
}

function generateInsights(report) {
    const insightsContainer = document.getElementById('detailInsights');
    if (!insightsContainer) return;
    
    // Generate insights based on tags and category
    const insights = [
        `This report provides comprehensive analysis on ${report.tags.slice(0, 2).join(' and ')}`,
        `Published by ${report.organization}, a leading institution in the ${formatCategory(report.category).toLowerCase()} sector`,
        `Key focus areas include industry trends, market analysis, and strategic recommendations`,
        `Relevant for professionals in logistics, supply chain, and international trade`
    ];
    
    insightsContainer.innerHTML = `
        <ul style="color: var(--text-sub); line-height: 2; padding-left: 1.5rem;">
            ${insights.map(i => `<li>${i}</li>`).join('')}
        </ul>
    `;
}

// ============================================
// Filter Functions
// ============================================

function filterByCategory(category) {
    currentCategory = category;
    currentPage = 1;
    
    // Update tab UI
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.category === category);
    });
    
    loadReports();
}

function searchReports() {
    const searchInput = document.getElementById('searchInput');
    currentSearch = searchInput ? searchInput.value.trim() : '';
    currentPage = 1;
    loadReports();
}

function sortReports() {
    const sortSelect = document.getElementById('sortSelect');
    currentSort = sortSelect ? sortSelect.value : 'newest';
    loadReports();
}

function toggleOrgFilter(org) {
    const index = selectedOrgs.indexOf(org);
    if (index === -1) {
        selectedOrgs.push(org);
    } else {
        selectedOrgs.splice(index, 1);
    }
    currentPage = 1;
    loadReports();
    loadFilters(); // Refresh filter UI
}

function toggleTagFilter(tag) {
    const index = selectedTags.indexOf(tag);
    if (index === -1) {
        selectedTags.push(tag);
    } else {
        selectedTags.splice(index, 1);
    }
    currentPage = 1;
    loadReports();
    loadFilters(); // Refresh filter UI
}

function clearFilters() {
    selectedOrgs = [];
    selectedTags = [];
    dateFrom = '';
    dateTo = '';
    currentSearch = '';
    currentCategory = 'all';
    currentPage = 1;
    
    // Reset UI
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';
    
    const dateFromInput = document.getElementById('dateFrom');
    if (dateFromInput) dateFromInput.value = '';
    
    const dateToInput = document.getElementById('dateTo');
    if (dateToInput) dateToInput.value = '';
    
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.category === 'all');
    });
    
    loadFilters();
    loadReports();
    
    showToast('Filters cleared', 'success');
}

function goToPage(page) {
    currentPage = page;
    loadReports();
    
    // Scroll to top of report section
    document.querySelector('.report-content')?.scrollIntoView({ behavior: 'smooth' });
}

// ============================================
// Bookmark Functions
// ============================================

function loadBookmarks() {
    try {
        const saved = localStorage.getItem('reportBookmarks');
        if (saved) {
            bookmarkedIds = new Set(JSON.parse(saved));
        }
    } catch (error) {
        console.error('Error loading bookmarks:', error);
        bookmarkedIds = new Set();
    }
}

function saveBookmarks() {
    try {
        localStorage.setItem('reportBookmarks', JSON.stringify([...bookmarkedIds]));
    } catch (error) {
        console.error('Error saving bookmarks:', error);
    }
}

async function toggleBookmark(reportId) {
    const isCurrentlyBookmarked = bookmarkedIds.has(reportId);
    
    try {
        if (isCurrentlyBookmarked) {
            await fetchAPI(`/bookmarks/${reportId}`, { method: 'DELETE' });
            bookmarkedIds.delete(reportId);
            showToast('Bookmark removed', 'success');
        } else {
            await fetchAPI('/bookmarks', {
                method: 'POST',
                body: JSON.stringify({ report_id: reportId })
            });
            bookmarkedIds.add(reportId);
            showToast('Bookmark added', 'success');
        }
        
        saveBookmarks();
        
        // Refresh the display
        loadReports();
        loadFeaturedReports();
        
    } catch (error) {
        console.error('Error toggling bookmark:', error);
        // Still update local state even if API fails
        if (isCurrentlyBookmarked) {
            bookmarkedIds.delete(reportId);
        } else {
            bookmarkedIds.add(reportId);
        }
        saveBookmarks();
        loadReports();
    }
}

function toggleBookmarkDetail() {
    const urlParams = new URLSearchParams(window.location.search);
    const reportId = urlParams.get('id');
    if (reportId) {
        toggleBookmark(reportId);
        updateBookmarkButton(reportId, !bookmarkedIds.has(reportId));
    }
}

function updateBookmarkButton(reportId, isBookmarked) {
    const btn = document.getElementById('bookmarkBtn');
    if (!btn) return;
    
    if (isBookmarked) {
        btn.classList.add('bookmarked');
        btn.innerHTML = '<i class="fas fa-bookmark"></i> Bookmarked';
    } else {
        btn.classList.remove('bookmarked');
        btn.innerHTML = '<i class="far fa-bookmark"></i> Add to Bookmarks';
    }
}

// ============================================
// Action Functions
// ============================================

function viewReport(reportId) {
    window.location.href = `report-detail.html?id=${reportId}`;
}

function downloadReportPDF(reportId, pdfUrl) {
    if (pdfUrl) {
        window.open(pdfUrl, '_blank');
    } else {
        showToast('PDF not available for this report', 'error');
    }
}

function downloadReport() {
    const urlParams = new URLSearchParams(window.location.search);
    const reportId = urlParams.get('id');
    
    // In a real implementation, this would fetch the PDF URL from the API
    showToast('Download started...', 'success');
}

function shareReport(platform) {
    const url = window.location.href;
    const title = document.getElementById('detailTitle')?.textContent || 'Report';
    
    let shareUrl = '';
    
    switch (platform) {
        case 'linkedin':
            shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
            break;
        case 'twitter':
            shareUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`;
            break;
        case 'email':
            shareUrl = `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(url)}`;
            break;
    }
    
    if (shareUrl) {
        window.open(shareUrl, '_blank');
    }
}

function copyLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        showToast('Link copied to clipboard', 'success');
    }).catch(() => {
        showToast('Failed to copy link', 'error');
    });
}

// ============================================
// Utility Functions
// ============================================

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatCategory(category) {
    const categories = {
        'global_research': 'Global Research',
        'government': 'Government',
        'company': 'Company'
    };
    return categories[category] || category;
}

function getCategoryIcon(category) {
    const icons = {
        'global_research': 'fa-microscope',
        'government': 'fa-landmark',
        'company': 'fa-building'
    };
    return icons[category] || 'fa-file-alt';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    if (!toast || !toastMessage) return;
    
    toast.className = `toast ${type}`;
    toastMessage.textContent = message;
    
    const icon = toast.querySelector('i');
    if (icon) {
        icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    }
    
    toast.style.display = 'flex';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}
