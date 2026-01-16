"""
AI Assistant API Blueprint
Gemini AI 기반 어시스턴트 API 라우트

Endpoints:
- /api/ai/chat - AI 대화
- /api/ai/suggestions - 빠른 제안 목록
- /api/ai/clear - 대화 이력 삭제
- /api/ai/status - AI 서비스 상태
- /api/ai/create-quote - AI 견적 요청 생성
"""

import logging
from flask import Blueprint, request, jsonify

import gemini_backend

logger = logging.getLogger(__name__)

# Flask Blueprint
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@ai_bp.route('/chat', methods=['POST'])
def ai_chat():
    """
    AI 어시스턴트와 대화
    
    Request Body:
    {
        "session_id": "unique_session_id",
        "message": "사용자 메시지"
    }
    
    Response:
    {
        "success": bool,
        "message": "AI 응답",
        "quote_data": {...} or null  # 추출된 Quote 데이터
    }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'message': '메시지를 입력해주세요.'}), 400
        
        result = gemini_backend.chat_with_gemini(session_id, message)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI Chat error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'}), 500


@ai_bp.route('/suggestions', methods=['GET'])
def ai_suggestions():
    """빠른 제안 버튼 목록 반환"""
    suggestions = gemini_backend.get_quick_suggestions()
    return jsonify({'suggestions': suggestions})


@ai_bp.route('/clear', methods=['POST'])
def ai_clear_conversation():
    """
    대화 이력 삭제
    
    Request Body:
    {
        "session_id": "unique_session_id"
    }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        success = gemini_backend.clear_conversation(session_id)
        
        if success:
            return jsonify({'success': True, 'message': '대화 이력이 삭제되었습니다.'})
        else:
            return jsonify({'success': False, 'message': '대화 이력 삭제에 실패했습니다.'}), 500
            
    except Exception as e:
        logger.error(f"AI Clear error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'}), 500


@ai_bp.route('/status', methods=['GET'])
def ai_status():
    """AI 서비스 상태 확인"""
    return jsonify({
        'available': gemini_backend.GEMINI_AVAILABLE,
        'model': 'gemini-2.5-flash' if gemini_backend.GEMINI_AVAILABLE else None
    })


@ai_bp.route('/create-quote', methods=['POST'])
def ai_create_quote():
    """
    AI 어시스턴트에서 직접 견적 요청 생성
    프론트엔드의 '견적 요청하기' 버튼 클릭 시 호출됨
    """
    try:
        from ai_tools import create_quote_request
        
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': '요청 데이터가 없습니다.'}), 400
        
        # create_quote_request 호출
        result = create_quote_request(
            trade_mode=data.get('trade_mode'),
            shipping_type=data.get('shipping_type'),
            load_type=data.get('load_type'),
            pol=data.get('pol'),
            pod=data.get('pod'),
            etd=data.get('etd'),
            customer_company=data.get('customer_company'),
            customer_name=data.get('customer_name'),
            customer_email=data.get('customer_email'),
            customer_phone=data.get('customer_phone'),
            container_type=data.get('container_type'),
            container_qty=data.get('container_qty', 1),
            cargo_weight_kg=data.get('cargo_weight_kg'),
            cargo_cbm=data.get('cargo_cbm'),
            incoterms=data.get('incoterms'),
            invoice_value_usd=data.get('invoice_value_usd', 1000),
            is_dg=data.get('is_dg', False),
            pickup_required=data.get('pickup_required', False),
            pickup_address=data.get('pickup_address'),
            delivery_required=data.get('delivery_required', False),
            delivery_address=data.get('delivery_address'),
            remark=data.get('remark')
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI Create Quote error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'견적 생성 중 오류가 발생했습니다: {str(e)}'}), 500

