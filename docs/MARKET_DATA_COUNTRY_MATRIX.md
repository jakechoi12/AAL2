# Market Data - Complete Country/Currency Matrix

## 📊 Summary

| Indicator | Stat Code | Periods | Items | Unit |
|-----------|-----------|---------|-------|------|
| Exchange Rate (KRW) | 731Y001 | D | 53 | KRW |
| Exchange Rate (USD) | 731Y002 | D | 51 | Currency/USD |
| Interest Rates | 902Y006 | M | 26 | % |
| Inflation (CPI) | 902Y008 | A, M, Q | 41 | 2010=100 |
| GDP | 902Y016 | A | 40 | M USD |
| GDP per Capita | 902Y018 | A | 41 | USD |
| GNI | 902Y017 | A | 36 | M USD |
| Export | 902Y012 | A, M, Q | 41 | M USD |
| Import | 902Y013 | A, M, Q | 41 | M USD |
| Economy Growth Rate | 902Y015 | A, Q | 38 | % |
| Unemployment | 902Y021 | A, M, Q | 34 | % |
| Global Stocks | 902Y002 | A, M, Q | 22 | 2015=100 |

---

## 📋 Period Availability

| Indicator | D | M | Q | A |
|-----------|:-:|:-:|:-:|:-:|
| Exchange Rate (KRW) | ✅ | - | - | - |
| Exchange Rate (USD) | ✅ | - | - | - |
| Interest Rates | - | ✅ | - | - |
| Inflation (CPI) | - | ✅ | ✅ | ✅ |
| GDP | - | - | - | ✅ |
| GDP per Capita | - | - | - | ✅ |
| GNI | - | - | - | ✅ |
| Export | - | ✅ | ✅ | ✅ |
| Import | - | ✅ | ✅ | ✅ |
| Economy Growth Rate | - | - | ✅ | ✅ |
| Unemployment | - | ✅ | ✅ | ✅ |
| Global Stocks | - | ✅ | ✅ | ✅ |

**Legend**: D = Daily, M = Monthly, Q = Quarterly, A = Annual

---

## 🛠️ Implementation Requirements

### 1. Exchange Rate (KRW) - 731Y001
- **Tab**: Separate tab for KRW exchange rates
- **Period**: Daily only
- **Features**:
  - Currency selection chips
  - Line chart with multiple currencies
  - Crosshair on hover (dotted lines for X/Y coordinates)

### 2. Exchange Rate (USD) - 731Y002
- **Tab**: Separate tab for USD exchange rates
- **Period**: Daily only
- **Features**:
  - Currency selection chips
  - Line chart with multiple currencies
  - Crosshair on hover (dotted lines for X/Y coordinates)

### 3. Interest Rates - 902Y006
- **Period Selector**: Monthly only (display as "Monthly")
- **Country Names**: Display in **English**
- **Features**:
  - Country selection chips with colors
  - Multi-line chart for country comparison
  - Crosshair on hover

### 4. Consumer Price Index (CPI/Inflation) - 902Y008
- **Period Selector Labels**: 
  - `Monthly` (not 월별)
  - `Quarterly` (not 분기별)
  - `Annually` (not 연별)
- **Country Names**: Display in **English**
- **Bug Fix**: Index values not showing - MUST FIX
- **Features**:
  - Country selection chips
  - Period toggle buttons (M/Q/A)
  - Crosshair on hover

### 5. GDP - 902Y016
- **Period**: Annual only
- **Country Names**: Display in **English** (not Korean)
- **Features**:
  - Country selection chips
  - Multi-line chart for country comparison
  - Crosshair on hover

### 6. GDP per Capita - 902Y018
- **Period**: Annual only
- **Country Names**: Display in **English** (not Korean)
- **Features**:
  - Country selection chips
  - Multi-line chart for country comparison
  - Crosshair on hover

### 7. GNI - 902Y017
- **Period**: Annual only
- **Country Names**: Display in **English** (not Korean)
- **Features**:
  - Country selection chips
  - Multi-line chart for country comparison
  - Crosshair on hover

