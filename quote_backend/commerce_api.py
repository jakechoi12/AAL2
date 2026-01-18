"""
B2B Commerce API Endpoints
FastAPI 라우터 모듈

Company, Product, RFQ, Quotation, Transaction API 제공
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from database import get_db
from commerce_models import (
    Company, CompanyCertification, CommerceUser, Category, Product,
    ProductRFQ, ProductRFQItem, ProductRFQInvitation,
    ProductQuotation, ProductQuotationItem, ProductQuotationRevision,
    ProductTransaction, ProductTransactionItem, ProductTransactionStatusLog,
    CommerceNotification, CommerceMessage
)
from commerce_schemas import (
    # Company
    CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListItem, CompanyListResponse,
    CertificationCreate, CertificationResponse,
    # User
    CommerceUserCreate, CommerceUserUpdate, CommerceUserResponse,
    # Category
    CategoryCreate, CategoryResponse, CategoryTreeItem,
    # Product
    ProductCreate, ProductUpdate, ProductResponse, ProductListItem, ProductListResponse,
    # RFQ
    ProductRFQCreate, ProductRFQUpdate, ProductRFQResponse, ProductRFQListItem, ProductRFQListResponse,
    RFQItemCreate, RFQItemResponse,
    # Quotation
    ProductQuotationCreate, ProductQuotationUpdate, ProductQuotationResponse,
    ProductQuotationListItem, ProductQuotationListResponse,
    QuotationItemCreate, QuotationItemResponse,
    QuotationComparisonItem, QuotationComparisonResponse,
    # Transaction
    ProductTransactionCreate, ProductTransactionResponse,
    ProductTransactionListItem, ProductTransactionListResponse,
    TransactionStatusUpdate,
    # Notification & Message
    CommerceNotificationResponse, CommerceNotificationListResponse,
    CommerceMessageCreate, CommerceMessageResponse, CommerceMessageThreadResponse,
    # Dashboard
    CompanyDashboardStats, RFQStats,
    # AI
    AIRFQDraftRequest, AIRFQDraftResponse,
    AIQuotationDraftRequest, AIQuotationDraftResponse,
    # Common
    APIResponse
)

import bcrypt


# ==========================================
# ROUTER SETUP
# ==========================================

router = APIRouter(prefix="/api/commerce", tags=["B2B Commerce"])


# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def generate_rfq_number() -> str:
    """RFQ 번호 생성: RFQ-YYYYMMDD-XXXX"""
    today = datetime.now().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"RFQ-{today}-{random_suffix}"


def generate_quotation_number() -> str:
    """견적 번호 생성: QT-YYYYMMDD-XXXX"""
    today = datetime.now().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"QT-{today}-{random_suffix}"


def generate_transaction_number() -> str:
    """거래 번호 생성: TX-YYYYMMDD-XXXX"""
    today = datetime.now().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"TX-{today}-{random_suffix}"


def hash_password(password: str) -> str:
    """비밀번호 해시"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """비밀번호 검증"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# ==========================================
# COMPANY ENDPOINTS
# ==========================================

