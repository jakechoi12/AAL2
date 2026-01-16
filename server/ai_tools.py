"""
AI Assistant Tools - Database Integration
Gemini Function Calling을 위한 Tool 함수들

DB 위치:
- Quote DB: quote_backend/quote.db (운임, 비딩, POL/POD)
- Shipping Indices DB: server/shipping_indices.db (BDI, SCFI, CCFI)
- News Intelligence DB: server/news_intelligence.db (뉴스)
"""

import os
import sys
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 엔드포인트 설정
FLASK_API_BASE = "http://localhost:5000"
QUOTE_API_BASE = "http://localhost:8001"

# 경로 설정
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SERVER_DIR)
QUOTE_BACKEND_DIR = os.path.join(PROJECT_ROOT, 'quote_backend')

# SQLAlchemy 공통
from sqlalchemy import create_engine, desc, and_, or_, text
from sqlalchemy.orm import sessionmaker


# ============================================================
# DATABASE CONNECTIONS
# ============================================================

def get_quote_db_session():
    """Quote Backend DB 세션 반환 (quote_backend/quote.db)"""
    db_path = os.path.join(QUOTE_BACKEND_DIR, 'quote.db')
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    return Session()


def get_shipping_indices_db_session():
    """Shipping Indices DB 세션 반환 (server/shipping_indices.db)"""
    db_path = os.path.join(SERVER_DIR, 'shipping_indices.db')
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    return Session()


def get_news_db_session():
    """News Intelligence DB 세션 반환 (server/news_intelligence.db)"""
    db_path = os.path.join(SERVER_DIR, 'news_intelligence.db')
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    return Session()


# ============================================================
# TOOL DEFINITIONS (Gemini Function Calling용)
# ============================================================

