"""
Authentication Backend
사용자 인증 API 로직 (비밀번호 암호화 포함)
"""

import bcrypt
import re
from datetime import datetime
from flask import Blueprint, request, jsonify
from .models import User, get_session, init_db, UserType

# Flask Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def hash_password(password: str) -> str:
    """
    비밀번호를 bcrypt로 해시화
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    비밀번호 검증
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str):
    """
    비밀번호 유효성 검증
    - 최소 8자 이상
    - 영문, 숫자 포함
    """
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다."
    if not re.search(r'[A-Za-z]', password):
        return False, "비밀번호에 영문자가 포함되어야 합니다."
    if not re.search(r'\d', password):
        return False, "비밀번호에 숫자가 포함되어야 합니다."
    return True, ""


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    회원가입 API
    
    Required fields:
    - user_type: shipper | forwarder
    - company: 회사명
    - name: 담당자명
    - email: 이메일
    - phone: 연락처
    - password: 비밀번호
    
    Optional:
    - business_no: 사업자등록번호
    """
    data = request.json
    
    # 필수 필드 검증
    required_fields = ['user_type', 'company', 'name', 'email', 'phone', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field}은(는) 필수 입력 항목입니다.'}), 400
    
    # 사용자 유형 검증
    if data['user_type'] not in ['shipper', 'forwarder']:
        return jsonify({'error': '유효하지 않은 사용자 유형입니다.'}), 400
    
    # 이메일 형식 검증
    if not validate_email(data['email']):
        return jsonify({'error': '올바른 이메일 형식이 아닙니다.'}), 400
    
    # 비밀번호 검증
    is_valid, message = validate_password(data['password'])
    if not is_valid:
        return jsonify({'error': message}), 400
    
    session = get_session()
    try:
        # 이메일 중복 확인
        existing = session.query(User).filter(User.email == data['email']).first()
        if existing:
            return jsonify({'error': '이미 등록된 이메일입니다.'}), 409
        
        # 사용자 생성
        user = User(
            user_type=data['user_type'],
            company=data['company'],
            business_no=data.get('business_no'),
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            password_hash=hash_password(data['password'])
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return jsonify({
            'message': '회원가입이 완료되었습니다.',
            'user': {
                'id': user.id,
                'user_type': user.user_type,
                'company': user.company,
                'name': user.name,
                'email': user.email,
                'phone': user.phone
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'회원가입 중 오류가 발생했습니다: {str(e)}'}), 500
    finally:
        session.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    로그인 API
    
    Required fields:
    - email: 이메일
    - password: 비밀번호
    """
    data = request.json
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': '이메일과 비밀번호를 입력해주세요.'}), 400
    
    session = get_session()
    try:
        user = session.query(User).filter(User.email == data['email']).first()
        
        if not user:
            return jsonify({'error': '등록되지 않은 이메일입니다.'}), 404
        
        if not user.is_active:
            return jsonify({'error': '비활성화된 계정입니다.'}), 403
        
        if not verify_password(data['password'], user.password_hash):
            return jsonify({'error': '비밀번호가 일치하지 않습니다.'}), 401
        
        # 마지막 로그인 시간 업데이트
        user.last_login_at = datetime.utcnow()
        session.commit()
        
        return jsonify({
            'message': '로그인 성공',
            'user': {
                'id': user.id,
                'user_type': user.user_type,
                'company': user.company,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'business_no': user.business_no
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'로그인 중 오류가 발생했습니다: {str(e)}'}), 500
    finally:
        session.close()


@auth_bp.route('/check-email', methods=['GET'])
def check_email():
    """
    이메일 중복 확인 API
    """
    email = request.args.get('email')
    
    if not email:
        return jsonify({'error': '이메일을 입력해주세요.'}), 400
    
    if not validate_email(email):
        return jsonify({'error': '올바른 이메일 형식이 아닙니다.'}), 400
    
    session = get_session()
    try:
        existing = session.query(User).filter(User.email == email).first()
        return jsonify({
            'email': email,
            'available': existing is None
        }), 200
    finally:
        session.close()


@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    사용자 정보 조회 API
    """
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'user_type': user.user_type,
                'company': user.company,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'business_no': user.business_no,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
        }), 200
    finally:
        session.close()


@auth_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    사용자 정보 수정 API
    """
    data = request.json
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        # 수정 가능한 필드
        if data.get('company'):
            user.company = data['company']
        if data.get('name'):
            user.name = data['name']
        if data.get('phone'):
            user.phone = data['phone']
        if data.get('business_no') is not None:
            user.business_no = data['business_no']
        
        session.commit()
        
        return jsonify({
            'message': '사용자 정보가 수정되었습니다.',
            'user': {
                'id': user.id,
                'user_type': user.user_type,
                'company': user.company,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'business_no': user.business_no
            }
        }), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'수정 중 오류가 발생했습니다: {str(e)}'}), 500
    finally:
        session.close()


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """
    비밀번호 변경 API
    
    Required fields:
    - user_id: 사용자 ID
    - current_password: 현재 비밀번호
    - new_password: 새 비밀번호
    """
    data = request.json
    
    if not all([data.get('user_id'), data.get('current_password'), data.get('new_password')]):
        return jsonify({'error': '모든 필드를 입력해주세요.'}), 400
    
    # 새 비밀번호 검증
    is_valid, message = validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'error': message}), 400
    
    session = get_session()
    try:
        user = session.query(User).filter(User.id == data['user_id']).first()
        
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        if not verify_password(data['current_password'], user.password_hash):
            return jsonify({'error': '현재 비밀번호가 일치하지 않습니다.'}), 401
        
        user.password_hash = hash_password(data['new_password'])
        session.commit()
        
        return jsonify({'message': '비밀번호가 변경되었습니다.'}), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}'}), 500
    finally:
        session.close()