@router.post("/companies", response_model=CompanyResponse, status_code=201)
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    """기업 등록"""
    company = Company(
        id=str(uuid.uuid4()),
        **data.model_dump()
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/companies", response_model=CompanyListResponse)
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_type: Optional[str] = None,
    country_code: Optional[str] = None,
    industry_code: Optional[str] = None,
    verification_status: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db)
):
    """기업 목록 조회"""
    query = db.query(Company).filter(Company.is_active == True)
    
    # Filters
    if company_type:
        query = query.filter(Company.company_type == company_type)
    if country_code:
        query = query.filter(Company.country_code == country_code)
    if industry_code:
        query = query.filter(Company.industry_code == industry_code)
    if verification_status:
        query = query.filter(Company.verification_status == verification_status)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Company.company_name.ilike(search_term),
                Company.company_name_en.ilike(search_term),
                Company.description.ilike(search_term)
            )
        )
    
    # Sorting
    sort_column = getattr(Company, sort, Company.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Pagination
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    companies = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return CompanyListResponse(
        companies=[CompanyListItem.model_validate(c) for c in companies],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: str, db: Session = Depends(get_db)):
    """기업 상세 조회"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/companies/{company_id}", response_model=CompanyResponse)
def update_company(company_id: str, data: CompanyUpdate, db: Session = Depends(get_db)):
    """기업 정보 수정"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)
    
    db.commit()
    db.refresh(company)
    return company


@router.delete("/companies/{company_id}")
def delete_company(company_id: str, db: Session = Depends(get_db)):
    """기업 비활성화 (소프트 삭제)"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.is_active = False
    db.commit()
    return {"message": "Company deactivated"}


# ==========================================
# CERTIFICATION ENDPOINTS
# ==========================================

@router.post("/companies/{company_id}/certifications", response_model=CertificationResponse, status_code=201)
def add_certification(company_id: str, data: CertificationCreate, db: Session = Depends(get_db)):
    """기업 인증 추가"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    cert = CompanyCertification(
        id=str(uuid.uuid4()),
        company_id=company_id,
        **data.model_dump(exclude={"company_id"})
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


@router.get("/companies/{company_id}/certifications", response_model=List[CertificationResponse])
def list_certifications(company_id: str, db: Session = Depends(get_db)):
    """기업 인증 목록 조회"""
    certs = db.query(CompanyCertification).filter(
        CompanyCertification.company_id == company_id
    ).all()
    return certs


# ==========================================
# CATEGORY ENDPOINTS
# ==========================================

@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    """카테고리 생성"""
    # Check for duplicate code
    existing = db.query(Category).filter(Category.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category code already exists")
    
    category = Category(
        id=str(uuid.uuid4()),
        **data.model_dump()
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    level: Optional[int] = None,
    parent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """카테고리 목록 조회"""
    query = db.query(Category).filter(Category.is_active == True)
    
    if level is not None:
        query = query.filter(Category.level == level)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    
    return query.order_by(Category.sort_order).all()


@router.get("/categories/tree", response_model=List[CategoryTreeItem])
def get_category_tree(db: Session = Depends(get_db)):
    """카테고리 트리 조회"""
    categories = db.query(Category).filter(
        Category.is_active == True
    ).order_by(Category.level, Category.sort_order).all()
    
    # Build tree structure
    category_map = {c.id: {
        "id": c.id,
        "code": c.code,
        "name_ko": c.name_ko,
        "name_en": c.name_en,
        "level": c.level,
        "children": []
    } for c in categories}
    
    tree = []
    for cat in categories:
        if cat.parent_id and cat.parent_id in category_map:
            category_map[cat.parent_id]["children"].append(category_map[cat.id])
        elif not cat.parent_id:
            tree.append(category_map[cat.id])
    
    return tree


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: str, db: Session = Depends(get_db)):
    """카테고리 상세 조회"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


# ==========================================
# PRODUCT ENDPOINTS
# ==========================================

@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    """상품 등록"""
    # Verify company exists
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    product = Product(
        id=str(uuid.uuid4()),
        **data.model_dump()
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: Optional[str] = None,
    category_id: Optional[str] = None,
    price_type: Optional[str] = None,
    origin_country: Optional[str] = None,
    search: Optional[str] = None,
    is_featured: Optional[bool] = None,
    sort: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db)
):
    """상품 목록 조회"""
    query = db.query(Product).filter(Product.is_active == True)
    
    # Filters
    if company_id:
        query = query.filter(Product.company_id == company_id)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if price_type:
        query = query.filter(Product.price_type == price_type)
    if origin_country:
        query = query.filter(Product.origin_country == origin_country)
    if is_featured is not None:
        query = query.filter(Product.is_featured == is_featured)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name_ko.ilike(search_term),
                Product.name_en.ilike(search_term),
                Product.description.ilike(search_term),
                Product.sku.ilike(search_term)
            )
        )
    
    # Sorting
    sort_column = getattr(Product, sort, Product.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Pagination
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    products = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Add company and category names
    result = []
    for p in products:
        item = ProductListItem.model_validate(p)
        if p.company:
            item.company_name = p.company.company_name
        if p.category:
            item.category_name = p.category.name_ko
        result.append(item)
    
    return ProductListResponse(
        products=result,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """상품 상세 조회"""
    product = db.query(Product).options(
        joinedload(Product.company),
        joinedload(Product.category)
    ).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Increment view count
    product.view_count += 1
    db.commit()
    
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, data: ProductUpdate, db: Session = Depends(get_db)):
    """상품 정보 수정"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)):
    """상품 비활성화"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = False
    db.commit()
    return {"message": "Product deactivated"}


# ==========================================
# RFQ ENDPOINTS
# ==========================================

@router.post("/rfqs", response_model=ProductRFQResponse, status_code=201)
def create_rfq(data: ProductRFQCreate, db: Session = Depends(get_db)):
    """RFQ 생성"""
    # Verify company exists
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Create RFQ
    rfq_data = data.model_dump(exclude={"items", "invited_company_ids"})
    rfq = ProductRFQ(
        id=str(uuid.uuid4()),
        rfq_number=generate_rfq_number(),
        status="draft",
        **rfq_data
    )
    db.add(rfq)
    db.flush()
    
    # Add items
    for i, item_data in enumerate(data.items, start=1):
        item = ProductRFQItem(
            id=str(uuid.uuid4()),
            rfq_id=rfq.id,
            item_number=i,
            **item_data.model_dump()
        )
        db.add(item)
    
    # Add invitations for private/invited RFQs
    if data.invited_company_ids and data.visibility in ["private", "invited"]:
        for inv_company_id in data.invited_company_ids:
            invitation = ProductRFQInvitation(
                id=str(uuid.uuid4()),
                rfq_id=rfq.id,
                company_id=inv_company_id,
                status="pending"
            )
            db.add(invitation)
    
    db.commit()
    db.refresh(rfq)
    return rfq


@router.get("/rfqs", response_model=ProductRFQListResponse)
def list_rfqs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: Optional[str] = None,
    rfq_type: Optional[str] = None,
    status: Optional[str] = None,
    visibility: Optional[str] = None,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db)
):
    """RFQ 목록 조회"""
    query = db.query(ProductRFQ)
    
    # Filters
    if company_id:
        query = query.filter(ProductRFQ.company_id == company_id)
    if rfq_type:
        query = query.filter(ProductRFQ.rfq_type == rfq_type)
    if status:
        query = query.filter(ProductRFQ.status == status)
    if visibility:
        query = query.filter(ProductRFQ.visibility == visibility)
    if category_id:
        query = query.filter(ProductRFQ.category_id == category_id)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ProductRFQ.title.ilike(search_term),
                ProductRFQ.description.ilike(search_term),
                ProductRFQ.rfq_number.ilike(search_term)
            )
        )
    
    # Sorting
    sort_column = getattr(ProductRFQ, sort, ProductRFQ.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Pagination
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    rfqs = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Build response
    result = []
    for r in rfqs:
        item = ProductRFQListItem(
            id=r.id,
            rfq_number=r.rfq_number,
            rfq_type=r.rfq_type,
            title=r.title,
            visibility=r.visibility,
            status=r.status,
            category_id=r.category_id,
            company_id=r.company_id,
            deadline=r.deadline,
            quotation_count=r.quotation_count,
            created_at=r.created_at
        )
        if r.company:
            item.company_name = r.company.company_name
        if r.category:
            item.category_name = r.category.name_ko
        result.append(item)
    
    return ProductRFQListResponse(
        rfqs=result,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/rfqs/{rfq_id}", response_model=ProductRFQResponse)
def get_rfq(rfq_id: str, db: Session = Depends(get_db)):
    """RFQ 상세 조회"""
    rfq = db.query(ProductRFQ).options(
        joinedload(ProductRFQ.items),
        joinedload(ProductRFQ.company),
        joinedload(ProductRFQ.category)
    ).filter(ProductRFQ.id == rfq_id).first()
    
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Increment view count
    rfq.view_count += 1
    db.commit()
    
    return rfq


@router.put("/rfqs/{rfq_id}", response_model=ProductRFQResponse)
def update_rfq(rfq_id: str, data: ProductRFQUpdate, db: Session = Depends(get_db)):
    """RFQ 수정"""
    rfq = db.query(ProductRFQ).filter(ProductRFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    if rfq.status not in ["draft"]:
        raise HTTPException(status_code=400, detail="Can only update draft RFQs")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rfq, key, value)
    
    db.commit()
    db.refresh(rfq)
    return rfq


@router.post("/rfqs/{rfq_id}/publish", response_model=ProductRFQResponse)
def publish_rfq(rfq_id: str, db: Session = Depends(get_db)):
    """RFQ 게시 (draft -> open)"""
    rfq = db.query(ProductRFQ).filter(ProductRFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    if rfq.status != "draft":
        raise HTTPException(status_code=400, detail="Can only publish draft RFQs")
    
    # Validate RFQ has items
    if not rfq.items or len(rfq.items) == 0:
        raise HTTPException(status_code=400, detail="RFQ must have at least one item")
    
    rfq.status = "open"
    rfq.published_at = datetime.utcnow()
    db.commit()
    db.refresh(rfq)
    return rfq


@router.post("/rfqs/{rfq_id}/close", response_model=ProductRFQResponse)
def close_rfq(rfq_id: str, db: Session = Depends(get_db)):
    """RFQ 마감 (open -> closed)"""
    rfq = db.query(ProductRFQ).filter(ProductRFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    if rfq.status != "open":
        raise HTTPException(status_code=400, detail="Can only close open RFQs")
    
    rfq.status = "closed"
    rfq.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(rfq)
    return rfq


@router.post("/rfqs/{rfq_id}/cancel", response_model=ProductRFQResponse)
def cancel_rfq(rfq_id: str, db: Session = Depends(get_db)):
    """RFQ 취소"""
    rfq = db.query(ProductRFQ).filter(ProductRFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    if rfq.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel this RFQ")
    
    rfq.status = "cancelled"
    rfq.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(rfq)
    return rfq


# ==========================================
# QUOTATION ENDPOINTS
# ==========================================

@router.post("/quotations", response_model=ProductQuotationResponse, status_code=201)
def create_quotation(data: ProductQuotationCreate, db: Session = Depends(get_db)):
    """견적 생성"""
    # Verify RFQ exists and is open
    rfq = db.query(ProductRFQ).filter(ProductRFQ.id == data.rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq.status != "open":
        raise HTTPException(status_code=400, detail="RFQ is not open for quotations")
    
    # Verify company exists
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if company already submitted quotation
    existing = db.query(ProductQuotation).filter(
        ProductQuotation.rfq_id == data.rfq_id,
        ProductQuotation.company_id == data.company_id,
        ProductQuotation.status != "expired"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already submitted a quotation for this RFQ")
    
    # Create quotation
    quot_data = data.model_dump(exclude={"items"})
    quotation = ProductQuotation(
        id=str(uuid.uuid4()),
        quotation_number=generate_quotation_number(),
        status="draft",
        **quot_data
    )
    db.add(quotation)
    db.flush()
    
    # Add items and calculate total
    total = 0
    for i, item_data in enumerate(data.items, start=1):
        amount = float(item_data.quantity) * float(item_data.unit_price)
        item = ProductQuotationItem(
            id=str(uuid.uuid4()),
            quotation_id=quotation.id,
            item_number=i,
            amount=amount,
            **item_data.model_dump()
        )
        db.add(item)
        total += amount
    
    quotation.total_amount = total
    
    db.commit()
    db.refresh(quotation)
    return quotation


@router.get("/quotations", response_model=ProductQuotationListResponse)
def list_quotations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rfq_id: Optional[str] = None,
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db)
):
    """견적 목록 조회"""
    query = db.query(ProductQuotation)
    
    # Filters
    if rfq_id:
        query = query.filter(ProductQuotation.rfq_id == rfq_id)
    if company_id:
        query = query.filter(ProductQuotation.company_id == company_id)
    if status:
        query = query.filter(ProductQuotation.status == status)
    
    # Sorting
    sort_column = getattr(ProductQuotation, sort, ProductQuotation.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Pagination
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    quotations = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Build response
    result = []
    for q in quotations:
        item = ProductQuotationListItem(
            id=q.id,
            quotation_number=q.quotation_number,
            rfq_id=q.rfq_id,
            company_id=q.company_id,
            status=q.status,
            total_amount=float(q.total_amount) if q.total_amount else None,
            currency=q.currency,
            valid_until=q.valid_until,
            created_at=q.created_at,
            submitted_at=q.submitted_at
        )
        if q.rfq:
            item.rfq_number = q.rfq.rfq_number
            item.rfq_title = q.rfq.title
        if q.company:
            item.company_name = q.company.company_name
        result.append(item)
    
    return ProductQuotationListResponse(
        quotations=result,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/quotations/{quotation_id}", response_model=ProductQuotationResponse)
def get_quotation(quotation_id: str, db: Session = Depends(get_db)):
    """견적 상세 조회"""
    quotation = db.query(ProductQuotation).options(
        joinedload(ProductQuotation.items),
        joinedload(ProductQuotation.company)
    ).filter(ProductQuotation.id == quotation_id).first()
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    return quotation


@router.put("/quotations/{quotation_id}", response_model=ProductQuotationResponse)
def update_quotation(quotation_id: str, data: ProductQuotationUpdate, db: Session = Depends(get_db)):
    """견적 수정"""
    quotation = db.query(ProductQuotation).filter(ProductQuotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status not in ["draft"]:
        raise HTTPException(status_code=400, detail="Can only update draft quotations")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(quotation, key, value)
    
    db.commit()
    db.refresh(quotation)
    return quotation


@router.post("/quotations/{quotation_id}/submit", response_model=ProductQuotationResponse)
def submit_quotation(quotation_id: str, db: Session = Depends(get_db)):
    """견적 제출 (draft -> submitted)"""
    quotation = db.query(ProductQuotation).filter(ProductQuotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status != "draft":
        raise HTTPException(status_code=400, detail="Can only submit draft quotations")
    
    # Validate quotation has items
    if not quotation.items or len(quotation.items) == 0:
        raise HTTPException(status_code=400, detail="Quotation must have at least one item")
    
    quotation.status = "submitted"
    quotation.submitted_at = datetime.utcnow()
    
    # Update RFQ quotation count
    rfq = db.query(ProductRFQ).filter(ProductRFQ.id == quotation.rfq_id).first()
    if rfq:
        rfq.quotation_count += 1
    
    db.commit()
    db.refresh(quotation)
    return quotation


@router.post("/quotations/{quotation_id}/accept", response_model=ProductTransactionResponse)
def accept_quotation(quotation_id: str, db: Session = Depends(get_db)):
    """견적 수락 -> 거래 생성"""
    quotation = db.query(ProductQuotation).options(
        joinedload(ProductQuotation.items)
    ).filter(ProductQuotation.id == quotation_id).first()
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status not in ["submitted", "viewed", "negotiating"]:
        raise HTTPException(status_code=400, detail="Cannot accept this quotation")
    
    # Get RFQ
    rfq = db.query(ProductRFQ).filter(ProductRFQ.id == quotation.rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Determine buyer and seller based on RFQ type
    if rfq.rfq_type == "buy":
        buyer_company_id = rfq.company_id
        seller_company_id = quotation.company_id
    else:
        buyer_company_id = quotation.company_id
        seller_company_id = rfq.company_id
    
    # Create transaction
    transaction = ProductTransaction(
        id=str(uuid.uuid4()),
        transaction_number=generate_transaction_number(),
        rfq_id=rfq.id,
        quotation_id=quotation.id,
        buyer_company_id=buyer_company_id,
        seller_company_id=seller_company_id,
        status="confirmed",
        total_amount=quotation.total_amount,
        currency=quotation.currency,
        incoterms=quotation.incoterms,
        payment_terms=quotation.payment_terms,
        delivery_date=quotation.delivery_date,
        destination_port=rfq.destination_port,
        origin_port=rfq.origin_port
    )
    db.add(transaction)
    db.flush()
    
    # Copy items to transaction
    for i, qitem in enumerate(quotation.items, start=1):
        titem = ProductTransactionItem(
            id=str(uuid.uuid4()),
            transaction_id=transaction.id,
            quotation_item_id=qitem.id,
            product_id=qitem.product_id,
            item_number=i,
            name=qitem.name,
            specifications=qitem.specifications,
            quantity=qitem.quantity,
            unit=qitem.unit,
            unit_price=qitem.unit_price,
            amount=qitem.amount
        )
        db.add(titem)
    
    # Update quotation status
    quotation.status = "accepted"
    
    # Reject other quotations for this RFQ
    other_quotations = db.query(ProductQuotation).filter(
        ProductQuotation.rfq_id == rfq.id,
        ProductQuotation.id != quotation.id,
        ProductQuotation.status.in_(["submitted", "viewed", "negotiating"])
    ).all()
    for oq in other_quotations:
        oq.status = "rejected"
    
    # Update RFQ status
    rfq.status = "completed"
    rfq.closed_at = datetime.utcnow()
    
    # Add status log
    status_log = ProductTransactionStatusLog(
        id=str(uuid.uuid4()),
        transaction_id=transaction.id,
        from_status=None,
        to_status="confirmed",
        change_reason="Quotation accepted"
    )
    db.add(status_log)
    
    # Update company stats
    buyer = db.query(Company).filter(Company.id == buyer_company_id).first()
    seller = db.query(Company).filter(Company.id == seller_company_id).first()
    if buyer:
        buyer.total_transactions += 1
        buyer.total_trade_volume += float(transaction.total_amount)
    if seller:
        seller.total_transactions += 1
        seller.total_trade_volume += float(transaction.total_amount)
    
    db.commit()
    db.refresh(transaction)
    return transaction


@router.post("/quotations/{quotation_id}/reject")
def reject_quotation(quotation_id: str, db: Session = Depends(get_db)):
    """견적 거절"""
    quotation = db.query(ProductQuotation).filter(ProductQuotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.status not in ["submitted", "viewed", "negotiating"]:
        raise HTTPException(status_code=400, detail="Cannot reject this quotation")
    
    quotation.status = "rejected"
    db.commit()
    return {"message": "Quotation rejected"}


@router.get("/rfqs/{rfq_id}/comparison", response_model=QuotationComparisonResponse)
def get_quotation_comparison(rfq_id: str, db: Session = Depends(get_db)):
    """RFQ 견적 비교"""
    rfq = db.query(ProductRFQ).filter(ProductRFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    quotations = db.query(ProductQuotation).options(
        joinedload(ProductQuotation.items),
        joinedload(ProductQuotation.company)
    ).filter(
        ProductQuotation.rfq_id == rfq_id,
        ProductQuotation.status.in_(["submitted", "viewed", "negotiating"])
    ).order_by(ProductQuotation.total_amount).all()
    
    if not quotations:
        return QuotationComparisonResponse(
            rfq_id=rfq.id,
            rfq_number=rfq.rfq_number,
            rfq_title=rfq.title,
            quotations=[],
            total_quotations=0,
            lowest_price=0,
            highest_price=0,
            avg_price=0
        )
    
    prices = [float(q.total_amount) for q in quotations if q.total_amount]
    lowest = min(prices) if prices else 0
    highest = max(prices) if prices else 0
    avg_price = sum(prices) / len(prices) if prices else 0
    
    comparison_items = []
    for i, q in enumerate(quotations, start=1):
        price = float(q.total_amount) if q.total_amount else 0
        price_diff = ((price - lowest) / lowest * 100) if lowest > 0 else 0
        
        item = QuotationComparisonItem(
            quotation_id=q.id,
            quotation_number=q.quotation_number,
            company_id=q.company_id,
            company_name=q.company.company_name if q.company else "",
            trust_score=float(q.company.trust_score) if q.company else 3.0,
            total_amount=price,
            currency=q.currency,
            incoterms=q.incoterms,
            payment_terms=q.payment_terms,
            delivery_date=q.delivery_date,
            lead_time=q.lead_time,
            valid_until=q.valid_until,
            item_count=len(q.items) if q.items else 0,
            price_rank=i,
            price_diff_pct=round(price_diff, 2)
        )
        comparison_items.append(item)
    
    return QuotationComparisonResponse(
        rfq_id=rfq.id,
        rfq_number=rfq.rfq_number,
        rfq_title=rfq.title,
        quotations=comparison_items,
        total_quotations=len(quotations),
        lowest_price=lowest,
        highest_price=highest,
        avg_price=round(avg_price, 2)
    )


# ==========================================
# TRANSACTION ENDPOINTS
# ==========================================

@router.get("/transactions", response_model=ProductTransactionListResponse)
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,  # "buyer" or "seller"
    sort: str = "created_at",
    order: str = "desc",
    db: Session = Depends(get_db)
):
    """거래 목록 조회"""
    query = db.query(ProductTransaction)
    
    # Filters
    if company_id:
        if role == "buyer":
            query = query.filter(ProductTransaction.buyer_company_id == company_id)
        elif role == "seller":
            query = query.filter(ProductTransaction.seller_company_id == company_id)
        else:
            query = query.filter(
                or_(
                    ProductTransaction.buyer_company_id == company_id,
                    ProductTransaction.seller_company_id == company_id
                )
            )
    if status:
        query = query.filter(ProductTransaction.status == status)
    
    # Sorting
    sort_column = getattr(ProductTransaction, sort, ProductTransaction.created_at)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Pagination
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    transactions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Build response
    result = []
    for t in transactions:
        item = ProductTransactionListItem(
            id=t.id,
            transaction_number=t.transaction_number,
            rfq_id=t.rfq_id,
            buyer_company_id=t.buyer_company_id,
            seller_company_id=t.seller_company_id,
            status=t.status,
            total_amount=float(t.total_amount),
            currency=t.currency,
            delivery_date=t.delivery_date,
            created_at=t.created_at
        )
        if t.rfq:
            item.rfq_number = t.rfq.rfq_number
        if t.buyer_company:
            item.buyer_company_name = t.buyer_company.company_name
        if t.seller_company:
            item.seller_company_name = t.seller_company.company_name
        result.append(item)
    
    return ProductTransactionListResponse(
        transactions=result,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/transactions/{transaction_id}", response_model=ProductTransactionResponse)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """거래 상세 조회"""
    transaction = db.query(ProductTransaction).options(
        joinedload(ProductTransaction.buyer_company),
        joinedload(ProductTransaction.seller_company),
        joinedload(ProductTransaction.items)
    ).filter(ProductTransaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.put("/transactions/{transaction_id}/status", response_model=ProductTransactionResponse)
def update_transaction_status(
    transaction_id: str,
    data: TransactionStatusUpdate,
    db: Session = Depends(get_db)
):
    """거래 상태 업데이트"""
    transaction = db.query(ProductTransaction).filter(ProductTransaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Add status log
    status_log = ProductTransactionStatusLog(
        id=str(uuid.uuid4()),
        transaction_id=transaction.id,
        from_status=transaction.status,
        to_status=data.status.value,
        change_reason=data.reason
    )
    db.add(status_log)
    
    # Update status
    old_status = transaction.status
    transaction.status = data.status.value
    
    # Handle completion
    if data.status.value == "completed":
        transaction.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(transaction)
    return transaction


# ==========================================
# DASHBOARD ENDPOINTS
# ==========================================

@router.get("/dashboard/{company_id}/stats", response_model=CompanyDashboardStats)
def get_dashboard_stats(company_id: str, db: Session = Depends(get_db)):
    """기업 대시보드 통계"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # RFQ stats
    total_rfqs = db.query(ProductRFQ).filter(ProductRFQ.company_id == company_id).count()
    open_rfqs = db.query(ProductRFQ).filter(
        ProductRFQ.company_id == company_id,
        ProductRFQ.status == "open"
    ).count()
    
    # Quotation stats
    total_quotations_sent = db.query(ProductQuotation).filter(
        ProductQuotation.company_id == company_id
    ).count()
    
    # Quotations received (for RFQs owned by this company)
    rfq_ids = db.query(ProductRFQ.id).filter(ProductRFQ.company_id == company_id).subquery()
    total_quotations_received = db.query(ProductQuotation).filter(
        ProductQuotation.rfq_id.in_(rfq_ids)
    ).count()
    
    pending_quotations = db.query(ProductQuotation).filter(
        ProductQuotation.company_id == company_id,
        ProductQuotation.status == "draft"
    ).count()
    
    # Transaction stats
    active_transactions = db.query(ProductTransaction).filter(
        or_(
            ProductTransaction.buyer_company_id == company_id,
            ProductTransaction.seller_company_id == company_id
        ),
        ProductTransaction.status.in_(["confirmed", "contract_pending", "payment_pending", "paid", "shipping"])
    ).count()
    
    completed_transactions = db.query(ProductTransaction).filter(
        or_(
            ProductTransaction.buyer_company_id == company_id,
            ProductTransaction.seller_company_id == company_id
        ),
        ProductTransaction.status == "completed"
    ).count()
    
    return CompanyDashboardStats(
        total_rfqs=total_rfqs,
        open_rfqs=open_rfqs,
        total_quotations_sent=total_quotations_sent,
        total_quotations_received=total_quotations_received,
        pending_quotations=pending_quotations,
        active_transactions=active_transactions,
        completed_transactions=completed_transactions,
        total_trade_volume=float(company.total_trade_volume),
        trust_score=float(company.trust_score),
        response_rate=float(company.response_rate)
    )


# ==========================================
# NOTIFICATION ENDPOINTS
# ==========================================

@router.get("/notifications", response_model=CommerceNotificationListResponse)
def list_notifications(
    user_id: str = Query(...),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """알림 목록 조회"""
    notifications = db.query(CommerceNotification).filter(
        CommerceNotification.user_id == user_id
    ).order_by(desc(CommerceNotification.created_at)).limit(limit).all()
    
    unread_count = db.query(CommerceNotification).filter(
        CommerceNotification.user_id == user_id,
        CommerceNotification.is_read == False
    ).count()
    
    return CommerceNotificationListResponse(
        notifications=[CommerceNotificationResponse.model_validate(n) for n in notifications],
        total=len(notifications),
        unread_count=unread_count
    )


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db)):
    """알림 읽음 처리"""
    notification = db.query(CommerceNotification).filter(
        CommerceNotification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    return {"message": "Notification marked as read"}


# ==========================================
# MESSAGE ENDPOINTS
# ==========================================

@router.post("/messages", response_model=CommerceMessageResponse, status_code=201)
def send_message(data: CommerceMessageCreate, sender_user_id: str = Query(...), db: Session = Depends(get_db)):
    """메시지 전송"""
    sender = db.query(CommerceUser).filter(CommerceUser.id == sender_user_id).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")
    
    message = CommerceMessage(
        id=str(uuid.uuid4()),
        sender_company_id=sender.company_id,
        sender_user_id=sender_user_id,
        **data.model_dump()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return CommerceMessageResponse.model_validate(message)


@router.get("/messages/thread", response_model=CommerceMessageThreadResponse)
def get_message_thread(
    rfq_id: Optional[str] = None,
    quotation_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
    company_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """메시지 스레드 조회"""
    query = db.query(CommerceMessage)
    
    if rfq_id:
        query = query.filter(CommerceMessage.rfq_id == rfq_id)
    elif quotation_id:
        query = query.filter(CommerceMessage.quotation_id == quotation_id)
    elif transaction_id:
        query = query.filter(CommerceMessage.transaction_id == transaction_id)
    else:
        raise HTTPException(status_code=400, detail="Must specify rfq_id, quotation_id, or transaction_id")
    
    # Filter by company (sender or recipient)
    query = query.filter(
        or_(
            CommerceMessage.sender_company_id == company_id,
            CommerceMessage.recipient_company_id == company_id
        )
    )
    
    messages = query.order_by(CommerceMessage.created_at).all()
    
    # Mark received messages as read
    for msg in messages:
        if msg.recipient_company_id == company_id and not msg.is_read:
            msg.is_read = True
            msg.read_at = datetime.utcnow()
    db.commit()
    
    return CommerceMessageThreadResponse(
        messages=[CommerceMessageResponse.model_validate(m) for m in messages],
        total=len(messages)
    )


# ==========================================
# AI ENDPOINTS (Placeholder)
# ==========================================

@router.post("/ai/rfq-draft", response_model=AIRFQDraftResponse)
def generate_rfq_draft(data: AIRFQDraftRequest, db: Session = Depends(get_db)):
    """AI RFQ 초안 생성 (Placeholder)"""
    # TODO: Implement AI integration
    return AIRFQDraftResponse(
        title=f"[AI Generated] {data.prompt[:50]}...",
        description=f"Based on your request: {data.prompt}\n\nPlease review and modify as needed.",
        items=[
            RFQItemCreate(
                name="Sample Item 1",
                quantity=100,
                unit="EA",
                specifications={"note": "Please specify details"}
            )
        ],
        suggested_incoterms="FOB",
        suggested_payment_terms="T/T 30%/70%",
        suggested_deadline_days=14,
        ai_notes="This is a placeholder response. AI integration pending."
    )


@router.post("/ai/quotation-draft", response_model=AIQuotationDraftResponse)
def generate_quotation_draft(data: AIQuotationDraftRequest, db: Session = Depends(get_db)):
    """AI 견적 초안 생성 (Placeholder)"""
    # Get RFQ for reference
    rfq = db.query(ProductRFQ).options(
        joinedload(ProductRFQ.items)
    ).filter(ProductRFQ.id == data.rfq_id).first()
    
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Generate placeholder items based on RFQ items
    items = []
    for rfq_item in rfq.items:
        items.append(QuotationItemCreate(
            rfq_item_id=rfq_item.id,
            name=rfq_item.name,
            quantity=float(rfq_item.quantity),
            unit=rfq_item.unit,
            unit_price=float(rfq_item.target_price) if rfq_item.target_price else 10.0,
            specifications=rfq_item.specifications
        ))
    
    return AIQuotationDraftResponse(
        items=items,
        suggested_incoterms=rfq.incoterms or "FOB",
        suggested_payment_terms=rfq.payment_terms or "T/T 30%/70%",
        suggested_lead_time=14,
        ai_notes="This is a placeholder response. AI integration pending."
    )