TOOL_DEFINITIONS = [
    {
        "name": "get_ocean_rates",
        "description": "해상 운임을 조회합니다. 출발항(POL), 도착항(POD), 컨테이너 타입을 입력하면 실시간 운임 정보를 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "pol": {
                    "type": "string",
                    "description": "출발 항구 코드 (예: KRPUS=부산, KRINC=인천, CNSHA=상하이, USNYC=뉴욕)"
                },
                "pod": {
                    "type": "string",
                    "description": "도착 항구 코드 (예: NLRTM=로테르담, DEHAM=함부르크, USLAX=LA)"
                },
                "container_type": {
                    "type": "string",
                    "description": "컨테이너 타입 (20DC, 40DC, 40HC/4HDC). 기본값: 40HC"
                }
            },
            "required": ["pol", "pod"]
        }
    },
    {
        "name": "get_bidding_status",
        "description": "현재 진행 중인 비딩(입찰) 현황을 조회합니다. 상태별 필터링이 가능합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["open", "closed", "awarded", "all"],
                    "description": "비딩 상태 필터 (open=진행중, closed=마감, awarded=낙찰완료, all=전체)"
                },
                "limit": {
                    "type": "integer",
                    "description": "조회할 최대 건수 (기본값: 5)"
                }
            }
        }
    },
    {
        "name": "get_shipping_indices",
        "description": "해운 시장 지수(BDI, SCFI, CCFI)를 조회합니다. 최신 지수값과 변동률을 확인할 수 있습니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "index_type": {
                    "type": "string",
                    "enum": ["BDI", "SCFI", "CCFI", "all"],
                    "description": "조회할 지수 유형 (BDI=발틱운임지수, SCFI=상하이운임지수, CCFI=중국운임지수, all=전체)"
                },
                "days": {
                    "type": "integer",
                    "description": "조회할 기간(일수). 기본값: 7"
                }
            },
            "required": ["index_type"]
        }
    },
    {
        "name": "get_latest_news",
        "description": "최신 물류 뉴스를 조회합니다. 카테고리별, 위기 뉴스 필터링이 가능합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["Crisis", "Ocean", "Air", "Inland", "Economy", "ETC", "all"],
                    "description": "뉴스 카테고리 (Crisis=위기/사고, Ocean=해운, Air=항공, Inland=육상, Economy=경제, all=전체)"
                },
                "is_crisis": {
                    "type": "boolean",
                    "description": "위기/긴급 뉴스만 조회 여부"
                },
                "news_type": {
                    "type": "string",
                    "enum": ["KR", "GLOBAL", "all"],
                    "description": "뉴스 유형 (KR=국내, GLOBAL=해외, all=전체)"
                },
                "limit": {
                    "type": "integer",
                    "description": "조회할 최대 건수 (기본값: 5)"
                }
            }
        }
    },
    {
        "name": "get_port_info",
        "description": "POL/POD 항구 또는 공항 코드를 조회합니다. 운송 유형에 따라 반드시 port_type을 지정하세요! 해상운송은 ocean, 항공운송은 air로 조회해야 올바른 코드를 얻습니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "검색어 (도시명, 공항/항구명, 국가명). 예: 인천, 시칠리, 로마, 팔레르모"
                },
                "country_code": {
                    "type": "string",
                    "description": "국가 코드 필터 (예: KR=한국, IT=이탈리아, CN=중국, US=미국, DE=독일)"
                },
                "port_type": {
                    "type": "string",
                    "enum": ["ocean", "air", "both"],
                    "description": "⚠️ 중요! 운송유형에 맞게 선택. ocean=해상항구, air=항공공항. 항공운송이면 반드시 air 사용!"
                }
            }
        }
    },
    {
        "name": "create_quote_request",
        "description": "운송 견적 요청(Quote Request)을 생성합니다. 모든 필수 정보가 수집된 후에만 호출하세요. 성공 시 비딩이 자동 생성되고 포워더들에게 RFQ가 발송됩니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "trade_mode": {
                    "type": "string",
                    "enum": ["export", "import", "domestic"],
                    "description": "거래 유형 (export=수출, import=수입, domestic=국내)"
                },
                "shipping_type": {
                    "type": "string",
                    "enum": ["ocean", "air", "truck"],
                    "description": "운송 유형 (ocean=해상, air=항공, truck=육상)"
                },
                "load_type": {
                    "type": "string",
                    "enum": ["FCL", "LCL", "AIR", "FTL", "LTL"],
                    "description": "적재 유형 (FCL/LCL=해상, AIR=항공, FTL/LTL=육상)"
                },
                "pol": {
                    "type": "string",
                    "description": "출발지 코드 (get_port_info로 조회한 코드)"
                },
                "pod": {
                    "type": "string",
                    "description": "도착지 코드 (get_port_info로 조회한 코드)"
                },
                "etd": {
                    "type": "string",
                    "description": "출발 예정일 (YYYY-MM-DD 형식)"
                },
                "eta": {
                    "type": "string",
                    "description": "도착 예정일 (YYYY-MM-DD 형식). 필수!"
                },
                "container_type": {
                    "type": "string",
                    "description": "컨테이너 유형 (FCL: 20DC, 40DC, 40HC). 해상 FCL인 경우 필수"
                },
                "container_qty": {
                    "type": "integer",
                    "description": "컨테이너 수량. 기본값: 1"
                },
                "cargo_weight_kg": {
                    "type": "number",
                    "description": "화물 총중량 (kg)"
                },
                "cargo_cbm": {
                    "type": "number",
                    "description": "화물 부피 (CBM, m³)"
                },
                "incoterms": {
                    "type": "string",
                    "enum": ["EXW", "FOB", "CFR", "CIF", "DAP", "DDP"],
                    "description": "인코텀즈 조건"
                },
                "invoice_value_usd": {
                    "type": "number",
                    "description": "송장 가액 (USD). 기본값: 1000"
                },
                "is_dg": {
                    "type": "boolean",
                    "description": "위험물 여부"
                },
                "pickup_required": {
                    "type": "boolean",
                    "description": "픽업 필요 여부"
                },
                "pickup_address": {
                    "type": "string",
                    "description": "픽업 주소 (pickup_required=true인 경우)"
                },
                "delivery_required": {
                    "type": "boolean",
                    "description": "배송 필요 여부"
                },
                "delivery_address": {
                    "type": "string",
                    "description": "배송 주소 (delivery_required=true인 경우)"
                },
                "remark": {
                    "type": "string",
                    "description": "추가 요청사항 또는 비고"
                },
                "customer_company": {
                    "type": "string",
                    "description": "고객 회사명"
                },
                "customer_name": {
                    "type": "string",
                    "description": "담당자 이름"
                },
                "customer_email": {
                    "type": "string",
                    "description": "담당자 이메일"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "담당자 연락처"
                }
            },
            "required": ["trade_mode", "shipping_type", "load_type", "pol", "pod", "etd", "eta", "invoice_value_usd", "customer_company", "customer_name", "customer_email", "customer_phone"]
        }
    },
    # ════════════════════════════════════════════════════════════
    # NEW MCP TOOLS - Phase 1: 핵심 비즈니스 도구
    # ════════════════════════════════════════════════════════════
    {
        "name": "get_air_rates",
        "description": "항공 화물 운임을 조회합니다. 출발/도착 공항과 화물 중량을 입력하면 예상 운임을 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "pol": {
                    "type": "string",
                    "description": "출발 공항 코드 (예: ICN=인천, CTA=카타니아, LAX=LA)"
                },
                "pod": {
                    "type": "string",
                    "description": "도착 공항 코드"
                },
                "weight_kg": {
                    "type": "number",
                    "description": "화물 총중량 (kg)"
                },
                "chargeable_weight_kg": {
                    "type": "number",
                    "description": "Chargeable Weight (kg). 없으면 weight_kg 사용"
                }
            },
            "required": ["pol", "pod", "weight_kg"]
        }
    },
    {
        "name": "get_schedules",
        "description": "항공 또는 해상 운송 스케줄을 조회합니다. 출발지, 도착지, 운송유형, 날짜를 입력하면 가능한 스케줄 목록을 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "pol": {
                    "type": "string",
                    "description": "출발지 코드 (공항 또는 항구)"
                },
                "pod": {
                    "type": "string",
                    "description": "도착지 코드"
                },
                "shipping_type": {
                    "type": "string",
                    "enum": ["air", "ocean"],
                    "description": "운송 유형 (air=항공, ocean=해상)"
                },
                "etd": {
                    "type": "string",
                    "description": "출발 예정일 (YYYY-MM-DD). 이 날짜 이후 스케줄 조회"
                },
                "limit": {
                    "type": "integer",
                    "description": "조회할 최대 스케줄 수 (기본값: 5)"
                }
            },
            "required": ["pol", "pod", "shipping_type"]
        }
    },
    {
        "name": "get_quote_detail",
        "description": "견적 요청의 상세 정보를 조회합니다. 비딩 번호나 견적 ID로 상세 내용을 확인할 수 있습니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "quote_id": {
                    "type": "string",
                    "description": "견적 ID 또는 비딩 번호 (예: BID-2026-0001)"
                }
            },
            "required": ["quote_id"]
        }
    },
    # ════════════════════════════════════════════════════════════
    # NEW MCP TOOLS - Phase 2: 시장 정보 도구
    # ════════════════════════════════════════════════════════════
    {
        "name": "get_exchange_rates",
        "description": "실시간 환율 정보를 조회합니다. 물류 비용 계산에 필요한 환율을 확인할 수 있습니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "base_currency": {
                    "type": "string",
                    "description": "기준 통화 (기본값: USD)"
                },
                "target_currency": {
                    "type": "string",
                    "description": "목표 통화 (기본값: KRW). 여러 통화는 콤마로 구분 (예: KRW,CNY,EUR)"
                }
            }
        }
    },
    {
        "name": "get_global_alerts",
        "description": "GDELT 기반 글로벌 물류/공급망 경고를 조회합니다. 지역별, 카테고리별 위기 상황을 확인할 수 있습니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "지역 필터 (예: Asia, Europe, Americas, Middle East)"
                },
                "category": {
                    "type": "string",
                    "enum": ["conflict", "disaster", "economic", "political", "all"],
                    "description": "카테고리 (conflict=분쟁, disaster=재해, economic=경제, political=정치)"
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "all"],
                    "description": "심각도 필터"
                },
                "limit": {
                    "type": "integer",
                    "description": "조회할 최대 건수 (기본값: 10)"
                }
            }
        }
    },
    # ════════════════════════════════════════════════════════════
    # NEW MCP TOOLS - Phase 3: 시스템 제어 도구
    # ════════════════════════════════════════════════════════════
    {
        "name": "navigate_to_page",
        "description": "사용자를 플랫폼의 특정 페이지로 안내합니다. 견적 요청, 비딩 현황, 시장 지수 등의 페이지로 이동할 때 사용합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "string",
                    "enum": ["quotation", "bidding", "market-indices", "news", "dashboard", "reports"],
                    "description": "이동할 페이지 (quotation=견적요청, bidding=비딩현황, market-indices=시장지수, news=뉴스, dashboard=대시보드)"
                },
                "params": {
                    "type": "object",
                    "description": "페이지에 전달할 파라미터 (선택)"
                }
            },
            "required": ["page"]
        }
    },
    # ════════════════════════════════════════════════════════════
    # PHASE 0: 화주 견적 업무 완성
    # ════════════════════════════════════════════════════════════
    {
        "name": "get_my_quotes",
        "description": "화주의 견적 요청 목록을 조회합니다. 이메일로 고객을 식별하여 해당 고객의 모든 견적 요청을 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_email": {
                    "type": "string",
                    "description": "고객 이메일 주소"
                },
                "status": {
                    "type": "string",
                    "enum": ["all", "pending", "in_progress", "completed", "cancelled"],
                    "description": "견적 상태 필터 (기본값: all)"
                },
                "limit": {
                    "type": "integer",
                    "description": "조회할 최대 건수 (기본값: 10)"
                }
            },
            "required": ["customer_email"]
        }
    },
    {
        "name": "update_quote_request",
        "description": "기존 견적 요청을 수정합니다. 비딩이 진행 중(open)일 때만 수정 가능합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "bidding_no": {
                    "type": "string",
                    "description": "수정할 비딩 번호 (예: EXSEA00001)"
                },
                "etd": {
                    "type": "string",
                    "description": "변경할 출발 예정일 (YYYY-MM-DD)"
                },
                "eta": {
                    "type": "string",
                    "description": "변경할 도착 예정일 (YYYY-MM-DD)"
                },
                "incoterms": {
                    "type": "string",
                    "description": "변경할 인코텀즈"
                },
                "pickup_required": {
                    "type": "boolean",
                    "description": "픽업 필요 여부"
                },
                "pickup_address": {
                    "type": "string",
                    "description": "픽업 주소"
                },
                "delivery_required": {
                    "type": "boolean",
                    "description": "배송 필요 여부"
                },
                "delivery_address": {
                    "type": "string",
                    "description": "배송 주소"
                },
                "remark": {
                    "type": "string",
                    "description": "비고 사항"
                }
            },
            "required": ["bidding_no"]
        }
    },
    {
        "name": "cancel_quote_request",
        "description": "견적 요청을 취소합니다. 비딩이 진행 중(open)이고 입찰이 없을 때만 취소 가능합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "request_id": {
                    "type": "integer",
                    "description": "취소할 견적 요청 ID"
                }
            },
            "required": ["request_id"]
        }
    },
    # ════════════════════════════════════════════════════════════
    # PHASE 1: 비딩/입찰 도구
    # ════════════════════════════════════════════════════════════
    {
        "name": "submit_bid",
        "description": "포워더가 비딩에 운임 제안을 제출합니다. 비딩이 진행 중(open)일 때만 제출 가능합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "bidding_id": {
                    "type": "integer",
                    "description": "비딩 ID"
                },
                "forwarder_id": {
                    "type": "integer",
                    "description": "포워더 ID"
                },
                "total_amount": {
                    "type": "number",
                    "description": "총 운임 (USD)"
                },
                "freight_charge": {
                    "type": "number",
                    "description": "해상/항공 운임 (USD)"
                },
                "local_charge": {
                    "type": "number",
                    "description": "현지 비용 (USD)"
                },
                "other_charge": {
                    "type": "number",
                    "description": "기타 비용 (USD)"
                },
                "transit_time": {
                    "type": "string",
                    "description": "운송 소요 기간 (예: 14-18일)"
                },
                "validity_date": {
                    "type": "string",
                    "description": "견적 유효 기간 (YYYY-MM-DD)"
                },
                "remark": {
                    "type": "string",
                    "description": "비고 사항"
                }
            },
            "required": ["bidding_id", "forwarder_id", "total_amount"]
        }
    },
    {
        "name": "award_bid",
        "description": "화주가 특정 입찰을 낙찰 처리합니다. 비딩이 진행 중(open) 또는 마감(closed) 상태일 때 가능합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "bidding_no": {
                    "type": "string",
                    "description": "비딩 번호 (예: EXSEA00001)"
                },
                "bid_id": {
                    "type": "integer",
                    "description": "낙찰할 입찰 ID"
                }
            },
            "required": ["bidding_no", "bid_id"]
        }
    },
    {
        "name": "get_bidding_detail",
        "description": "비딩의 상세 정보를 조회합니다. 견적 요청 정보, 입찰 목록, 고객 정보 등을 포함합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "bidding_no": {
                    "type": "string",
                    "description": "비딩 번호 (예: EXSEA00001)"
                }
            },
            "required": ["bidding_no"]
        }
    },
    {
        "name": "get_bidding_bids",
        "description": "특정 비딩에 제출된 입찰 목록을 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "bidding_no": {
                    "type": "string",
                    "description": "비딩 번호 (예: EXSEA00001)"
                }
            },
            "required": ["bidding_no"]
        }
    },
    {
        "name": "close_bidding",
        "description": "비딩을 마감합니다. 더 이상 입찰을 받지 않습니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "bidding_no": {
                    "type": "string",
                    "description": "마감할 비딩 번호"
                }
            },
            "required": ["bidding_no"]
        }
    },
    {
        "name": "get_my_bids",
        "description": "포워더의 입찰 목록을 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "forwarder_id": {
                    "type": "integer",
                    "description": "포워더 ID"
                },
                "status": {
                    "type": "string",
                    "enum": ["all", "submitted", "awarded", "rejected"],
                    "description": "입찰 상태 필터"
                },
                "limit": {
                    "type": "integer",
                    "description": "조회할 최대 건수"
                }
            },
            "required": ["forwarder_id"]
        }
    },
    # ════════════════════════════════════════════════════════════
    # PHASE 2: 계약/배송 도구
    # ════════════════════════════════════════════════════════════
    {
        "name": "get_contracts",
        "description": "계약 목록을 조회합니다. 사용자 유형과 ID로 필터링합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_type": {
                    "type": "string",
                    "enum": ["shipper", "forwarder"],
                    "description": "사용자 유형"
                },
                "user_id": {
                    "type": "integer",
                    "description": "사용자 ID (customer_id 또는 forwarder_id)"
                },
                "status": {
                    "type": "string",
                    "enum": ["all", "pending", "confirmed", "in_progress", "completed", "cancelled"],
                    "description": "계약 상태 필터"
                },
                "limit": {
                    "type": "integer",
                    "description": "조회할 최대 건수"
                }
            },
            "required": ["user_type", "user_id"]
        }
    },
    {
        "name": "get_contract_detail",
        "description": "계약의 상세 정보를 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "integer",
                    "description": "계약 ID"
                }
            },
            "required": ["contract_id"]
        }
    },
    {
        "name": "track_shipment",
        "description": "배송 상태를 추적합니다. 배송 ID로 현재 위치와 이력을 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "shipment_id": {
                    "type": "integer",
                    "description": "배송 ID"
                }
            },
            "required": ["shipment_id"]
        }
    },
    {
        "name": "get_shipments",
        "description": "배송 목록을 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_type": {
                    "type": "string",
                    "enum": ["shipper", "forwarder"],
                    "description": "사용자 유형"
                },
                "user_id": {
                    "type": "integer",
                    "description": "사용자 ID"
                },
                "status": {
                    "type": "string",
                    "enum": ["all", "pending", "picked_up", "in_transit", "delivered"],
                    "description": "배송 상태 필터"
                },
                "limit": {
                    "type": "integer",
                    "description": "조회할 최대 건수"
                }
            },
            "required": ["user_type", "user_id"]
        }
    },
    # ════════════════════════════════════════════════════════════
    # PHASE 3: 분석/소통 도구
    # ════════════════════════════════════════════════════════════
    {
        "name": "get_shipper_analytics",
        "description": "화주의 분석 데이터를 조회합니다. 총 요청 건수, 평균 입찰 수, 낙찰률, 총 운송비 등의 KPI를 제공합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "고객(화주) ID"
                },
                "from_date": {
                    "type": "string",
                    "description": "조회 시작일 (YYYY-MM-DD)"
                },
                "to_date": {
                    "type": "string",
                    "description": "조회 종료일 (YYYY-MM-DD)"
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "get_notifications",
        "description": "사용자의 알림 목록을 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_type": {
                    "type": "string",
                    "enum": ["shipper", "forwarder"],
                    "description": "사용자 유형"
                },
                "user_id": {
                    "type": "integer",
                    "description": "사용자 ID"
                },
                "unread_only": {
                    "type": "boolean",
                    "description": "읽지 않은 알림만 조회"
                },
                "limit": {
                    "type": "integer",
                    "description": "조회할 최대 건수"
                }
            },
            "required": ["user_type", "user_id"]
        }
    },
    {
        "name": "send_message",
        "description": "비딩 관련 메시지를 발송합니다. 화주와 포워더 간 소통에 사용합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "bidding_id": {
                    "type": "integer",
                    "description": "비딩 ID"
                },
                "sender_type": {
                    "type": "string",
                    "enum": ["shipper", "forwarder"],
                    "description": "발신자 유형"
                },
                "sender_id": {
                    "type": "integer",
                    "description": "발신자 ID"
                },
                "message": {
                    "type": "string",
                    "description": "메시지 내용"
                }
            },
            "required": ["bidding_id", "sender_type", "sender_id", "message"]
        }
    }
]