### 8. Export x Import - 902Y012 / 902Y013
- **Period Selector Labels**:
  - `Monthly` (not 월별)
  - `Quarterly` (not 분기별)
  - `Annually` (not 연별)
- **Country Names**: Display in **English**
- **Indicator Toggles**:
  - **Export**: Blue color (`#2196F3` or `var(--c-trade-export)`)
  - **Import**: Red color (`#F44336` or `var(--c-trade-import)`)
  - **Trade Balance**: Green color (`#4CAF50` or `var(--c-trade-balance)`)
- **Trade Balance Calculation**: `Export - Import`
- **Button Styling**: Active buttons must show their respective colors
- **Chart**:
  - Export: Solid blue line
  - Import: Solid red line (or dashed)
  - Trade Balance: Solid green line
- **Features**:
  - Crosshair on hover

### 9. Economy Growth Rate - 902Y015
- **Period Selector Labels**:
  - `Quarterly`
  - `Annually`
- **Country Names**: Display in **English** (not Korean)
- **Features**:
  - Country selection chips
  - Period toggle (Q/A)
  - Multi-line chart
  - Crosshair on hover

### 10. Unemployment - 902Y021
- **Period Selector Labels**:
  - `Monthly`
  - `Quarterly`
  - `Annually`
- **Country Names**: Display in **English** (not Korean)
- **Features**:
  - Country selection chips
  - Period toggle (M/Q/A)
  - Multi-line chart
  - Crosshair on hover

### 11. Global Stocks - 902Y002
- **Period Selector Labels**:
  - `Monthly`
  - `Quarterly`
  - `Annually`
- **Country Names**: Display in **English** (not Korean)
- **Features**:
  - Country selection chips
  - Period toggle (M/Q/A)
  - Multi-line chart
  - Crosshair on hover

---

## 📐 Chart Interaction Requirements

### Crosshair on Hover (All Charts)
When user hovers over any chart:
1. **Vertical Line**: Dotted line from top to bottom at mouse X position
2. **Horizontal Line**: Dotted line from left to right at mouse Y position
3. **Intersection Point**: Show data point marker
4. **Tooltip**: Display values at intersection

```css
/* Crosshair styling */
.chart-crosshair-line {
    stroke: rgba(255, 255, 255, 0.5);
    stroke-width: 1;
    stroke-dasharray: 4, 4;
    pointer-events: none;
}
```

---

## 🌍 Complete Country/Currency Matrix

