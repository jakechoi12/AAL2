/**
 * AAL Application - Global Constants and Configuration
 * 이 파일은 전역 상수와 설정을 정의합니다.
 */

// API Configuration
const API_BASE = 'http://localhost:5000/api';

// Currency Mapping for Exchange Rate API
const CURRENCY_MAPPING = {
    'USD': 'USD',
    'EUR': 'EUR',
    'JPY': 'JPY',
    'CNY': 'CNY',
    'GBP': 'GBP',
    'CHF': 'CHF',
    'HKD': 'HKD',
    'CAD': 'CAD',
    'RUB': 'RUB'
};

// Global Application State
const AppState = {
    exchangeRates: {},
    activeCurrencies: ['USD'],
    chartData: {},
    previousRates: {},
    chartInteractivitySetup: false,
    yAxisRange: { min: 0, max: 0 }
};

// Backwards compatibility - expose to window object
window.API_BASE = API_BASE;
window.AppState = AppState;

// Expose individual state variables for backwards compatibility
let exchangeRates = AppState.exchangeRates;
let activeCurrencies = AppState.activeCurrencies;
let chartData = AppState.chartData;
let previousRates = AppState.previousRates;
let chartInteractivitySetup = AppState.chartInteractivitySetup;
let yAxisRange = AppState.yAxisRange;

// Also expose to window for external access
window.exchangeRates = exchangeRates;
window.activeCurrencies = activeCurrencies;
window.chartData = chartData;
window.previousRates = previousRates;
window.CURRENCY_MAPPING = CURRENCY_MAPPING;

console.log('✅ AAL Config loaded: API_BASE =', API_BASE);

