"""
GDELT 데이터 파싱 및 필터링 백엔드 모듈
- GDELT Events CSV 파일에서 긴급 이벤트 추출
- GoldsteinScale 기반 위험도 필터링
- 자동 다운로드 및 데이터 관리
"""

import os
import gzip
import csv
import json
import io
import zipfile
import requests
import shutil
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

# GDELT Events CSV 컬럼 인덱스 (0-based)
# 참고: https://blog.gdeltproject.org/gdelt-2-0-data-format-codebook/
COL_GOLDSTEIN_SCALE = 30  # GoldsteinScale
COL_ACTION_GEO_LAT = 56   # ActionGeo_Lat
COL_ACTION_GEO_LONG = 57  # ActionGeo_Long
COL_ACTOR1NAME = 6        # Actor1Name
COL_ACTOR2NAME = 16       # Actor2NAME
COL_EVENT_BASE_TEXT = 60  # EventBaseText (또는 다른 텍스트 필드)
COL_SOURCEURL = 60        # SOURCEURL (실제 CSV는 61개 컬럼, 인덱스 0-60)

# GDELT 다운로드 URL
GDELT_BASE_URL = "http://data.gdeltproject.org/gdeltv2"
GDELT_LASTUPDATE_URL = f"{GDELT_BASE_URL}/lastupdate.txt"

# 기본 GDELT 저장 경로 (프로젝트 내부 data/gdelt로 설정)
# 환경 변수 GDELT_BASE_PATH가 설정되어 있으면 그것을 사용, 없으면 프로젝트 내부 경로 사용
_project_root = Path(__file__).parent.parent
DEFAULT_GDELT_PATH = _project_root / "data" / "gdelt"