| Code | English Name | Korean Name | ExKRW | ExUSD | Interest | CPI | GDP | GDP/Cap | GNI | Export | Import | Growth | Unemp | Stocks |
|------|--------------|-------------|:-----:|:-----:|:--------:|:---:|:---:|:-------:|:---:|:------:|:------:|:------:|:-----:|:------:|
| KR | Korea | 한국 | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| US | United States | 미국 | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| JP | Japan | 일본 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CN | China | 중국 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ |
| DE | Germany | 독일 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| GB | United Kingdom | 영국 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| FR | France | 프랑스 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| IT | Italy | 이탈리아 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CA | Canada | 캐나다 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| AU | Australia | 호주 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| BR | Brazil | 브라질 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | - | - | ✅ |
| IN | India | 인도 | ✅ | ✅ | ✅ | ✅ | - | ✅ | - | ✅ | ✅ | - | - | ✅ |
| RU | Russia | 러시아 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ |
| MX | Mexico | 멕시코 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ID | Indonesia | 인도네시아 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅ | - | ✅ |
| TR | Turkey | 튀르키예 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CH | Switzerland | 스위스 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SE | Sweden | 스웨덴 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| NO | Norway | 노르웨이 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ZA | South Africa | 남아프리카공화국 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | - | - | ✅ |
| DK | Denmark | 덴마크 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| NZ | New Zealand | 뉴질랜드 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| AT | Austria | 오스트리아 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| BE | Belgium | 벨기에 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| CL | Chile | 칠레 | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| CZ | Czech Republic | 체코 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| EE | Estonia | 에스토니아 | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| FI | Finland | 핀란드 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| GR | Greece | 그리스 | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| HU | Hungary | 헝가리 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| IS | Iceland | 아이슬란드 | - | - | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | - |
| IE | Ireland | 아일랜드 | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| IL | Israel | 이스라엘 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| LV | Latvia | 라트비아 | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - |
| LU | Luxembourg | 룩셈부르크 | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| NL | Netherlands | 네덜란드 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| PL | Poland | 폴란드 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| PT | Portugal | 포르투갈 | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| SK | Slovakia | 슬로바키아 | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| SI | Slovenia | 슬로베니아 | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| ES | Spain | 스페인 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| EU | Eurozone | 유로 지역 | ✅ | ✅ | ✅ | - | - | - | - | - | - | - | - | - |
| HK | Hong Kong | 홍콩 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| TW | Taiwan | 대만 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| SG | Singapore | 싱가포르 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| TH | Thailand | 태국 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| MY | Malaysia | 말레이시아 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| PH | Philippines | 필리핀 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| VN | Vietnam | 베트남 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| PK | Pakistan | 파키스탄 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| BD | Bangladesh | 방글라데시 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| MN | Mongolia | 몽골 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| KZ | Kazakhstan | 카자흐스탄 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| AR | Argentina | 아르헨티나 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| SA | Saudi Arabia | 사우디아라비아 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| QA | Qatar | 카타르 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| JO | Jordan | 요르단 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| KW | Kuwait | 쿠웨이트 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| BH | Bahrain | 바레인 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| AE | UAE | 아랍에미리트 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| EG | Egypt | 이집트 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| BN | Brunei | 브루나이 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |

---

## 📌 Column Legend

| Column | Description |
|--------|-------------|
| **ExKRW** | Exchange Rate vs KRW (731Y001) |
| **ExUSD** | Exchange Rate vs USD (731Y002) |
| **Interest** | Interest Rates (902Y006) |
| **CPI** | Inflation/CPI (902Y008) |
| **GDP** | GDP (902Y016) |
| **GDP/Cap** | GDP per Capita (902Y018) |
| **GNI** | GNI (902Y017) |
| **Export** | Export (902Y012) |
| **Import** | Import (902Y013) |
| **Growth** | Economy Growth Rate (902Y015) |
| **Unemp** | Unemployment Rate (902Y021) |
| **Stocks** | Global Stocks Index (902Y002) |

---

## 🎨 Color Scheme

### Trade Indicators
| Indicator | Color | CSS Variable |
|-----------|-------|--------------|
| Export | Blue | `--c-trade-export: #2196F3` |
| Import | Red | `--c-trade-import: #F44336` |
| Trade Balance | Green | `--c-trade-balance: #4CAF50` |

### Period Button Labels (English)
| Korean | English |
|--------|---------|
| 월별 | Monthly |
| 분기별 | Quarterly |
| 연별 | Annually |

---

## 📊 Statistics

| Metric | Count |
|--------|-------|
| **Total Unique Countries/Currencies** | 61 |
| **Countries with Full Coverage (10+ indicators)** | 22 |
| **Countries with Exchange Rate Only** | 20 |
| **Max Indicators per Country** | 12 (Korea, Japan, etc.) |

---

## ✅ Implementation Checklist

- [ ] Exchange Rate (KRW) - Separate tab with graph
- [ ] Exchange Rate (USD) - Separate tab with graph
- [ ] Interest Rates - English period labels
- [ ] CPI/Inflation - Fix index display, English labels
- [ ] GDP - English country names
- [ ] GDP per Capita - English country names
- [ ] GNI - English country names
- [ ] Export x Import - Trade Balance calculation, colors, English labels
- [ ] Economy Growth Rate - English country names, Q/A selector
- [ ] Unemployment - English country names, M/Q/A selector
- [ ] Global Stocks - English country names, M/Q/A selector
- [ ] All Charts - Crosshair on hover (dotted X/Y lines)

---

*Last Updated: January 2026*
