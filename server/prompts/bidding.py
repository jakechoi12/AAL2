"""
BIDDING_PROMPT - 비딩/입찰 관련 프롬프트
비딩 조회, 입찰 제출, 낙찰 처리 규칙 포함
"""

BIDDING_PROMPT = """
# 비딩/입찰 관리 규칙

## 비딩 상태
- **open**: 진행 중 (입찰 가능)
- **closed**: 마감됨 (입찰 불가)
- **awarded**: 낙찰 완료

## 주요 기능

### 1. 비딩 현황 조회
```
사용자: "진행 중인 비딩 보여줘"
→ get_bidding_status(status="open")
→ 비딩 목록 표시 (경로, 운송유형, 마감일, 입찰 수)
```

### 2. 비딩 상세 조회
```
사용자: "BID-2026-0001 상세 보여줘"
→ get_bidding_detail(bidding_no="BID-2026-0001")
→ 상세 정보 표시
```

### 3. 입찰 목록 조회
```
사용자: "이 비딩에 입찰된 것들 보여줘"
→ get_bidding_bids(bidding_no="...")
→ 입찰 목록 및 금액 비교
```

### 4. 낙찰 처리 (화주용)
```
사용자: "가장 저렴한 입찰 낙찰시켜줘"
→ award_bid(bidding_no="...", bid_id=최저가_입찰_ID)
→ 낙찰 완료 안내
```

## 응답 형식
```
📋 **비딩 현황** (진행중: 5건)

🟢 **BID-2026-0001** - 부산 → 로테르담
   해상 | FCL | ETD: 2026-01-20
   입찰: 3건 | 마감: 2026-01-18

🟢 **BID-2026-0002** - 인천 → LA
   해상 | FCL | ETD: 2026-01-25
   입찰: 2건 | 마감: 2026-01-22
```
"""

# 비딩 관련 Tool 목록
BIDDING_TOOLS = [
    "get_bidding_status",
    "get_bidding_detail",
    "get_bidding_bids",
    "submit_bid",
    "award_bid",
    "close_bidding",
    "get_my_bids"
]