def get_gdelt_base_path() -> Path:
    """
    GDELT 기본 경로를 반환합니다.
    환경 변수 GDELT_BASE_PATH가 설정되어 있으면 그것을 사용하고,
    없으면 프로젝트 내부 data/gdelt 경로를 사용합니다.
    """
    env_path = os.getenv("GDELT_BASE_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_GDELT_PATH


def find_latest_gdelt_file(base_path: Path = None) -> Optional[Path]:
    """
    가장 최근의 GDELT Events CSV 파일을 찾습니다.
    
    Args:
        base_path: GDELT 파일이 저장된 기본 경로
        
    Returns:
        가장 최근 파일의 Path 또는 None
    """
    if base_path is None:
        base_path = get_gdelt_base_path()
    
    if not base_path.exists():
        logger.warning(f"GDELT base path does not exist: {base_path}")
        return None
    
    # default/events/YYYYMMDD/ 디렉토리 구조에서 최신 파일 찾기
    events_path = base_path / "default" / "events"
    if not events_path.exists():
        logger.warning(f"GDELT events path does not exist: {events_path}")
        return None
    
    # 날짜 디렉토리 중 가장 최근 것 찾기
    date_dirs = sorted([d for d in events_path.iterdir() if d.is_dir()], reverse=True)
    
    for date_dir in date_dirs:
        # CSV 파일 찾기 (압축 파일 포함)
        csv_files = list(date_dir.glob("*.export.CSV")) + list(date_dir.glob("*.export.CSV.zip"))
        if csv_files:
            # 가장 최근 파일 반환
            latest_file = sorted(csv_files, reverse=True)[0]
            logger.info(f"Found latest GDELT file: {latest_file}")
            return latest_file
    
    logger.warning("No GDELT CSV files found")
    return None


def parse_gdelt_events(
    file_path: Path,
    goldstein_threshold: float = -5.0,
    max_events: int = 1000
) -> List[Dict]:
    """
    GDELT Events CSV 파일을 파싱하여 긴급 이벤트를 추출합니다.
    
    Args:
        file_path: GDELT CSV 파일 경로
        goldstein_threshold: GoldsteinScale 임계값 (이하 값만 추출)
        max_events: 최대 추출할 이벤트 수
        
    Returns:
        이벤트 리스트
    """
    if not file_path or not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []
    
    events = []
    
    try:
        # 파일 열기 (압축 파일 처리)
        if file_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zf:
                # ZIP 내부의 CSV 파일 찾기
                csv_name = [name for name in zf.namelist() if name.endswith('.CSV')][0]
                with zf.open(csv_name) as f:
                    content = io.TextIOWrapper(f, encoding='utf-8', errors='ignore')
                    events = _parse_csv_content(content, goldstein_threshold, max_events)
        elif file_path.suffix.lower() == '.gz':
            with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                events = _parse_csv_content(f, goldstein_threshold, max_events)
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                events = _parse_csv_content(f, goldstein_threshold, max_events)
    
    except Exception as e:
        logger.error(f"Error parsing GDELT file: {e}", exc_info=True)
        return []
    
    logger.info(f"Parsed {len(events)} critical events from {file_path.name}")
    return events


def _parse_csv_content(
    content,
    goldstein_threshold: float,
    max_events: int
) -> List[Dict]:
    """
    CSV 내용을 파싱하여 이벤트 추출
    """
    events = []
    reader = csv.reader(content, delimiter='\t')
    
    for row in reader:
        if len(row) < 61:  # 최소 컬럼 수 확인
            continue
        
        try:
            # GoldsteinScale 확인
            goldstein_scale = float(row[COL_GOLDSTEIN_SCALE])
            if goldstein_scale > goldstein_threshold:
                continue
            
            # 위도/경도 확인
            lat = float(row[COL_ACTION_GEO_LAT]) if row[COL_ACTION_GEO_LAT] else None
            lng = float(row[COL_ACTION_GEO_LONG]) if row[COL_ACTION_GEO_LONG] else None
            
            if lat is None or lng is None:
                continue
            
            # 이벤트 정보 추출 (프론트엔드 형식에 맞춤)
            event = {
                'name': f"{row[COL_ACTOR1NAME]} - {row[COL_ACTOR2NAME]}" if len(row) > COL_ACTOR2NAME else 'Event',
                'actor1': row[COL_ACTOR1NAME] if len(row) > COL_ACTOR1NAME else '',
                'actor2': row[COL_ACTOR2NAME] if len(row) > COL_ACTOR2NAME else '',
                'scale': goldstein_scale,  # 프론트엔드가 기대하는 필드명
                'goldstein_scale': goldstein_scale,  # 하위 호환성
                'lat': lat,  # 프론트엔드가 기대하는 필드명
                'lng': lng,  # 프론트엔드가 기대하는 필드명
                'latitude': lat,  # 하위 호환성
                'longitude': lng,  # 하위 호환성
                'url': row[COL_SOURCEURL] if len(row) > COL_SOURCEURL else '',  # 프론트엔드가 기대하는 필드명
                'source_url': row[COL_SOURCEURL] if len(row) > COL_SOURCEURL else '',  # 하위 호환성
                'event_date': row[1] if len(row) > 1 else '',  # SQLDATE
            }
            
            events.append(event)
            
            if len(events) >= max_events:
                break
        
        except (ValueError, IndexError) as e:
            # 파싱 오류는 무시하고 계속 진행
            continue
    
    return events


def get_critical_alerts(
    goldstein_threshold: float = -5.0,
    max_alerts: int = 1000,
    base_path: Path = None
) -> Dict:
    """
    긴급 알림 데이터를 가져옵니다.
    
    Args:
        goldstein_threshold: GoldsteinScale 임계값
        max_alerts: 최대 알림 수
        base_path: GDELT 데이터 경로
        
    Returns:
        알림 데이터 딕셔너리
    """
    # 최신 GDELT 파일 찾기
    latest_file = find_latest_gdelt_file(base_path)
    
    if not latest_file:
        return {
            'error': 'No GDELT data file found',
            'alerts': [],
            'count': 0,
            'last_updated': None
        }
    
    # 이벤트 파싱
    events = parse_gdelt_events(latest_file, goldstein_threshold, max_alerts)
    
    return {
        'alerts': events,
        'count': len(events),
        'last_updated': datetime.now().isoformat(),
        'file_path': str(latest_file),
        'threshold': goldstein_threshold
    }


# 날짜별로 GDELT 파일 찾기
def find_gdelt_file_by_date(target_date: str, base_path: Path = None) -> Optional[Path]:
    """
    특정 날짜의 GDELT 파일을 찾습니다.
    
    Args:
        target_date: 날짜 (YYYYMMDD 또는 YYYY-MM-DD 형식)
        base_path: GDELT 데이터 경로
        
    Returns:
        파일 Path 또는 None
    """
    if base_path is None:
        base_path = get_gdelt_base_path()
    
    # 날짜 형식 정규화 (YYYYMMDD)
    target_date = target_date.replace('-', '')
    
    events_path = base_path / "default" / "events" / target_date
    
    if not events_path.exists():
        logger.warning(f"Date directory not found: {events_path}")
        return None
    
    # CSV 파일 찾기
    csv_files = list(events_path.glob("*.export.CSV")) + list(events_path.glob("*.export.CSV.zip"))
    
    if csv_files:
        return sorted(csv_files, reverse=True)[0]
    
    return None


def get_alerts_by_date_range(
    start_date: str,
    end_date: str,
    goldstein_threshold: float = -5.0,
    max_alerts: int = 1000,
    base_path: Path = None
) -> Dict:
    """
    날짜 범위 내의 긴급 알림을 가져옵니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        goldstein_threshold: GoldsteinScale 임계값
        max_alerts: 최대 알림 수
        base_path: GDELT 데이터 경로
        
    Returns:
        알림 데이터 딕셔너리
    """
    from datetime import datetime, timedelta
    
    if base_path is None:
        base_path = get_gdelt_base_path()
    
    # 날짜 파싱
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return {
            'error': 'Invalid date format. Use YYYY-MM-DD',
            'alerts': [],
            'count': 0
        }
    
    all_events = []
    current_date = start_dt
    
    # 날짜별로 파일 찾아서 파싱
    while current_date <= end_dt and len(all_events) < max_alerts:
        date_str = current_date.strftime('%Y%m%d')
        file_path = find_gdelt_file_by_date(date_str, base_path)
        
        if file_path:
            events = parse_gdelt_events(
                file_path,
                goldstein_threshold,
                max_alerts - len(all_events)
            )
            all_events.extend(events)
        
        current_date += timedelta(days=1)
    
    return {
        'alerts': all_events,
        'count': len(all_events),
        'date_range': {
            'start': start_date,
            'end': end_date
        },
        'threshold': goldstein_threshold,
        'last_updated': datetime.now().isoformat()
    }


def get_latest_gdelt_file_url() -> Optional[str]:
    """
    GDELT 서버에서 최신 파일 URL을 가져옵니다.
    
    Returns:
        최신 파일 URL 또는 None
    """
    try:
        response = requests.get(GDELT_LASTUPDATE_URL, timeout=10)
        if response.status_code == 200:
            # lastupdate.txt 형식: 
            # 78857 e097bd4fb117a0ca51716cf09f16bea2 http://data.gdeltproject.org/gdeltv2/20251230020000.export.CSV.zip
            lines = response.text.strip().split('\n')
            if lines:
                # 첫 번째 줄에서 마지막 토큰 추출 (이미 전체 URL이 포함됨)
                last_token = lines[0].strip().split()[-1] if lines[0].strip() else None
                if last_token:
                    # 이미 URL이면 그대로 사용, 파일명만이면 BASE_URL 추가
                    if last_token.startswith('http://') or last_token.startswith('https://'):
                        return last_token
                    else:
                        return f"{GDELT_BASE_URL}/{last_token}"
        logger.error(f"Failed to get latest GDELT file URL: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching latest GDELT file URL: {e}")
    return None


def download_gdelt_file(file_url: str = None, base_path: Path = None) -> Optional[Path]:
    """
    GDELT 파일을 다운로드합니다.
    
    Args:
        file_url: 다운로드할 파일 URL (None이면 최신 파일 자동 감지)
        base_path: 저장할 기본 경로
        
    Returns:
        다운로드된 파일의 Path 또는 None
    """
    if base_path is None:
        base_path = get_gdelt_base_path()
    
    # 디렉토리 구조 생성
    base_path.mkdir(parents=True, exist_ok=True)
    events_path = base_path / "default" / "events"
    events_path.mkdir(parents=True, exist_ok=True)
    
    # 최신 파일 URL 가져오기
    if file_url is None:
        file_url = get_latest_gdelt_file_url()
        if not file_url:
            logger.error("Failed to get latest GDELT file URL")
            return None
    
    try:
        # 파일명 추출 (예: 20251229120000.export.CSV.zip)
        file_name = file_url.split('/')[-1]
        
        # 날짜 추출 (YYYYMMDD)
        date_str = file_name[:8]  # 첫 8자리가 날짜
        
        # 날짜별 디렉토리 생성
        date_dir = events_path / date_str
        date_dir.mkdir(exist_ok=True)
        
        # 저장 경로
        save_path = date_dir / file_name
        
        # 이미 파일이 있으면 스킵
        if save_path.exists():
            logger.info(f"File already exists: {save_path}")
            return save_path
        
        # 파일 다운로드
        logger.info(f"Downloading GDELT file: {file_url}")
        response = requests.get(file_url, timeout=60, stream=True)
        response.raise_for_status()
        
        # 파일 저장
        with open(save_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        
        logger.info(f"Downloaded GDELT file: {save_path}")
        return save_path
        
    except Exception as e:
        logger.error(f"Error downloading GDELT file: {e}", exc_info=True)
        return None


def cleanup_old_gdelt_data(base_path: Path = None, keep_days: int = 2) -> int:
    """
    오래된 GDELT 데이터를 삭제합니다.
    UTC 기준으로 오늘과 어제 데이터만 유지하고 나머지는 삭제합니다.
    
    Args:
        base_path: GDELT 데이터 기본 경로
        keep_days: 유지할 일수 (기본값: 2 = 오늘 + 어제)
        
    Returns:
        삭제된 디렉토리 수
    """
    if base_path is None:
        base_path = get_gdelt_base_path()
    
    events_path = base_path / "default" / "events"
    if not events_path.exists():
        return 0
    
    # UTC 기준 오늘 날짜
    utc_now = datetime.now(timezone.utc)
    today = utc_now.date()
    
    # 유지할 날짜 목록 (오늘부터 keep_days-1일 전까지)
    keep_dates = {today - timedelta(days=i) for i in range(keep_days)}
    
    deleted_count = 0
    
    try:
        # 날짜 디렉토리 순회
        for date_dir in events_path.iterdir():
            if not date_dir.is_dir():
                continue
            
            try:
                # 디렉토리명에서 날짜 파싱 (YYYYMMDD)
                dir_date = datetime.strptime(date_dir.name, '%Y%m%d').date()
                
                # 유지할 날짜가 아니면 삭제
                if dir_date not in keep_dates:
                    logger.info(f"Deleting old GDELT data: {date_dir}")
                    shutil.rmtree(date_dir)
                    deleted_count += 1
            except ValueError:
                # 날짜 형식이 아닌 디렉토리는 무시
                logger.warning(f"Skipping invalid date directory: {date_dir.name}")
                continue
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old GDELT data directories")
        
    except Exception as e:
        logger.error(f"Error cleaning up old GDELT data: {e}", exc_info=True)
    
    return deleted_count


def update_gdelt_data() -> Dict:
    """
    GDELT 데이터를 업데이트합니다 (다운로드 + 정리).
    
    Returns:
        업데이트 결과 딕셔너리
    """
    result = {
        'downloaded': False,
        'file_path': None,
        'cleaned_dirs': 0,
        'error': None
    }
    
    try:
        # 최신 파일 다운로드
        downloaded_file = download_gdelt_file()
        if downloaded_file:
            result['downloaded'] = True
            result['file_path'] = str(downloaded_file)
        
        # 오래된 데이터 정리
        deleted_count = cleanup_old_gdelt_data()
        result['cleaned_dirs'] = deleted_count
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Error updating GDELT data: {e}", exc_info=True)
    
    return result