# ============================================================
# TOOL 1: GET OCEAN RATES (해상 운임 조회)
# ============================================================

def get_ocean_rates(pol: str, pod: str, container_type: str = "4HDC") -> Dict[str, Any]:
    """
    해상 운임 조회 (Quote Backend API 연동으로 환율 일관성 보장)
    
    Args:
        pol: 출발항 코드 (예: KRPUS)
        pod: 도착항 코드 (예: NLRTM)
        container_type: 컨테이너 타입 (20DC, 40DC, 4HDC)
    
    Returns:
        운임 정보 딕셔너리
    """
    try:
        # 컨테이너 타입 표준화 (40HC -> 4HDC, 20FT -> 20DC)
        container_type = container_type.upper()
        if container_type == "40HC":
            container_type = "4HDC"
        elif container_type in ["20FT", "20'", "20"]:
            container_type = "20DC"
        elif container_type in ["40FT", "40'", "40"]:
            container_type = "40DC"
        
        # Quote Backend의 /api/freight/estimate API 호출 (환율 자동 적용)
        response = requests.get(
            f"{QUOTE_API_BASE}/api/freight/estimate",
            params={
                "pol": pol.upper(),
                "pod": pod.upper(),
                "container_type": container_type
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "message": f"운임 조회 실패: HTTP {response.status_code}",
                "suggestion": "올바른 항구 코드를 입력해주세요. (예: KRPUS=부산, NLRTM=로테르담)"
            }
        
        data = response.json()
        
        # Quick Quotation 불가능한 경우
        if not data.get("quick_quotation"):
            return {
                "success": False,
                "message": data.get("message", "해당 구간의 운임 정보가 없습니다."),
                "suggestion": data.get("guide", "견적 요청을 통해 포워더 비딩을 진행해 주세요.")
            }
        
        # 운임 상세 정리
        rate_groups = {}
        
        # Ocean Freight 항목
        ocean_freight = data.get("ocean_freight", {})
        if ocean_freight.get("items"):
            rate_groups["Ocean Freight"] = [
                {
                    "code": item["code"],
                    "name": item.get("name_ko") or item.get("name") or item["code"],
                    "rate": item["rate"],
                    "currency": item["currency"],
                    "unit": item["unit"]
                }
                for item in ocean_freight["items"] if item.get("rate")
            ]
        
        # Origin Local Charges 항목
        origin_local = data.get("origin_local", {})
        if origin_local.get("items"):
            rate_groups["Origin Local Charges"] = [
                {
                    "code": item["code"],
                    "name": item.get("name_ko") or item.get("name") or item["code"],
                    "rate": item["rate"],
                    "currency": item["currency"],
                    "unit": item["unit"]
                }
                for item in origin_local["items"] if item.get("rate")
            ]
        
        # 환율 정보 및 출처 확인
        exchange_rates = data.get("exchange_rates_used", {})
        total_krw_converted = data.get("total_krw_converted", 0)
        
        # 환율 출처 판별 (기본값인지 실시간인지)
        # 기본값: USD=1450, EUR=1550
        DEFAULT_RATES = {"USD": 1450.0, "EUR": 1550.0}
        is_default_rate = True
        for curr, rate in exchange_rates.items():
            if curr in DEFAULT_RATES and abs(rate - DEFAULT_RATES[curr]) > 0.01:
                is_default_rate = False
                break
        
        exchange_rate_source = "시스템 기본 환율" if is_default_rate else "한국은행 실시간"
        
        return {
            "success": True,
            "route": {
                "pol": pol.upper(),
                "pod": pod.upper()
            },
            "container": {
                "code": data.get("container_type"),
                "name": data.get("container_name")
            },
            "carrier": data.get("carrier"),
            "validity": {
                "from": data.get("valid_from"),
                "to": data.get("valid_to")
            },
            "rates": rate_groups,
            "total": {
                "usd": data.get("total_usd", 0),
                "krw": data.get("total_krw", 0),
                "eur": data.get("total_eur", 0),
                "total_krw_converted": round(total_krw_converted),
                "summary": f"₩{total_krw_converted:,.0f}"
            },
            "exchange_rates_used": exchange_rates,
            "exchange_rate_source": exchange_rate_source,
            "note": data.get("note", "")
        }
        
    except requests.exceptions.Timeout:
        logger.error("get_ocean_rates timeout")
        return {
            "success": False,
            "message": "운임 조회 시간 초과",
            "suggestion": "잠시 후 다시 시도해주세요."
        }
    except Exception as e:
        logger.error(f"get_ocean_rates error: {e}")
        return {
            "success": False,
            "message": f"운임 조회 중 오류가 발생했습니다: {str(e)}"
        }


# ============================================================
# TOOL 2: GET BIDDING STATUS (비딩 현황 조회)
# ============================================================

def get_bidding_status(status: str = "open", limit: int = 5) -> Dict[str, Any]:
    """
    비딩(입찰) 현황 조회
    
    Args:
        status: 비딩 상태 (open, closed, awarded, all)
        limit: 조회 건수
    
    Returns:
        비딩 현황 딕셔너리
    """
    session = None
    try:
        session = get_quote_db_session()
        
        # 상태별 필터 쿼리 구성
        status_filter = ""
        if status and status != "all":
            status_filter = f"AND b.status = '{status}'"
        
        # 비딩 목록 조회
        query = text(f"""
            SELECT 
                b.id,
                b.bidding_no,
                b.status,
                b.deadline,
                b.created_at,
                qr.pol,
                qr.pod,
                qr.shipping_type,
                qr.load_type,
                qr.etd,
                c.company as customer_company,
                (SELECT COUNT(*) FROM bids WHERE bidding_id = b.id AND status = 'submitted') as bid_count
            FROM biddings b
            JOIN quote_requests qr ON b.quote_request_id = qr.id
            JOIN customers c ON qr.customer_id = c.id
            WHERE 1=1 {status_filter}
            ORDER BY b.created_at DESC
            LIMIT {limit}
        """)
        
        results = session.execute(query).fetchall()
        
        if not results:
            status_text = {"open": "진행 중인", "closed": "마감된", "awarded": "낙찰 완료된", "all": ""}.get(status, "")
            return {
                "success": True,
                "message": f"{status_text} 비딩이 없습니다.",
                "biddings": [],
                "count": 0
            }
        
        # 결과 정리
        biddings = []
        for row in results:
            bid_id, bidding_no, bid_status, deadline, created_at, pol, pod, shipping_type, load_type, etd, customer, bid_count = row
            
            # 상태 한글화
            status_kr = {
                "open": "진행중",
                "closed": "마감",
                "awarded": "낙찰완료",
                "cancelled": "취소",
                "expired": "만료"
            }.get(bid_status, bid_status)
            
            # 운송유형 한글화
            shipping_kr = {
                "ocean": "해상",
                "air": "항공",
                "truck": "트럭"
            }.get(shipping_type, shipping_type)
            
            biddings.append({
                "bidding_no": bidding_no,
                "status": status_kr,
                "route": f"{pol} → {pod}",
                "shipping_type": shipping_kr,
                "load_type": load_type,
                "etd": str(etd)[:10] if etd else None,
                "deadline": str(deadline)[:16] if deadline else None,
                "bid_count": bid_count,
                "customer": customer
            })
        
        # 통계
        stats_query = text("""
            SELECT 
                status,
                COUNT(*) as count
            FROM biddings
            GROUP BY status
        """)
        stats_results = session.execute(stats_query).fetchall()
        stats = {row[0]: row[1] for row in stats_results}
        
        return {
            "success": True,
            "biddings": biddings,
            "count": len(biddings),
            "statistics": {
                "open": stats.get("open", 0),
                "closed": stats.get("closed", 0),
                "awarded": stats.get("awarded", 0),
                "total": sum(stats.values())
            }
        }
        
    except Exception as e:
        logger.error(f"get_bidding_status error: {e}")
        return {
            "success": False,
            "message": f"비딩 현황 조회 중 오류가 발생했습니다: {str(e)}"
        }
    finally:
        if session:
            session.close()


# ============================================================
# TOOL 3: GET SHIPPING INDICES (해운 지수 조회)
# ============================================================

def get_shipping_indices(index_type: str = "all", days: int = 7) -> Dict[str, Any]:
    """
    해운 시장 지수 조회 (BDI, SCFI, CCFI)
    
    Args:
        index_type: 지수 유형 (BDI, SCFI, CCFI, all)
        days: 조회 기간(일)
    
    Returns:
        지수 정보 딕셔너리
    """
    session = None
    try:
        session = get_shipping_indices_db_session()
        
        result = {}
        index_types = [index_type.upper()] if index_type.upper() != "ALL" else ["BDI", "SCFI", "CCFI"]
        
        for idx_type in index_types:
            table_name = f"{idx_type.lower()}_index"
            
            # 최신 데이터 조회
            query = text(f"""
                SELECT 
                    index_date,
                    current_index,
                    previous_index,
                    change,
                    change_rate,
                    source
                FROM {table_name}
                ORDER BY index_date DESC
                LIMIT {days}
            """)
            
            try:
                rows = session.execute(query).fetchall()
                
                if rows:
                    latest = rows[0]
                    trend = "상승" if latest[3] and latest[3] > 0 else ("하락" if latest[3] and latest[3] < 0 else "보합")
                    
                    # 지수 설명
                    descriptions = {
                        "BDI": "발틱운임지수 (Baltic Dry Index) - 벌크선 운임 지표",
                        "SCFI": "상하이컨테이너운임지수 - 상하이발 컨테이너 운임",
                        "CCFI": "중국컨테이너운임지수 - 중국발 컨테이너 운임"
                    }
                    
                    result[idx_type] = {
                        "latest": {
                            "date": str(latest[0]),
                            "value": latest[1],
                            "change": latest[3],
                            "change_rate": f"{latest[4]:.2f}%" if latest[4] else "0%",
                            "trend": trend
                        },
                        "description": descriptions.get(idx_type, ""),
                        "history": [
                            {
                                "date": str(row[0]),
                                "value": row[1],
                                "change": row[3]
                            }
                            for row in rows
                        ]
                    }
                else:
                    result[idx_type] = {"message": f"{idx_type} 데이터가 없습니다."}
                    
            except Exception as e:
                logger.warning(f"{idx_type} 조회 실패: {e}")
                result[idx_type] = {"message": f"{idx_type} 데이터 조회 실패"}
        
        return {
            "success": True,
            "indices": result,
            "queried_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
    except Exception as e:
        logger.error(f"get_shipping_indices error: {e}")
        return {
            "success": False,
            "message": f"해운 지수 조회 중 오류가 발생했습니다: {str(e)}"
        }
    finally:
        if session:
            session.close()


# ============================================================
# TOOL 4: GET LATEST NEWS (뉴스 인텔리전스)
# ============================================================

def get_latest_news(
    category: str = "all",
    is_crisis: bool = False,
    news_type: str = "all",
    limit: int = 5
) -> Dict[str, Any]:
    """
    최신 물류 뉴스 조회
    
    Args:
        category: 뉴스 카테고리 (Crisis, Ocean, Air, Inland, Economy, ETC, all)
        is_crisis: 위기 뉴스만 조회
        news_type: 뉴스 유형 (KR, GLOBAL, all)
        limit: 조회 건수
    
    Returns:
        뉴스 목록 딕셔너리
    """
    session = None
    try:
        session = get_news_db_session()
        
        # 필터 조건 구성
        conditions = ["status = 'ACTIVE'"]
        
        if category and category != "all":
            conditions.append(f"category = '{category}'")
        
        if is_crisis:
            conditions.append("is_crisis = 1")
        
        if news_type and news_type != "all":
            conditions.append(f"news_type = '{news_type}'")
        
        where_clause = " AND ".join(conditions)
        
        # 24시간 이내 뉴스 우선 조회
        query = text(f"""
            SELECT 
                id,
                title,
                content_summary,
                source_name,
                url,
                published_at_utc,
                collected_at_utc,
                news_type,
                category,
                is_crisis,
                country_tags,
                keywords
            FROM news_articles
            WHERE {where_clause}
            ORDER BY 
                CASE WHEN published_at_utc IS NOT NULL THEN published_at_utc ELSE collected_at_utc END DESC
            LIMIT {limit}
        """)
        
        rows = session.execute(query).fetchall()
        
        if not rows:
            return {
                "success": True,
                "message": "조건에 맞는 뉴스가 없습니다.",
                "articles": [],
                "count": 0
            }
        
        # 결과 정리
        articles = []
        for row in rows:
            news_id, title, summary, source, url, pub_at, coll_at, n_type, cat, crisis, countries, keywords = row
            
            # 카테고리 한글화
            cat_kr = {
                "Crisis": "위기/사고",
                "Ocean": "해운",
                "Air": "항공",
                "Inland": "육상/물류",
                "Economy": "경제",
                "ETC": "기타"
            }.get(cat, cat or "기타")
            
            articles.append({
                "id": news_id,
                "title": title,
                "summary": summary[:200] + "..." if summary and len(summary) > 200 else summary,
                "source": source,
                "url": url,
                "published_at": str(pub_at)[:16] if pub_at else str(coll_at)[:16],
                "type": "국내" if n_type == "KR" else "해외",
                "category": cat_kr,
                "is_crisis": bool(crisis),
                "keywords": keywords[:5] if keywords else []
            })
        
        # 카테고리별 통계
        stats_query = text("""
            SELECT category, COUNT(*) as count
            FROM news_articles
            WHERE status = 'ACTIVE'
            AND (published_at_utc >= datetime('now', '-24 hours') 
                 OR collected_at_utc >= datetime('now', '-24 hours'))
            GROUP BY category
        """)
        stats = session.execute(stats_query).fetchall()
        category_stats = {row[0] or "ETC": row[1] for row in stats}
        
        return {
            "success": True,
            "articles": articles,
            "count": len(articles),
            "category_stats": category_stats,
            "queried_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
    except Exception as e:
        logger.error(f"get_latest_news error: {e}")
        return {
            "success": False,
            "message": f"뉴스 조회 중 오류가 발생했습니다: {str(e)}"
        }
    finally:
        if session:
            session.close()


# ============================================================
# TOOL 5: GET PORT INFO (항구 정보 조회)
# ============================================================

def get_port_info(
    search: str = None,
    country_code: str = None,
    port_type: str = None
) -> Dict[str, Any]:
    """
    항구 정보 조회
    
    Args:
        search: 검색어 (공항/항구 코드 또는 영문 도시명)
        country_code: 국가 코드 필터
        port_type: 항구 유형 (ocean, air, both)
    
    Returns:
        항구 목록 딕셔너리
    
    Note:
        - 검색어는 영문 공항/항구명 또는 코드로 입력해야 합니다.
        - 지역명(시칠리아 등)이 아닌 실제 공항/항구명(Catania, Palermo)으로 검색하세요.
        - AI가 먼저 지역 → 공항명을 추론한 후 이 함수를 호출해야 합니다.
    """
    session = None
    try:
        session = get_quote_db_session()
        
        # 필터 조건 구성
        conditions = ["is_active = 1"]
        
        if search:
            search_upper = search.upper()
            conditions.append(f"""(
                UPPER(code) LIKE '%{search_upper}%' 
                OR UPPER(name) LIKE '%{search_upper}%' 
                OR UPPER(name_ko) LIKE '%{search_upper}%'
                OR UPPER(country) LIKE '%{search_upper}%'
            )""")
        
        if country_code:
            conditions.append(f"country_code = '{country_code.upper()}'")
        
        if port_type:
            conditions.append(f"port_type = '{port_type}'")
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT 
                code,
                name,
                name_ko,
                country,
                country_code,
                port_type
            FROM ports
            WHERE {where_clause}
            ORDER BY country_code, code
            LIMIT 20
        """)
        
        rows = session.execute(query).fetchall()
        
        if not rows:
            return {
                "success": True,
                "message": "조건에 맞는 항구를 찾을 수 없습니다. 영문 공항/항구명 또는 코드로 검색해주세요.",
                "ports": []
            }
        
        ports = []
        for code, name, name_ko, country, country_cd, p_type in rows:
            ports.append({
                "code": code,
                "name": name_ko or name,
                "name_en": name,
                "country": country,
                "country_code": country_cd,
                "type": {"ocean": "해상", "air": "항공", "both": "복합"}.get(p_type, p_type)
            })
        
        return {
            "success": True,
            "ports": ports,
            "count": len(ports)
        }
        
    except Exception as e:
        logger.error(f"get_port_info error: {e}")
        return {
            "success": False,
            "message": f"항구 정보 조회 중 오류가 발생했습니다: {str(e)}"
        }
    finally:
        if session:
            session.close()


# ============================================================
# TOOL 6: CREATE QUOTE REQUEST (견적 요청 생성)
# ============================================================

def create_quote_request(
    trade_mode: str,
    shipping_type: str,
    load_type: str,
    pol: str,
    pod: str,
    etd: str,
    eta: str = None,  # 사용자 제공 ETA (없으면 자동 계산)
    customer_company: str = None,
    customer_name: str = None,
    customer_email: str = None,
    customer_phone: str = None,
    container_type: str = None,
    container_qty: int = 1,
    cargo_weight_kg: float = None,
    cargo_cbm: float = None,
    incoterms: str = None,
    invoice_value_usd: float = 1000,
    is_dg: bool = False,
    pickup_required: bool = False,
    pickup_address: str = None,
    delivery_required: bool = False,
    delivery_address: str = None,
    remark: str = None
) -> Dict[str, Any]:
    """
    운송 견적 요청(Quote Request) 생성
    
    Quote Backend API를 호출하여 견적 요청을 생성하고 비딩을 시작합니다.
    
    Returns:
        {
            "success": bool,
            "message": str,
            "request_number": str,  # 견적 요청 번호
            "bidding_no": str,      # 비딩 번호
            "deadline": str         # 입찰 마감일
        }
    """
    import requests
    from datetime import datetime, timedelta
    
    try:
        # 필수값 검증
        if not all([trade_mode, shipping_type, load_type, pol, pod, etd]):
            return {
                "success": False,
                "message": "필수 정보가 누락되었습니다. (trade_mode, shipping_type, load_type, pol, pod, etd)"
            }
        
        if not all([customer_company, customer_name, customer_email, customer_phone]):
            return {
                "success": False,
                "message": "고객 정보가 누락되었습니다. (회사명, 담당자명, 이메일, 연락처)"
            }
        
        # 해상 FCL인 경우 컨테이너 타입 필수
        if shipping_type == "ocean" and load_type == "FCL" and not container_type:
            return {
                "success": False,
                "message": "해상 FCL 운송의 경우 컨테이너 타입이 필요합니다. (20DC, 40DC, 40HC)"
            }
        
        # ETD 형식 검증 및 ETA 처리
        try:
            etd_date = datetime.strptime(etd, "%Y-%m-%d")
            
            # 사용자가 ETA를 제공했으면 사용, 아니면 자동 계산
            if eta:
                try:
                    datetime.strptime(eta, "%Y-%m-%d")  # 형식 검증만
                    final_eta = eta
                except ValueError:
                    # ETA 형식이 잘못되면 자동 계산
                    transit_days = {"ocean": 30, "air": 7, "truck": 3}.get(shipping_type, 14)
                    eta_date = etd_date + timedelta(days=transit_days)
                    final_eta = eta_date.strftime("%Y-%m-%d")
            else:
                # ETA가 없으면 운송 유형에 따라 추정
                transit_days = {"ocean": 30, "air": 7, "truck": 3}.get(shipping_type, 14)
                eta_date = etd_date + timedelta(days=transit_days)
                final_eta = eta_date.strftime("%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "message": f"ETD 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요. (입력값: {etd})"
            }
        
        # load_type 표준화 (AIR -> Air, FCL/LCL/FTL/LTL은 대문자 유지)
        load_type_map = {
            "AIR": "Air", "air": "Air",
            "FCL": "FCL", "fcl": "FCL",
            "LCL": "LCL", "lcl": "LCL",
            "FTL": "FTL", "ftl": "FTL",
            "LTL": "LTL", "ltl": "LTL",
            "BULK": "Bulk", "bulk": "Bulk"
        }
        load_type = load_type_map.get(load_type, load_type)
        
        # 컨테이너 타입 표준화
        if container_type:
            container_type = container_type.upper()
            if container_type == "40HC":
                container_type = "4HDC"
        
        # Cargo 정보 구성
        cargo_detail = {
            "row_index": 0,
            "qty": container_qty or 1,
            "gross_weight": cargo_weight_kg,
            "cbm": cargo_cbm
        }
        
        if shipping_type == "ocean" and load_type == "FCL":
            cargo_detail["container_type"] = container_type
        elif shipping_type == "truck":
            cargo_detail["truck_type"] = "5T_WING"  # 기본값
        
        # Quote Request 데이터 구성
        quote_data = {
            "trade_mode": trade_mode,
            "shipping_type": shipping_type,
            "load_type": load_type,
            "pol": pol.upper(),
            "pod": pod.upper(),
            "etd": etd,
            "eta": final_eta,
            "incoterms": incoterms or "FOB",
            "is_dg": is_dg,
            "dg_class": None,
            "dg_un": None,
            "export_cc": False,
            "import_cc": False,
            "shipping_insurance": False,
            "pickup_required": pickup_required,
            "pickup_address": pickup_address,
            "delivery_required": delivery_required,
            "delivery_address": delivery_address,
            "invoice_value": invoice_value_usd,
            "remark": remark,
            "cargo": [cargo_detail],
            "customer": {
                "company": customer_company,
                "name": customer_name,
                "email": customer_email,
                "phone": customer_phone,
                "job_title": None
            }
        }
        
        # Quote Backend API 호출 (포트 8001)
        QUOTE_API_BASE = "http://localhost:8001"
        
        response = requests.post(
            f"{QUOTE_API_BASE}/api/quote/request",
            json=quote_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"견적 요청이 성공적으로 생성되었습니다!",
                    "request_number": result.get("request_number"),
                    "bidding_no": result.get("bidding_no"),
                    "deadline": result.get("deadline"),
                    "summary": {
                        "route": f"{pol} → {pod}",
                        "shipping_type": {"ocean": "해상", "air": "항공", "truck": "육상"}.get(shipping_type, shipping_type),
                        "load_type": load_type,
                        "etd": etd,
                        "customer": customer_company
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"견적 요청 생성 실패: {result.get('message', '알 수 없는 오류')}"
                }
        else:
            error_detail = response.json().get("detail", response.text) if response.text else "서버 오류"
            return {
                "success": False,
                "message": f"API 호출 실패 (HTTP {response.status_code}): {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요. (localhost:8000)"
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
        }
    except Exception as e:
        logger.error(f"create_quote_request error: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"견적 요청 생성 중 오류가 발생했습니다: {str(e)}"
        }


# ============================================================
# TOOL 7: GET AIR RATES (항공 운임 조회)
# ============================================================

def get_air_rates(
    pol: str,
    pod: str,
    weight_kg: float,
    chargeable_weight_kg: float = None
) -> Dict[str, Any]:
    """
    항공 화물 운임 조회
    
    Args:
        pol: 출발 공항 코드
        pod: 도착 공항 코드
        weight_kg: 화물 총중량 (kg)
        chargeable_weight_kg: Chargeable Weight (kg)
    
    Returns:
        항공 운임 정보
    """
    try:
        # Chargeable Weight 사용 (없으면 weight_kg)
        cw = chargeable_weight_kg or weight_kg
        
        # 항공 운임은 현재 DB에 없으므로 예상 운임 계산
        # 기본 운임 구조: 기본료 + (중량 * kg당 운임)
        base_rates = {
            # 한국 출발
            "ICN": {"base": 150, "per_kg": 3.5},
            # 유럽
            "CTA": {"base": 200, "per_kg": 4.0},
            "PMO": {"base": 200, "per_kg": 4.0},
            "FCO": {"base": 180, "per_kg": 3.8},
            "MXP": {"base": 180, "per_kg": 3.8},
            # 미국
            "LAX": {"base": 250, "per_kg": 4.5},
            "JFK": {"base": 280, "per_kg": 4.8},
            # 중국
            "PVG": {"base": 120, "per_kg": 2.5},
            "PEK": {"base": 130, "per_kg": 2.8},
        }
        
        # 출발지 기준 운임 (기본값 사용)
        rate_info = base_rates.get(pol.upper(), {"base": 200, "per_kg": 4.0})
        
        # 운임 계산
        freight = rate_info["base"] + (cw * rate_info["per_kg"])
        
        # 연료 할증료 (운임의 20%)
        fuel_surcharge = freight * 0.20
        
        # 보안 할증료 (고정)
        security_fee = 50
        
        # AWB 발급료
        awb_fee = 35
        
        total = freight + fuel_surcharge + security_fee + awb_fee
        
        return {
            "success": True,
            "route": f"{pol.upper()} → {pod.upper()}",
            "weight_kg": weight_kg,
            "chargeable_weight_kg": cw,
            "charges": {
                "freight": round(freight, 2),
                "fuel_surcharge": round(fuel_surcharge, 2),
                "security_fee": security_fee,
                "awb_fee": awb_fee,
                "total": round(total, 2)
            },
            "currency": "USD",
            "note": "예상 운임입니다. 실제 운임은 항공사 및 시즌에 따라 변동될 수 있습니다.",
            "transit_days": "3-7일 (직항/경유에 따라 상이)"
        }
        
    except Exception as e:
        logger.error(f"get_air_rates error: {e}")
        return {
            "success": False,
            "message": f"항공 운임 조회 중 오류 발생: {str(e)}"
        }


# ============================================================
# TOOL 8: GET SCHEDULES (스케줄 조회)
# ============================================================

def get_schedules(
    pol: str,
    pod: str,
    shipping_type: str,
    etd: str = None,
    limit: int = 5
) -> Dict[str, Any]:
    """
    항공/해상 운송 스케줄 조회
    
    Args:
        pol: 출발지 코드
        pod: 도착지 코드
        shipping_type: 운송 유형 (air/ocean)
        etd: 출발 예정일 (YYYY-MM-DD)
        limit: 조회 개수
    
    Returns:
        스케줄 목록
    """
    from datetime import datetime, timedelta
    import random
    
    try:
        # 기준 날짜 설정
        if etd:
            try:
                base_date = datetime.strptime(etd, "%Y-%m-%d")
            except ValueError:
                base_date = datetime.now()
        else:
            base_date = datetime.now()
        
        schedules = []
        
        if shipping_type == "air":
            # 항공 스케줄 (예시 데이터)
            carriers = ["KE", "OZ", "CX", "SQ", "LH", "AF", "BA", "TK"]
            for i in range(min(limit, 5)):
                departure = base_date + timedelta(days=i)
                transit_days = random.randint(1, 3)
                arrival = departure + timedelta(days=transit_days)
                
                schedules.append({
                    "carrier": random.choice(carriers),
                    "flight_no": f"{random.choice(carriers)}{random.randint(100, 999)}",
                    "departure": departure.strftime("%Y-%m-%d"),
                    "departure_time": f"{random.randint(6, 22):02d}:{random.choice(['00', '30'])}",
                    "arrival": arrival.strftime("%Y-%m-%d"),
                    "transit_days": transit_days,
                    "stops": "Direct" if transit_days <= 1 else f"{transit_days-1} Stop(s)",
                    "available": random.choice(["Available", "Limited", "On Request"])
                })
        else:
            # 해상 스케줄 (예시 데이터)
            carriers = ["MSC", "Maersk", "CMA CGM", "COSCO", "Evergreen", "HMM", "ONE", "Yang Ming"]
            vessel_names = ["GLORY", "FORTUNE", "STAR", "OCEAN", "PACIFIC", "ATLANTIC", "PIONEER"]
            
            for i in range(min(limit, 5)):
                departure = base_date + timedelta(days=i * 2)
                transit_days = random.randint(14, 35)
                arrival = departure + timedelta(days=transit_days)
                
                schedules.append({
                    "carrier": random.choice(carriers),
                    "vessel": f"{random.choice(vessel_names)} {random.choice(['V.', ''])}",
                    "voyage": f"{random.randint(100, 999)}E",
                    "departure": departure.strftime("%Y-%m-%d"),
                    "arrival": arrival.strftime("%Y-%m-%d"),
                    "transit_days": transit_days,
                    "service": f"Service {random.choice(['A', 'B', 'C', 'D'])}",
                    "transhipment": random.choice(["Direct", "T/S 1", "T/S 2"]),
                    "available": random.choice(["Available", "Limited Space", "Wait Listed"])
                })
        
        return {
            "success": True,
            "route": f"{pol.upper()} → {pod.upper()}",
            "shipping_type": {"air": "항공", "ocean": "해상"}.get(shipping_type, shipping_type),
            "base_date": base_date.strftime("%Y-%m-%d"),
            "count": len(schedules),
            "schedules": schedules,
            "note": "스케줄은 예시 데이터입니다. 실제 스케줄은 선사/항공사 확인이 필요합니다."
        }
        
    except Exception as e:
        logger.error(f"get_schedules error: {e}")
        return {
            "success": False,
            "message": f"스케줄 조회 중 오류 발생: {str(e)}"
        }


# ============================================================
# TOOL 9: GET QUOTE DETAIL (견적 상세 조회)
# ============================================================

def get_quote_detail(quote_id: str) -> Dict[str, Any]:
    """
    견적 요청 상세 정보 조회
    
    Args:
        quote_id: 견적 ID 또는 비딩 번호
    
    Returns:
        견적 상세 정보
    """
    session = None
    try:
        session = get_quote_db_session()
        
        # 비딩 번호 또는 ID로 조회
        query = text("""
            SELECT 
                qr.id, qr.request_number, qr.trade_mode, qr.shipping_type, qr.load_type,
                qr.pol, qr.pod, qr.etd, qr.eta, qr.incoterms, qr.invoice_value,
                qr.is_dg, qr.pickup_required, qr.pickup_address,
                qr.delivery_required, qr.delivery_address, qr.remark,
                qr.created_at,
                b.bidding_no, b.status as bidding_status, b.bid_deadline,
                c.company as customer_company, c.name as customer_name,
                c.email as customer_email, c.phone as customer_phone
            FROM quote_requests qr
            LEFT JOIN biddings b ON qr.id = b.quote_request_id
            LEFT JOIN customers c ON qr.customer_id = c.id
            WHERE qr.request_number = :quote_id 
               OR b.bidding_no = :quote_id
               OR CAST(qr.id AS TEXT) = :quote_id
            LIMIT 1
        """)
        
        result = session.execute(query, {"quote_id": quote_id}).fetchone()
        
        if not result:
            return {
                "success": False,
                "message": f"견적을 찾을 수 없습니다: {quote_id}"
            }
        
        return {
            "success": True,
            "quote": {
                "id": result[0],
                "request_number": result[1],
                "trade_mode": result[2],
                "shipping_type": result[3],
                "load_type": result[4],
                "route": f"{result[5]} → {result[6]}",
                "pol": result[5],
                "pod": result[6],
                "etd": result[7],
                "eta": result[8],
                "incoterms": result[9],
                "invoice_value": result[10],
                "is_dg": result[11],
                "pickup": {
                    "required": result[12],
                    "address": result[13]
                },
                "delivery": {
                    "required": result[14],
                    "address": result[15]
                },
                "remark": result[16],
                "created_at": result[17]
            },
            "bidding": {
                "bidding_no": result[18],
                "status": result[19],
                "deadline": result[20]
            },
            "customer": {
                "company": result[21],
                "name": result[22],
                "email": result[23],
                "phone": result[24]
            }
        }
        
    except Exception as e:
        logger.error(f"get_quote_detail error: {e}")
        return {
            "success": False,
            "message": f"견적 상세 조회 중 오류 발생: {str(e)}"
        }
    finally:
        if session:
            session.close()


# ============================================================
# TOOL 10: GET EXCHANGE RATES (환율 조회)
# ============================================================

def get_exchange_rates(
    base_currency: str = "USD",
    target_currency: str = "KRW"
) -> Dict[str, Any]:
    """
    실시간 환율 조회 (한국은행 API 연동)
    
    Args:
        base_currency: 기준 통화
        target_currency: 목표 통화 (콤마로 다중 지정 가능)
    
    Returns:
        환율 정보
    """
    # 기본 환율 (Quote Backend와 동일 - 한국은행 API 실패 시 사용)
    DEFAULT_RATES = {
        "USD": {"KRW": 1450.0, "CNY": 7.25, "EUR": 0.92, "JPY": 155.30, "GBP": 0.79, "SGD": 1.35, "HKD": 7.82},
        "EUR": {"KRW": 1550.0, "USD": 1.087},
        "JPY": {"KRW": 9.5},
        "CNY": {"KRW": 200.0}
    }
    
    def fetch_bok_rate(currency: str) -> float:
        """한국은행 API에서 환율 조회 (Flask 서버 경유)"""
        try:
            from datetime import timedelta
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
            
            response = requests.get(
                f"{FLASK_API_BASE}/api/market/indices",
                params={
                    "type": "exchange",
                    "itemCode": currency.upper(),
                    "startDate": start_date,
                    "endDate": end_date,
                    "cycle": "D"
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    latest = data["data"][-1]
                    return float(latest.get("DATA_VALUE", 0))
        except Exception as e:
            logger.warning(f"한국은행 API 환율 조회 실패 ({currency}): {e}")
        
        return None
    
    try:
        base = base_currency.upper()
        targets = [t.strip().upper() for t in target_currency.split(",")]
        
        rates = {}
        api_source = "한국은행 API"
        
        for target in targets:
            rate_value = None
            
            # KRW 환율인 경우 한국은행 API 시도
            if target == "KRW" and base in ["USD", "EUR", "JPY", "CNY"]:
                rate_value = fetch_bok_rate(base)
            
            # API 실패 시 기본값 사용
            if rate_value is None:
                api_source = "기본값"
                if base in DEFAULT_RATES and target in DEFAULT_RATES[base]:
                    rate_value = DEFAULT_RATES[base][target]
            
            if rate_value:
                rates[target] = {
                    "rate": rate_value,
                    "pair": f"{base}/{target}"
                }
        
        if not rates:
            return {
                "success": False,
                "message": f"지원하지 않는 통화 쌍입니다: {base}/{target_currency}"
            }
        
        return {
            "success": True,
            "base_currency": base,
            "rates": rates,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": api_source,
            "note": "환율은 한국은행 API 또는 시스템 기본값입니다."
        }
        
    except Exception as e:
        logger.error(f"get_exchange_rates error: {e}")
        return {
            "success": False,
            "message": f"환율 조회 중 오류 발생: {str(e)}"
        }


# ============================================================
# TOOL 11: GET GLOBAL ALERTS (GDELT 경고 조회)
# ============================================================

def get_global_alerts(
    region: str = None,
    category: str = "all",
    severity: str = "all",
    limit: int = 10
) -> Dict[str, Any]:
    """
    GDELT 기반 글로벌 물류/공급망 경고 조회
    
    Args:
        region: 지역 필터
        category: 카테고리 (conflict, disaster, economic, political)
        severity: 심각도 (critical, high, medium)
        limit: 조회 개수
    
    Returns:
        경고 목록
    """
    try:
        # GDELT 데이터 조회 (gdelt_backend 모듈 활용)
        import sys
        sys.path.insert(0, SERVER_DIR)
        
        try:
            from gdelt_backend import get_critical_alerts as gdelt_get_alerts
            
            result = gdelt_get_alerts(
                category=category if category != "all" else None,
                limit=limit
            )
            
            if result:
                # 지역 필터링
                alerts = result.get("alerts", [])
                if region:
                    region_lower = region.lower()
                    alerts = [a for a in alerts if region_lower in str(a.get("region", "")).lower()]
                
                # 심각도 필터링
                if severity != "all":
                    severity_map = {"critical": 3, "high": 2, "medium": 1}
                    min_severity = severity_map.get(severity, 0)
                    alerts = [a for a in alerts if a.get("severity_level", 0) >= min_severity]
                
                return {
                    "success": True,
                    "count": len(alerts[:limit]),
                    "alerts": alerts[:limit],
                    "filters": {
                        "region": region,
                        "category": category,
                        "severity": severity
                    }
                }
        except ImportError:
            pass
        
        # GDELT 모듈이 없으면 예시 데이터 반환
        sample_alerts = [
            {
                "title": "홍해 지역 선박 안전 경고",
                "region": "Middle East",
                "category": "conflict",
                "severity": "critical",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "impact": "홍해 통과 선박 운항 지연 예상"
            },
            {
                "title": "동남아시아 태풍 접근",
                "region": "Asia",
                "category": "disaster",
                "severity": "high",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "impact": "필리핀-베트남 항로 영향 가능"
            }
        ]
        
        return {
            "success": True,
            "count": len(sample_alerts),
            "alerts": sample_alerts,
            "note": "예시 데이터입니다. 실제 GDELT 연동 시 실시간 경고가 표시됩니다."
        }
        
    except Exception as e:
        logger.error(f"get_global_alerts error: {e}")
        return {
            "success": False,
            "message": f"글로벌 경고 조회 중 오류 발생: {str(e)}"
        }


# ============================================================
# TOOL 12: NAVIGATE TO PAGE (페이지 이동 안내)
# ============================================================

def navigate_to_page(
    page: str,
    params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    사용자를 플랫폼의 특정 페이지로 안내
    
    Args:
        page: 이동할 페이지 이름
        params: 페이지에 전달할 파라미터
    
    Returns:
        네비게이션 정보
    """
    page_map = {
        "quotation": {
            "path": "/pages/quotation.html",
            "title": "견적 요청",
            "description": "새로운 운송 견적을 요청하는 페이지입니다."
        },
        "bidding": {
            "path": "/pages/bidding-list.html",
            "title": "비딩 현황",
            "description": "진행 중인 비딩 목록을 확인하는 페이지입니다."
        },
        "market-indices": {
            "path": "/pages/market-indices.html",
            "title": "시장 지수",
            "description": "BDI, SCFI, CCFI 등 해운 시장 지수를 확인하는 페이지입니다."
        },
        "news": {
            "path": "/pages/news-intelligence.html",
            "title": "뉴스 인텔리전스",
            "description": "물류 관련 최신 뉴스와 분석을 확인하는 페이지입니다."
        },
        "dashboard": {
            "path": "/pages/dashboard.html",
            "title": "대시보드",
            "description": "전체 현황을 한눈에 확인하는 대시보드입니다."
        },
        "reports": {
            "path": "/pages/reports.html",
            "title": "리포트",
            "description": "물류 시장 분석 리포트를 확인하는 페이지입니다."
        }
    }
    
    if page not in page_map:
        return {
            "success": False,
            "message": f"알 수 없는 페이지입니다: {page}",
            "available_pages": list(page_map.keys())
        }
    
    page_info = page_map[page]
    
    # URL 파라미터 생성
    url = page_info["path"]
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{url}?{param_str}"
    
    return {
        "success": True,
        "action": "navigate",
        "page": page,
        "url": url,
        "title": page_info["title"],
        "description": page_info["description"],
        "params": params
    }


# ============================================================
# PHASE 0: 화주 견적 업무 도구
# ============================================================

def get_my_quotes(
    customer_email: str,
    status: str = "all",
    limit: int = 10
) -> Dict[str, Any]:
    """
    화주의 견적 요청 목록 조회
    
    Args:
        customer_email: 고객 이메일
        status: 상태 필터
        limit: 조회 건수
    
    Returns:
        견적 요청 목록
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        params = {
            "customer_email": customer_email,
            "limit": limit
        }
        if status and status != "all":
            params["status"] = status
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/quote/requests",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get("quotes", data.get("requests", []))
            
            return {
                "success": True,
                "count": len(quotes),
                "quotes": quotes,
                "customer_email": customer_email
            }
        else:
            return {
                "success": False,
                "message": f"견적 목록 조회 실패: {response.text}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"get_my_quotes error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def update_quote_request(
    bidding_no: str,
    etd: str = None,
    eta: str = None,
    incoterms: str = None,
    pickup_required: bool = None,
    pickup_address: str = None,
    delivery_required: bool = None,
    delivery_address: str = None,
    remark: str = None
) -> Dict[str, Any]:
    """
    견적 요청 수정
    
    Args:
        bidding_no: 비딩 번호
        기타: 수정할 필드들
    
    Returns:
        수정 결과
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        update_data = {}
        if etd:
            update_data["etd"] = etd
        if eta:
            update_data["eta"] = eta
        if incoterms:
            update_data["incoterms"] = incoterms
        if pickup_required is not None:
            update_data["pickup_required"] = pickup_required
        if pickup_address:
            update_data["pickup_address"] = pickup_address
        if delivery_required is not None:
            update_data["delivery_required"] = delivery_required
        if delivery_address:
            update_data["delivery_address"] = delivery_address
        if remark:
            update_data["remark"] = remark
        
        if not update_data:
            return {
                "success": False,
                "message": "수정할 내용이 없습니다."
            }
        
        response = requests.put(
            f"{QUOTE_API_BASE}/api/quote/update/{bidding_no}",
            json=update_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "message": f"견적 요청이 수정되었습니다.",
                "bidding_no": bidding_no,
                "updated_fields": list(update_data.keys())
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"견적 수정 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"update_quote_request error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def cancel_quote_request(request_id: int) -> Dict[str, Any]:
    """
    견적 요청 취소
    
    Args:
        request_id: 견적 요청 ID
    
    Returns:
        취소 결과
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        response = requests.delete(
            f"{QUOTE_API_BASE}/api/quote-request/{request_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": f"견적 요청(ID: {request_id})이 취소되었습니다."
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"견적 취소 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"cancel_quote_request error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


# ============================================================
# PHASE 1: 비딩/입찰 도구
# ============================================================

def submit_bid(
    bidding_id: int,
    forwarder_id: int,
    total_amount: float,
    freight_charge: float = None,
    local_charge: float = None,
    other_charge: float = None,
    transit_time: str = None,
    validity_date: str = None,
    remark: str = None
) -> Dict[str, Any]:
    """
    포워더가 비딩에 입찰 제출
    
    Args:
        bidding_id: 비딩 ID
        forwarder_id: 포워더 ID
        total_amount: 총 운임
        기타: 운임 상세 및 비고
    
    Returns:
        입찰 제출 결과
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        bid_data = {
            "bidding_id": bidding_id,
            "total_amount": total_amount
        }
        
        if freight_charge is not None:
            bid_data["freight_charge"] = freight_charge
        if local_charge is not None:
            bid_data["local_charge"] = local_charge
        if other_charge is not None:
            bid_data["other_charge"] = other_charge
        if transit_time:
            bid_data["transit_time"] = transit_time
        if validity_date:
            bid_data["validity_date"] = validity_date
        if remark:
            bid_data["remark"] = remark
        
        response = requests.post(
            f"{QUOTE_API_BASE}/api/bid/submit",
            params={"forwarder_id": forwarder_id},
            json=bid_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "message": "입찰이 성공적으로 제출되었습니다!",
                "bid_id": result.get("bid", {}).get("id"),
                "bidding_id": bidding_id,
                "total_amount": total_amount
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"입찰 제출 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"submit_bid error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def award_bid(bidding_no: str, bid_id: int) -> Dict[str, Any]:
    """
    입찰 낙찰 처리 (화주용)
    
    Args:
        bidding_no: 비딩 번호
        bid_id: 낙찰할 입찰 ID
    
    Returns:
        낙찰 결과
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        response = requests.post(
            f"{QUOTE_API_BASE}/api/bidding/{bidding_no}/award",
            params={"bid_id": bid_id},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("data", {})
            return {
                "success": True,
                "message": f"입찰이 낙찰되었습니다!",
                "bidding_no": bidding_no,
                "awarded_bid_id": bid_id,
                "forwarder_company": data.get("forwarder_company"),
                "total_amount": data.get("total_amount")
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"낙찰 처리 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"award_bid error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def get_bidding_detail(bidding_no: str) -> Dict[str, Any]:
    """
    비딩 상세 정보 조회
    
    Args:
        bidding_no: 비딩 번호
    
    Returns:
        비딩 상세 정보
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/bidding/{bidding_no}/detail",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "bidding": data
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"비딩 조회 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"get_bidding_detail error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def get_bidding_bids(bidding_no: str) -> Dict[str, Any]:
    """
    비딩에 제출된 입찰 목록 조회
    
    Args:
        bidding_no: 비딩 번호
    
    Returns:
        입찰 목록
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/bidding/{bidding_no}/bids",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            bids = data.get("bids", [])
            return {
                "success": True,
                "bidding_no": bidding_no,
                "count": len(bids),
                "bids": bids
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"입찰 목록 조회 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"get_bidding_bids error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def close_bidding(bidding_no: str) -> Dict[str, Any]:
    """
    비딩 마감
    
    Args:
        bidding_no: 비딩 번호
    
    Returns:
        마감 결과
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        response = requests.post(
            f"{QUOTE_API_BASE}/api/bidding/{bidding_no}/close",
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": f"비딩({bidding_no})이 마감되었습니다.",
                "bidding_no": bidding_no
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"비딩 마감 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"close_bidding error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def get_my_bids(
    forwarder_id: int,
    status: str = "all",
    limit: int = 10
) -> Dict[str, Any]:
    """
    포워더의 입찰 목록 조회
    
    Args:
        forwarder_id: 포워더 ID
        status: 상태 필터
        limit: 조회 건수
    
    Returns:
        입찰 목록
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        params = {
            "forwarder_id": forwarder_id,
            "limit": limit
        }
        if status and status != "all":
            params["status"] = status
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/bid/my-bids",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            bids = data.get("bids", [])
            return {
                "success": True,
                "count": len(bids),
                "bids": bids
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"입찰 목록 조회 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"get_my_bids error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


# ============================================================
# PHASE 2: 계약/배송 도구
# ============================================================

def get_contracts(
    user_type: str,
    user_id: int,
    status: str = "all",
    limit: int = 10
) -> Dict[str, Any]:
    """
    계약 목록 조회
    
    Args:
        user_type: 사용자 유형 (shipper/forwarder)
        user_id: 사용자 ID
        status: 상태 필터
        limit: 조회 건수
    
    Returns:
        계약 목록
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        params = {
            "user_type": user_type,
            "user_id": user_id,
            "limit": limit
        }
        if status and status != "all":
            params["status"] = status
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/contracts",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            contracts = data.get("contracts", [])
            return {
                "success": True,
                "count": len(contracts),
                "contracts": contracts
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"계약 목록 조회 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"get_contracts error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def get_contract_detail(contract_id: int) -> Dict[str, Any]:
    """
    계약 상세 정보 조회
    
    Args:
        contract_id: 계약 ID
    
    Returns:
        계약 상세 정보
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/contract/{contract_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "contract": data
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"계약 조회 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"get_contract_detail error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def track_shipment(shipment_id: int) -> Dict[str, Any]:
    """
    배송 추적
    
    Args:
        shipment_id: 배송 ID
    
    Returns:
        배송 상세 정보 및 추적 이력
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/shipment/{shipment_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "shipment": {
                    "id": data.get("id"),
                    "shipment_no": data.get("shipment_no"),
                    "current_status": data.get("current_status"),
                    "current_location": data.get("current_location"),
                    "estimated_delivery": data.get("estimated_delivery"),
                    "actual_delivery": data.get("actual_delivery"),
                    "bl_no": data.get("bl_no"),
                    "vessel_flight": data.get("vessel_flight"),
                    "pol": data.get("pol"),
                    "pod": data.get("pod"),
                    "tracking_history": data.get("tracking_history", [])
                }
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"배송 추적 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"track_shipment error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def get_shipments(
    user_type: str,
    user_id: int,
    status: str = "all",
    limit: int = 10
) -> Dict[str, Any]:
    """
    배송 목록 조회
    
    Args:
        user_type: 사용자 유형
        user_id: 사용자 ID
        status: 상태 필터
        limit: 조회 건수
    
    Returns:
        배송 목록
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        params = {
            "user_type": user_type,
            "user_id": user_id,
            "limit": limit
        }
        if status and status != "all":
            params["status"] = status
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/shipments",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            shipments = data.get("shipments", [])
            return {
                "success": True,
                "count": len(shipments),
                "shipments": shipments
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"배송 목록 조회 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"get_shipments error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


# ============================================================
# PHASE 3: 분석/소통 도구
# ============================================================

def get_shipper_analytics(
    customer_id: int,
    from_date: str = None,
    to_date: str = None
) -> Dict[str, Any]:
    """
    화주 분석 데이터 조회
    
    Args:
        customer_id: 고객 ID
        from_date: 시작일
        to_date: 종료일
    
    Returns:
        분석 데이터 (KPI)
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        params = {"customer_id": customer_id}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/analytics/shipper/summary",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "analytics": {
                    "total_requests": data.get("total_requests"),
                    "avg_bids_per_request": data.get("avg_bids_per_request"),
                    "award_rate": data.get("award_rate"),
                    "total_cost_krw": data.get("total_cost_krw"),
                    "avg_saving_rate": data.get("avg_saving_rate"),
                    "period": {
                        "from": from_date or "전체",
                        "to": to_date or "현재"
                    }
                }
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"분석 데이터 조회 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"get_shipper_analytics error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def get_notifications(
    user_type: str,
    user_id: int,
    unread_only: bool = False,
    limit: int = 20
) -> Dict[str, Any]:
    """
    알림 목록 조회
    
    Args:
        user_type: 사용자 유형
        user_id: 사용자 ID
        unread_only: 읽지 않은 알림만
        limit: 조회 건수
    
    Returns:
        알림 목록
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        params = {
            "user_type": user_type,
            "user_id": user_id,
            "limit": limit
        }
        if unread_only:
            params["unread_only"] = "true"
        
        response = requests.get(
            f"{QUOTE_API_BASE}/api/notifications",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            notifications = data.get("notifications", [])
            return {
                "success": True,
                "count": len(notifications),
                "unread_count": data.get("unread_count", 0),
                "notifications": notifications
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"알림 조회 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"get_notifications error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


def send_message(
    bidding_id: int,
    sender_type: str,
    sender_id: int,
    message: str
) -> Dict[str, Any]:
    """
    메시지 발송
    
    Args:
        bidding_id: 비딩 ID
        sender_type: 발신자 유형 (shipper/forwarder)
        sender_id: 발신자 ID
        message: 메시지 내용
    
    Returns:
        발송 결과
    """
    import requests
    
    try:
        QUOTE_API_BASE = "http://localhost:8001"
        
        response = requests.post(
            f"{QUOTE_API_BASE}/api/messages",
            json={
                "bidding_id": bidding_id,
                "sender_type": sender_type,
                "sender_id": sender_id,
                "content": message
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "message": "메시지가 발송되었습니다.",
                "message_id": result.get("id")
            }
        else:
            error_detail = response.json().get("detail", response.text)
            return {
                "success": False,
                "message": f"메시지 발송 실패: {error_detail}"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Quote Backend 서버에 연결할 수 없습니다."
        }
    except Exception as e:
        logger.error(f"send_message error: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


# ============================================================
# TOOL EXECUTOR (통합 실행기)
# ============================================================

def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool 함수 실행
    
    Args:
        tool_name: Tool 이름
        parameters: Tool 파라미터
    
    Returns:
        Tool 실행 결과
    """
    tool_map = {
        # 기존 도구
        "get_ocean_rates": get_ocean_rates,
        "get_bidding_status": get_bidding_status,
        "get_shipping_indices": get_shipping_indices,
        "get_latest_news": get_latest_news,
        "get_port_info": get_port_info,
        "create_quote_request": create_quote_request,
        # 새 MCP 도구
        "get_air_rates": get_air_rates,
        "get_schedules": get_schedules,
        "get_quote_detail": get_quote_detail,
        "get_exchange_rates": get_exchange_rates,
        "get_global_alerts": get_global_alerts,
        "navigate_to_page": navigate_to_page,
        # Phase 0: 화주 견적 업무
        "get_my_quotes": get_my_quotes,
        "update_quote_request": update_quote_request,
        "cancel_quote_request": cancel_quote_request,
        # Phase 1: 비딩/입찰
        "submit_bid": submit_bid,
        "award_bid": award_bid,
        "get_bidding_detail": get_bidding_detail,
        "get_bidding_bids": get_bidding_bids,
        "close_bidding": close_bidding,
        "get_my_bids": get_my_bids,
        # Phase 2: 계약/배송
        "get_contracts": get_contracts,
        "get_contract_detail": get_contract_detail,
        "track_shipment": track_shipment,
        "get_shipments": get_shipments,
        # Phase 3: 분석/소통
        "get_shipper_analytics": get_shipper_analytics,
        "get_notifications": get_notifications,
        "send_message": send_message,
    }
    
    if tool_name not in tool_map:
        return {
            "success": False,
            "message": f"알 수 없는 Tool: {tool_name}"
        }
    
    try:
        return tool_map[tool_name](**parameters)
    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}")
        return {
            "success": False,
            "message": f"Tool 실행 중 오류 발생: {str(e)}"
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("AI Tools Test")
    print("=" * 60)
    
    # Test 1: Ocean Rates
    print("\n[TEST 1] Ocean Rates - KRPUS → NLRTM")
    result = get_ocean_rates("KRPUS", "NLRTM", "4HDC")
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Route: {result.get('route')}")
        print(f"Total: {result.get('total')}")
    else:
        print(f"Message: {result.get('message')}")
    
    # Test 2: Bidding Status
    print("\n[TEST 2] Bidding Status")
    result = get_bidding_status("open", 3)
    print(f"Success: {result.get('success')}")
    print(f"Count: {result.get('count')}")
    
    # Test 3: Shipping Indices
    print("\n[TEST 3] Shipping Indices - BDI")
    result = get_shipping_indices("BDI", 5)
    print(f"Success: {result.get('success')}")
    if result.get('success') and result.get('indices'):
        bdi = result['indices'].get('BDI', {})
        if 'latest' in bdi:
            print(f"BDI Latest: {bdi['latest']}")
    
    # Test 4: Latest News
    print("\n[TEST 4] Latest News")
    result = get_latest_news(category="all", limit=3)
    print(f"Success: {result.get('success')}")
    print(f"Count: {result.get('count')}")
    
    # Test 5: Port Info
    print("\n[TEST 5] Port Info - Korea")
    result = get_port_info(country_code="KR")
    print(f"Success: {result.get('success')}")
    print(f"Ports: {[p['code'] for p in result.get('ports', [])]}")
