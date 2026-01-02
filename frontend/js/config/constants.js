/**
 * AAL Application - Global Constants and Configuration
 * 이 파일은 전역 상수와 설정을 정의합니다.
 */

// API Configuration
const API_BASE = 'http://localhost:5000/api';

// Currency Mapping for Exchange Rate API (KRW base - 731Y001)
const CURRENCY_MAPPING = {
    // Major Currencies
    'USD': 'USD',   // United States
    'EUR': 'EUR',   // Eurozone
    'JPY': 'JPY',   // Japan
    'CNY': 'CNY',   // China
    'GBP': 'GBP',   // United Kingdom
    'CHF': 'CHF',   // Switzerland
    'CAD': 'CAD',   // Canada
    'AUD': 'AUD',   // Australia
    // Asia Pacific
    'HKD': 'HKD',   // Hong Kong
    'TWD': 'TWD',   // Taiwan
    'SGD': 'SGD',   // Singapore
    'THB': 'THB',   // Thailand
    'MYR': 'MYR',   // Malaysia
    'IDR': 'IDR',   // Indonesia
    'PHP': 'PHP',   // Philippines
    'VND': 'VND',   // Vietnam
    'INR': 'INR',   // India
    'PKR': 'PKR',   // Pakistan
    'BDT': 'BDT',   // Bangladesh
    'NZD': 'NZD',   // New Zealand
    'MNT': 'MNT',   // Mongolia
    'KZT': 'KZT',   // Kazakhstan
    'BND': 'BND',   // Brunei
    // Europe
    'SEK': 'SEK',   // Sweden
    'DKK': 'DKK',   // Denmark
    'NOK': 'NOK',   // Norway
    'RUB': 'RUB',   // Russia
    'HUF': 'HUF',   // Hungary
    'PLN': 'PLN',   // Poland
    'CZK': 'CZK',   // Czech Republic
    // Americas
    'MXN': 'MXN',   // Mexico
    'BRL': 'BRL',   // Brazil
    'ARS': 'ARS',   // Argentina
    // Middle East
    'SAR': 'SAR',   // Saudi Arabia
    'AED': 'AED',   // UAE
    'QAR': 'QAR',   // Qatar
    'KWD': 'KWD',   // Kuwait
    'BHD': 'BHD',   // Bahrain
    'JOD': 'JOD',   // Jordan
    'ILS': 'ILS',   // Israel
    'TRY': 'TRY',   // Turkey
    // Africa
    'ZAR': 'ZAR',   // South Africa
    'EGP': 'EGP'    // Egypt
};

// Currency Mapping for USD-based Exchange Rate API (731Y002)
const USD_CURRENCY_MAPPING = {
    // Major currencies
    'JPY': 'JPY',   // Japan
    'EUR': 'EUR',   // Europe
    'GBP': 'GBP',   // United Kingdom
    'CAD': 'CAD',   // Canada
    'CHF': 'CHF',   // Switzerland
    'AUD': 'AUD',   // Australia
    'NZD': 'NZD',   // New Zealand
    // Asia
    'HKD': 'HKD',   // Hong Kong
    'SGD': 'SGD',   // Singapore
    'TWD': 'TWD',   // Taiwan
    'THB': 'THB',   // Thailand
    'MYR': 'MYR',   // Malaysia
    'PHP': 'PHP',   // Philippines
    'IDR': 'IDR',   // Indonesia
    'VND': 'VND',   // Vietnam
    'INR': 'INR',   // India
    'PKR': 'PKR',   // Pakistan
    'BDT': 'BDT',   // Bangladesh
    'MNT': 'MNT',   // Mongolia
    'KZT': 'KZT',   // Kazakhstan
    // Europe (other)
    'SEK': 'SEK',   // Sweden
    'NOK': 'NOK',   // Norway
    'DKK': 'DKK',   // Denmark
    'RUB': 'RUB',   // Russia
    'HUF': 'HUF',   // Hungary
    'PLN': 'PLN',   // Poland
    'CZK': 'CZK',   // Czech Republic
    'TRY': 'TRY',   // Turkey
    // Americas
    'MXN': 'MXN',   // Mexico
    'BRL': 'BRL',   // Brazil
    'ARS': 'ARS',   // Argentina
    // Middle East
    'SAR': 'SAR',   // Saudi Arabia
    'QAR': 'QAR',   // Qatar
    'ILS': 'ILS',   // Israel
    'JOD': 'JOD',   // Jordan
    'KWD': 'KWD',   // Kuwait
    'BHD': 'BHD',   // Bahrain
    'AED': 'AED',   // UAE
    // Africa & Others
    'ZAR': 'ZAR',   // South Africa
    'BND': 'BND',   // Brunei
    'EGP': 'EGP'    // Egypt
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
window.USD_CURRENCY_MAPPING = USD_CURRENCY_MAPPING;

console.log('✅ AAL Config loaded: API_BASE =', API_BASE);

