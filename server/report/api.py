"""
Report & Insight - Backend API (Flask version)
Flask Blueprint for report management
MVP Version: No Auth/Bookmarks, PDF download from DB
"""

from flask import Blueprint, request, jsonify, Response
from sqlalchemy import func, or_, desc, asc
from datetime import date
import uuid

from .models import ReportDB, ReportFileDB, init_db, SessionLocal

# Create Flask Blueprint
report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


# ============================================
# Helper Functions
# ============================================

def report_to_response(report: ReportDB, include_file: bool = True) -> dict:
    """Convert DB model to response dict"""
    response = {
        "id": report.id,
        "title": report.title,
        "category": report.category,
        "organization": report.organization,
        "published_date": report.published_date.isoformat() if report.published_date else None,
        "summary": report.summary,
        "tags": report.get_tags(),
        "key_insights": report.get_key_insights(),
        "canonical_url": report.canonical_url,
        "is_featured": report.is_featured,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    }
    
    # Add file info if available
    if include_file and report.files:
        file = report.files[0]  # Get first file
        response["file"] = {
            "file_name": file.file_name,
            "download_url": f"/api/reports/{report.id}/download"
        }
        response["has_pdf"] = True
    else:
        response["file"] = None
        response["has_pdf"] = bool(report.files) if hasattr(report, 'files') else False
    
    return response


def report_to_list_item(report: ReportDB) -> dict:
    """Convert DB model to list item (lighter response)"""
    return {
        "id": report.id,
        "title": report.title,
        "category": report.category,
        "organization": report.organization,
        "published_date": report.published_date.isoformat() if report.published_date else None,
        "summary": report.summary,
        "tags": report.get_tags(),
        "is_featured": report.is_featured,
        "has_pdf": bool(report.files) if hasattr(report, 'files') else False
    }


def get_session():
    """Get a new database session"""
    return SessionLocal()


# ============================================
# Report Endpoints
# ============================================

@report_bp.route('', methods=['GET'])
def get_reports():
    """Get paginated list of reports with filters"""
    db = get_session()
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 12, type=int)
        category = request.args.get('category')
        organization = request.args.get('organization')
        tags = request.args.get('tags')  # Comma-separated
        search = request.args.get('search') or request.args.get('q')  # Support both
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        sort = request.args.get('sort', 'newest')
        
        # Base query
        query = db.query(ReportDB)
        
        # Apply filters
        if category and category != 'all':
            query = query.filter(ReportDB.category == category)
        
        if organization:
            query = query.filter(ReportDB.organization == organization)
        
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            for tag in tag_list:
                query = query.filter(ReportDB.tags.contains(tag))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    ReportDB.title.ilike(search_term),
                    ReportDB.summary.ilike(search_term),
                    ReportDB.organization.ilike(search_term),
                    ReportDB.tags.ilike(search_term)
                )
            )
        
        if date_from:
            query = query.filter(ReportDB.published_date >= date.fromisoformat(date_from))
        
        if date_to:
            query = query.filter(ReportDB.published_date <= date.fromisoformat(date_to))
        
        # Apply sorting
        if sort == 'newest':
            query = query.order_by(desc(ReportDB.published_date))
        elif sort == 'oldest':
            query = query.order_by(asc(ReportDB.published_date))
        elif sort == 'title':
            query = query.order_by(asc(ReportDB.title))
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        offset = (page - 1) * page_size
        
        # Get reports
        reports = query.offset(offset).limit(page_size).all()
        
        # Convert to response
        report_responses = [report_to_list_item(r) for r in reports]
        
        return jsonify({
            "reports": report_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        })
    finally:
        db.close()


@report_bp.route('/featured', methods=['GET'])
def get_featured_reports():
    """Get featured reports"""
    db = get_session()
    try:
        limit = request.args.get('limit', 3, type=int)
        
        reports = db.query(ReportDB)\
            .filter(ReportDB.is_featured == True)\
            .order_by(desc(ReportDB.published_date))\
            .limit(limit)\
            .all()
        
        return jsonify([report_to_list_item(r) for r in reports])
    finally:
        db.close()


