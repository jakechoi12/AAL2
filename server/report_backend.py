"""
Report & Insight - Backend API (Flask version)
Flask Blueprint for report management
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from typing import List, Optional
from datetime import date, datetime
import uuid
import json

from report_models import (
    ReportDB, BookmarkDB, init_db, get_db, SessionLocal
)

# Create Flask Blueprint
report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


# ============================================
# Helper Functions
# ============================================

def report_to_response(report: ReportDB, is_bookmarked: bool = False) -> dict:
    """Convert DB model to response dict"""
    return {
        "id": report.id,
        "title": report.title,
        "category": report.category,
        "organization": report.organization,
        "published_date": report.published_date.isoformat() if report.published_date else None,
        "summary": report.summary,
        "tags": report.get_tags(),
        "pdf_url": report.pdf_url,
        "thumbnail_url": report.thumbnail_url,
        "is_featured": report.is_featured,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        "is_bookmarked": is_bookmarked
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
        search = request.args.get('search')
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
        
        # Get bookmarked report IDs
        bookmarked_ids = set(
            b.report_id for b in db.query(BookmarkDB).all()
        )
        
        # Convert to response
        report_responses = [
            report_to_response(r, r.id in bookmarked_ids) 
            for r in reports
        ]
        
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
        
        bookmarked_ids = set(b.report_id for b in db.query(BookmarkDB).all())
        
        return jsonify([report_to_response(r, r.id in bookmarked_ids) for r in reports])
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
        # Organizations with counts
        org_counts = db.query(
            ReportDB.organization,
            func.count(ReportDB.id)
        ).group_by(ReportDB.organization).all()
        
        organizations = [
            {"name": org, "count": count}
            for org, count in org_counts
        ]
        
        # Tags with counts
        all_tags = {}
        for report in db.query(ReportDB).all():
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
    """Get single report by ID"""
    db = get_session()
    try:
        report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        
        if not report:
            return jsonify({"error": "Report not found"}), 404
        
        # Check if bookmarked
        is_bookmarked = db.query(BookmarkDB)\
            .filter(BookmarkDB.report_id == report_id)\
            .first() is not None
        
        return jsonify(report_to_response(report, is_bookmarked))
    finally:
        db.close()


@report_bp.route('/<report_id>/related', methods=['GET'])
def get_related_reports(report_id):
    """Get related reports based on category and tags"""
    db = get_session()
    try:
        limit = request.args.get('limit', 4, type=int)
        
        # Get the source report
        report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        
        if not report:
            return jsonify({"error": "Report not found"}), 404
        
        # Find related reports (same category, different ID)
        related = db.query(ReportDB)\
            .filter(ReportDB.category == report.category)\
            .filter(ReportDB.id != report_id)\
            .order_by(desc(ReportDB.published_date))\
            .limit(limit)\
            .all()
        
        bookmarked_ids = set(b.report_id for b in db.query(BookmarkDB).all())
        
        return jsonify([report_to_response(r, r.id in bookmarked_ids) for r in related])
    finally:
        db.close()


@report_bp.route('', methods=['POST'])
def create_report():
    """Create a new report"""
    db = get_session()
    try:
        data = request.get_json()
        
        report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
        
        db_report = ReportDB(
            id=report_id,
            title=data.get('title'),
            category=data.get('category'),
            organization=data.get('organization'),
            published_date=date.fromisoformat(data.get('published_date')) if data.get('published_date') else date.today(),
            summary=data.get('summary'),
            pdf_url=data.get('pdf_url'),
            thumbnail_url=data.get('thumbnail_url'),
            is_featured=data.get('is_featured', False)
        )
        db_report.set_tags(data.get('tags', []))
        
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
        if 'pdf_url' in data:
            db_report.pdf_url = data['pdf_url']
        if 'thumbnail_url' in data:
            db_report.thumbnail_url = data['thumbnail_url']
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
        
        # Delete related bookmarks
        db.query(BookmarkDB).filter(BookmarkDB.report_id == report_id).delete()
        
        db.delete(db_report)
        db.commit()
        
        return jsonify({"message": "Report deleted successfully"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ============================================
# Bookmark Endpoints
# ============================================

@report_bp.route('/bookmarks/list', methods=['GET'])
def get_bookmarks():
    """Get all bookmarked reports"""
    db = get_session()
    try:
        bookmarks = db.query(BookmarkDB).all()
        report_ids = [b.report_id for b in bookmarks]
        
        if not report_ids:
            return jsonify([])
        
        reports = db.query(ReportDB)\
            .filter(ReportDB.id.in_(report_ids))\
            .order_by(desc(ReportDB.published_date))\
            .all()
        
        return jsonify([report_to_response(r, True) for r in reports])
    finally:
        db.close()


@report_bp.route('/bookmarks', methods=['POST'])
def add_bookmark():
    """Add a bookmark"""
    db = get_session()
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        
        # Check if report exists
        report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        if not report:
            return jsonify({"error": "Report not found"}), 404
        
        # Check if already bookmarked
        existing = db.query(BookmarkDB)\
            .filter(BookmarkDB.report_id == report_id)\
            .first()
        
        if existing:
            return jsonify({"error": "Already bookmarked"}), 400
        
        db_bookmark = BookmarkDB(
            id=f"BM-{uuid.uuid4().hex[:8].upper()}",
            report_id=report_id
        )
        
        db.add(db_bookmark)
        db.commit()
        
        return jsonify({"message": "Bookmark added", "id": db_bookmark.id}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@report_bp.route('/bookmarks/<report_id>', methods=['DELETE'])
def remove_bookmark(report_id):
    """Remove a bookmark"""
    db = get_session()
    try:
        bookmark = db.query(BookmarkDB)\
            .filter(BookmarkDB.report_id == report_id)\
            .first()
        
        if not bookmark:
            return jsonify({"error": "Bookmark not found"}), 404
        
        db.delete(bookmark)
        db.commit()
        
        return jsonify({"message": "Bookmark removed"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# Initialize database on module load
init_db()