@report_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get report statistics"""
    db = get_session()
    try:
        # Total reports
        total = db.query(ReportDB).count()
        
        # Unique organizations
        orgs = db.query(func.count(func.distinct(ReportDB.organization))).scalar() or 0
        
        # This month
        today = date.today()
        first_of_month = date(today.year, today.month, 1)
        this_month = db.query(ReportDB)\
            .filter(ReportDB.published_date >= first_of_month)\
            .count()
        
        # Category counts
        categories = db.query(
            ReportDB.category,
            func.count(ReportDB.id)
        ).group_by(ReportDB.category).all()
        
        category_counts = [
            {"category": cat, "count": count}
            for cat, count in categories
        ]
        
        return jsonify({
            "total_reports": total,
            "total_organizations": orgs,
            "this_month": this_month,
            "category_counts": category_counts
        })
    finally:
        db.close()


@report_bp.route('/filters', methods=['GET'])
def get_filters():
    """Get available filter options"""
    db = get_session()
    try:
        category = request.args.get('category')
        
        # Base query for filtering
        base_query = db.query(ReportDB)
        if category and category != 'all':
            base_query = base_query.filter(ReportDB.category == category)
        
        # Organizations with counts
        org_counts = db.query(
            ReportDB.organization,
            func.count(ReportDB.id)
        )
        if category and category != 'all':
            org_counts = org_counts.filter(ReportDB.category == category)
        org_counts = org_counts.group_by(ReportDB.organization).all()
        
        organizations = [
            {"name": org, "count": count}
            for org, count in sorted(org_counts, key=lambda x: -x[1])
        ]
        
        # Tags with counts
        all_tags = {}
        for report in base_query.all():
            for tag in report.get_tags():
                all_tags[tag] = all_tags.get(tag, 0) + 1
        
        tags = [
            {"name": tag, "count": count}
            for tag, count in sorted(all_tags.items(), key=lambda x: -x[1])
        ]
        
        return jsonify({
            "organizations": organizations,
            "tags": tags
        })
    finally:
        db.close()


@report_bp.route('/<report_id>', methods=['GET'])
def get_report(report_id):
    """Get single report by ID with full details"""
    db = get_session()
    try:
        report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        
        if not report:
            return jsonify({"error": "Report not found"}), 404
        
        return jsonify(report_to_response(report, include_file=True))
    finally:
        db.close()


@report_bp.route('/<report_id>/download', methods=['GET'])
def download_report(report_id):
    """Download PDF file for a report"""
    from urllib.parse import quote
    
    db = get_session()
    try:
        # Get the report file
        file = db.query(ReportFileDB)\
            .filter(ReportFileDB.report_id == report_id)\
            .first()
        
        if not file:
            return jsonify({"error": "PDF file not found for this report"}), 404
        
        # Encode filename for Content-Disposition (RFC 5987)
        # Use both filename (ASCII fallback) and filename* (UTF-8)
        ascii_filename = file.file_name.encode('ascii', 'ignore').decode('ascii') or 'report.pdf'
        encoded_filename = quote(file.file_name)
        
        # Return the PDF as binary response
        return Response(
            file.file_bytes,
            mimetype=file.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{encoded_filename}",
                "Content-Length": str(file.file_size)
            }
        )
    finally:
        db.close()


@report_bp.route('/<report_id>/related', methods=['GET'])
def get_related_reports(report_id):
    """
    Get related reports based on MVP logic:
    1. Same category_key
    2. Same source/organization (if category allows)
    3. Tag overlap
    4. published_at DESC
    5. Max 6
    6. Exclude self
    """
    db = get_session()
    try:
        limit = request.args.get('limit', 6, type=int)
        
        # Get the source report
        report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        
        if not report:
            return jsonify({"error": "Report not found"}), 404
        
        related_ids = set()
        related_reports = []
        
        # Priority 1: Same category, different ID, newest first
        same_category = db.query(ReportDB)\
            .filter(ReportDB.category == report.category)\
            .filter(ReportDB.id != report_id)\
            .order_by(desc(ReportDB.published_date))\
            .limit(limit)\
            .all()
        
        for r in same_category:
            if r.id not in related_ids and len(related_reports) < limit:
                related_ids.add(r.id)
                related_reports.append(r)
        
        # Priority 2: Same organization if not enough
        if len(related_reports) < limit:
            same_org = db.query(ReportDB)\
                .filter(ReportDB.organization == report.organization)\
                .filter(ReportDB.id != report_id)\
                .filter(~ReportDB.id.in_(related_ids))\
                .order_by(desc(ReportDB.published_date))\
                .limit(limit - len(related_reports))\
                .all()
            
            for r in same_org:
                if r.id not in related_ids and len(related_reports) < limit:
                    related_ids.add(r.id)
                    related_reports.append(r)
        
        # Priority 3: Tag overlap if still not enough
        if len(related_reports) < limit:
            report_tags = report.get_tags()
            if report_tags:
                # Find reports with any matching tag
                for tag in report_tags:
                    if len(related_reports) >= limit:
                        break
                    tag_matches = db.query(ReportDB)\
                        .filter(ReportDB.tags.contains(tag))\
                        .filter(ReportDB.id != report_id)\
                        .filter(~ReportDB.id.in_(related_ids))\
                        .order_by(desc(ReportDB.published_date))\
                        .limit(limit - len(related_reports))\
                        .all()
                    
                    for r in tag_matches:
                        if r.id not in related_ids and len(related_reports) < limit:
                            related_ids.add(r.id)
                            related_reports.append(r)
        
        return jsonify([report_to_list_item(r) for r in related_reports])
    finally:
        db.close()


@report_bp.route('', methods=['POST'])
def create_report():
    """Create a new report (for admin/seed purposes)"""
    db = get_session()
    try:
        data = request.get_json()
        
        report_id = data.get('id') or f"RPT-{uuid.uuid4().hex[:8].upper()}"
        
        db_report = ReportDB(
            id=report_id,
            title=data.get('title'),
            category=data.get('category'),
            organization=data.get('organization'),
            published_date=date.fromisoformat(data.get('published_date')) if data.get('published_date') else date.today(),
            summary=data.get('summary'),
            canonical_url=data.get('canonical_url'),
            is_featured=data.get('is_featured', False)
        )
        db_report.set_tags(data.get('tags', []))
        db_report.set_key_insights(data.get('key_insights', []))
        
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        return jsonify(report_to_response(db_report)), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@report_bp.route('/<report_id>', methods=['PUT'])
def update_report(report_id):
    """Update an existing report"""
    db = get_session()
    try:
        db_report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        
        if not db_report:
            return jsonify({"error": "Report not found"}), 404
        
        data = request.get_json()
        
        if 'title' in data:
            db_report.title = data['title']
        if 'category' in data:
            db_report.category = data['category']
        if 'organization' in data:
            db_report.organization = data['organization']
        if 'published_date' in data:
            db_report.published_date = date.fromisoformat(data['published_date'])
        if 'summary' in data:
            db_report.summary = data['summary']
        if 'tags' in data:
            db_report.set_tags(data['tags'])
        if 'key_insights' in data:
            db_report.set_key_insights(data['key_insights'])
        if 'canonical_url' in data:
            db_report.canonical_url = data['canonical_url']
        if 'is_featured' in data:
            db_report.is_featured = data['is_featured']
        
        db.commit()
        db.refresh(db_report)
        
        return jsonify(report_to_response(db_report))
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@report_bp.route('/<report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Delete a report"""
    db = get_session()
    try:
        db_report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        
        if not db_report:
            return jsonify({"error": "Report not found"}), 404
        
        # Files are deleted automatically via cascade
        db.delete(db_report)
        db.commit()
        
        return jsonify({"message": "Report deleted successfully"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# Initialize database on module load
init_db()

