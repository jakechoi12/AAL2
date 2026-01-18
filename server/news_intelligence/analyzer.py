"""
News Analyzer Module (Optimized Version)

Provides AI-powered analysis for news articles with optimization:
1. Rule-based first + AI supplementary (reduces API calls by ~70%)
2. Batch processing (10 articles per API call)
3. Designed for async background processing

Categories: Crisis, Ocean, Air, Inland, Economy, ETC

v2.5: Migrated from OpenAI to Google Gemini
"""

import os
import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Try to import Google Gemini (new google-genai package)
GEMINI_AVAILABLE = False
genai_client = None

try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        logger.info("Gemini API (google-genai) configured successfully for news analysis")
    else:
        logger.warning("GEMINI_API_KEY not found. AI analysis will use fallback methods.")
except ImportError:
    logger.warning("google-genai package not installed. AI analysis will use fallback methods.")


# ===== 일반 키워드 필터링 강화 (v2.3) =====
# 워드클라우드에서 제외할 일반적인 업계 용어

STOP_WORDS = {
    # English common words
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used',
    'and', 'but', 'or', 'nor', 'for', 'yet', 'so', 'as', 'at', 'by', 'in',
    'of', 'on', 'to', 'up', 'out', 'with', 'from', 'into', 'through',
    'this', 'that', 'these', 'those', 'it', 'its',
    'what', 'which', 'who', 'whom', 'whose', 'when', 'where', 'why', 'how',
    'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'not', 'only', 'same', 'than', 'too', 'very',
    'about', 'after', 'before', 'over', 'under', 'again', 'further',
    'then', 'once', 'here', 'there', 'any', 'own', 'just', 'now',
    
    # Logistics-generic words (too common) - 강화
    'logistics', 'company', 'market', 'industry', 'business', 'report',
    'news', 'says', 'said', 'new', 'year', 'month', 'week', 'day',
    'percent', 'million', 'billion', 'according', 'also', 'however',
    'freight', 'shipping', 'port', 'container', 'cargo', 'trade',
    'import', 'export', 'supply', 'chain', 'supply chain',
    'service', 'services', 'global', 'world', 'international',
    'first', 'second', 'last', 'next', 'latest', 'recent', 'today',
    'growth', 'increase', 'decrease', 'change', 'expected', 'announced',
    'quarter', 'half', 'annual', 'monthly', 'weekly', 'daily',
    'total', 'number', 'amount', 'level', 'rate', 'rates',
    
    # GDELT-specific terms
    'goldstein', 'goldstein scale', 'average tone', 'avg tone', 'mentions',
    'sources', 'articles', 'material conflict', 'verbal conflict',
    'material cooperation', 'verbal cooperation', 'category', 'event',
    'location', 'involves', 'unknown',
    
    # 조사/관사 구문 필터링 (v2.4)
    'in 2025', 'in 2026', 'in 2024', 'in the', 'to the', 'of the',
    'port of', 'the post', 'at the', 'on the', 'for the', 'by the',
    'from the', 'with the', 'as the', 'will be', 'has been', 'have been',
    
    # Korean common words - 확장
    '있다', '하다', '되다', '이다', '있는', '하는', '되는', '대한', '위한', '통해',
    '따르면', '것으로', '지난', '오는', '관련', '등', '및', '위해', '대해', '있어',
    '물류', '해운', '항만', '컨테이너', '수출', '수입', '무역', '화물', '운송', '공급망',
    '뉴스', '기사', '보도', '전망', '올해', '내년', '지난해', '상반기', '하반기',
    '것으로', '밝혔다', '전했다', '보도했다', '알려졌다', '나타났다',
    '증가', '감소', '상승', '하락', '유지', '기록', '달성', '예상', '전년',
}

# Country code mappings
COUNTRY_CODES = {
    # Major logistics countries
    'united states': 'US', 'usa': 'US', 'u.s.': 'US', 'america': 'US', 'american': 'US',
    'china': 'CN', 'chinese': 'CN', 'prc': 'CN',
    'korea': 'KR', 'south korea': 'KR', 'korean': 'KR', '한국': 'KR', '대한민국': 'KR',
    'japan': 'JP', 'japanese': 'JP', '일본': 'JP',
    'germany': 'DE', 'german': 'DE',
    'netherlands': 'NL', 'dutch': 'NL', 'rotterdam': 'NL', 'amsterdam': 'NL',
    'uk': 'GB', 'united kingdom': 'GB', 'britain': 'GB', 'british': 'GB', 'england': 'GB',
    'singapore': 'SG', 'singaporean': 'SG',
    'hong kong': 'HK',
    'taiwan': 'TW', 'taiwanese': 'TW',
    'vietnam': 'VN', 'vietnamese': 'VN',
    'india': 'IN', 'indian': 'IN',
    'indonesia': 'ID', 'indonesian': 'ID',
    'malaysia': 'MY', 'malaysian': 'MY',
    'thailand': 'TH', 'thai': 'TH',
    'philippines': 'PH', 'filipino': 'PH',
    'australia': 'AU', 'australian': 'AU',
    'canada': 'CA', 'canadian': 'CA',
    'mexico': 'MX', 'mexican': 'MX',
    'brazil': 'BR', 'brazilian': 'BR',
    'russia': 'RU', 'russian': 'RU',
    'france': 'FR', 'french': 'FR',
    'italy': 'IT', 'italian': 'IT',
    'spain': 'ES', 'spanish': 'ES',
    'belgium': 'BE', 'belgian': 'BE', 'antwerp': 'BE',
    'egypt': 'EG', 'egyptian': 'EG', 'suez': 'EG',
    'panama': 'PA', 'panamanian': 'PA',
    'uae': 'AE', 'dubai': 'AE', 'emirates': 'AE',
    'saudi arabia': 'SA', 'saudi': 'SA',
    'israel': 'IL', 'israeli': 'IL',
    'turkey': 'TR', 'turkish': 'TR',
    'ukraine': 'UA', 'ukrainian': 'UA',
    'yemen': 'YE', 'yemeni': 'YE',
    'iran': 'IR', 'iranian': 'IR',
    'greece': 'GR', 'greek': 'GR',
    # Major ports and regions
    'los angeles': 'US', 'long beach': 'US', 'new york': 'US', 'savannah': 'US',
    'shanghai': 'CN', 'shenzhen': 'CN', 'ningbo': 'CN', 'guangzhou': 'CN', 'qingdao': 'CN',
    'busan': 'KR', '부산': 'KR', '인천': 'KR', 'incheon': 'KR',
    'hamburg': 'DE', 'bremerhaven': 'DE',
    'felixstowe': 'GB', 'southampton': 'GB',
    'le havre': 'FR', 'marseille': 'FR',
    'genoa': 'IT', 'gioia tauro': 'IT',
    'valencia': 'ES', 'barcelona': 'ES', 'algeciras': 'ES',
    'piraeus': 'GR',
    'tanjung pelepas': 'MY', 'port klang': 'MY',
    'laem chabang': 'TH',
    'ho chi minh': 'VN', 'hai phong': 'VN',
    'red sea': 'REGION', 'suez canal': 'EG', 'panama canal': 'PA',
    'strait of malacca': 'REGION', 'south china sea': 'REGION',
}

# Category keyword configurations with weights
CATEGORY_KEYWORDS = {
    'Crisis': {
        'high': ['strike', 'crisis', 'disruption', 'accident', 'conflict', 'war', 'disaster',
                 '파업', '위기', '사고', '재난', '마비', '폐쇄', '충돌'],
        'medium': ['delay', 'closure', 'shortage', 'congestion', 'storm', 'attack', 'threat',
                   'suspend', 'halt', 'emergency', '지연', '혼잡', '부족', '중단', '긴급'],
        'low': ['cancel', 'reduce', 'impact', 'severe', '취소', '피해', '위험']
    },
    'Ocean': {
        'high': ['shipping', 'maritime', 'port', 'container', 'vessel', 'liner', 'berth',
                 '해운', '항만', '컨테이너', '선박', '해상', '부두'],
        'medium': ['sea freight', 'bulk', 'tanker', 'cargo ship', 'terminal', 'dock',
                   '터미널', '선적', '하역'],
        'low': ['ocean', 'carrier', 'fleet', '운항', '정박']
    },
    'Air': {
        'high': ['air cargo', 'air freight', 'airline', 'airport', 'aviation',
                 '항공화물', '항공운송', '공항', '화물기'],
        'medium': ['aircraft', 'cargo plane', 'flight', 'freighter', '항공', '비행'],
        'low': ['airway', 'air transport', '여객기']
    },
    'Inland': {
        'high': ['truck', 'rail', 'warehouse', 'distribution center', 'logistics center',
                 '트럭', '철도', '물류센터', '창고', '배송센터'],
        'medium': ['inland', 'ground transport', 'trucking', 'railway', 'intermodal',
                   '내륙', '육상운송', '물류단지'],
        'low': ['delivery', 'last mile', '배송', '운송']
    },
    'Economy': {
        'high': ['freight rate', 'tariff', 'trade war', 'inflation', 'recession',
                 '운임', '관세', '무역전쟁', '인플레이션'],
        'medium': ['rate', 'price', 'demand', 'supply', 'trade', 'economy', 'market', 'index',
                   '가격', '수요', '공급', '무역', '경제', '시장'],
        'low': ['growth', 'cost', 'profit', '성장', '비용', '수익']
    }
}


class NewsAnalyzer:
    """
    Optimized AI-powered news analyzer for logistics intelligence.
    
    Optimization strategy:
    1. Rule-based first: Analyze with keywords/rules first
    2. AI supplementary: Only use AI for uncertain classifications
    3. Batch processing: Process multiple articles in one API call
    
    v2.5: Uses Google Gemini instead of OpenAI
    """
    
    CATEGORIES = ['Crisis', 'Ocean', 'Air', 'Inland', 'Economy', 'ETC']
    
    # Confidence threshold - articles below this need AI verification
    CONFIDENCE_THRESHOLD = 0.6
    
    # Batch size for AI processing
    BATCH_SIZE = 10
    
    def __init__(self, model: str = 'gemini-2.0-flash'):
        """
        Initialize analyzer.
        
        Args:
            model: Gemini model to use (default: gemini-2.0-flash)
        """
        self.model_name = model
        self.client = genai_client  # Use global client
        
        if GEMINI_AVAILABLE and self.client:
            logger.info(f"Gemini analyzer ready with model: {self.model_name}")
        else:
            logger.warning("Gemini not available, using rule-based analysis only")
        
        self.logger = logging.getLogger(__name__)
        
        # Statistics for monitoring
        self.stats = {
            'rule_based_count': 0,
            'ai_count': 0,
            'batch_count': 0,
        }
    
    def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single article using rule-based first approach.
        
        Args:
            article: Article dictionary with 'title' and 'content_summary'
            
        Returns:
            Analysis results including category, country_tags, keywords, is_crisis
        """
        title = article.get('title', '')
        summary = article.get('content_summary', '')
        text = f"{title} {summary}".strip()
        
        if not text:
            return {
                'category': 'ETC',
                'country_tags': [],
                'keywords': [],
                'is_crisis': False,
                'confidence': 1.0,
                'analysis_method': 'empty',
            }
        
        # Step 1: Rule-based analysis first (fast, no API cost)
        rule_result, confidence = self._analyze_with_rules_scored(title, summary)
        
        # Step 2: If confidence is high enough, use rule-based result
        if confidence >= self.CONFIDENCE_THRESHOLD:
            self.stats['rule_based_count'] += 1
            rule_result['confidence'] = confidence
            rule_result['analysis_method'] = 'rule_based'
            return rule_result
        
        # Step 3: Low confidence - use AI if available
        if self.client:
            try:
                self.stats['ai_count'] += 1
                ai_result = self._analyze_with_ai(title, summary)
                ai_result['confidence'] = 0.9  # AI typically high confidence
                ai_result['analysis_method'] = 'ai_gemini'
                return ai_result
            except Exception as e:
                self.logger.error(f"AI analysis failed, using rule-based: {e}")
        
        # Fallback to rule-based result
        rule_result['confidence'] = confidence
        rule_result['analysis_method'] = 'rule_based_fallback'
        return rule_result
    
    def analyze_batch(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze a batch of articles with optimized processing.
        
        Uses rule-based first, then batches uncertain articles for AI.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of articles with analysis results added
        """
        results = []
        needs_ai = []  # Articles that need AI analysis
        
        # Step 1: Rule-based analysis for all articles
        for i, article in enumerate(articles):
            title = article.get('title', '')
            summary = article.get('content_summary', '')
            text = f"{title} {summary}".strip()
            
            if not text:
                article.update({
                    'category': 'ETC',
                    'country_tags': [],
                    'keywords': [],
                    'is_crisis': False,
                    'confidence': 1.0,
                    'analysis_method': 'empty',
                })
                results.append(article)
                continue
            
            rule_result, confidence = self._analyze_with_rules_scored(title, summary)
            
            if confidence >= self.CONFIDENCE_THRESHOLD:
                # High confidence - use rule-based result
                self.stats['rule_based_count'] += 1
                article.update(rule_result)
                article['confidence'] = confidence
                article['analysis_method'] = 'rule_based'
                results.append(article)
            else:
                # Low confidence - queue for AI analysis
                article['_rule_result'] = rule_result
                article['_confidence'] = confidence
                needs_ai.append((i, article))
                results.append(article)  # Placeholder
        
        # Step 2: Batch AI analysis for uncertain articles
        if needs_ai and self.client:
            self.logger.info(f"Processing {len(needs_ai)} articles with Gemini (batch mode)")
            self._batch_ai_analysis(needs_ai, results)
        else:
            # No AI available - use rule-based results
            for i, article in needs_ai:
                rule_result = article.pop('_rule_result', {})
                confidence = article.pop('_confidence', 0.5)
                article.update(rule_result)
                article['confidence'] = confidence
                article['analysis_method'] = 'rule_based_fallback'
        
        return results
    
    def _analyze_with_rules_scored(self, title: str, summary: str) -> Tuple[Dict[str, Any], float]:
        """
        Rule-based analysis with confidence score.
        
        Returns:
            Tuple of (analysis_result, confidence_score)
        """
        text = f"{title} {summary}".lower()
        
        # Category detection with confidence
        category, cat_confidence = self._detect_category_scored(text)
        
        # Country detection
        countries = self._detect_countries(text)
        
        # Keyword extraction
        keywords = self._extract_keywords(text)
        
        # Crisis detection
        is_crisis = self._detect_crisis(text)
        
        # Overall confidence based on category confidence and data richness
        overall_confidence = cat_confidence
        if countries:
            overall_confidence += 0.1
        if keywords:
            overall_confidence += 0.1
        overall_confidence = min(overall_confidence, 1.0)
        
        return {
            'category': category,
            'country_tags': countries[:5],
            'keywords': keywords[:5],
            'is_crisis': is_crisis,
        }, overall_confidence
    
    def _detect_category_scored(self, text: str) -> Tuple[str, float]:
        """Detect category with confidence score"""
        scores = {}
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = 0
            score += sum(3 for k in keywords.get('high', []) if k in text)
            score += sum(2 for k in keywords.get('medium', []) if k in text)
            score += sum(1 for k in keywords.get('low', []) if k in text)
            scores[category] = score
        
        # Find best category
        max_category = max(scores, key=scores.get)
        max_score = scores[max_category]
        
        if max_score == 0:
            return 'ETC', 0.3  # Low confidence for ETC
        
        # Calculate confidence based on score and separation from others
        total_score = sum(scores.values())
        if total_score > 0:
            confidence = max_score / total_score
            # Boost confidence if there's clear separation
            if max_score >= 6:
                confidence = min(confidence + 0.2, 0.95)
            elif max_score >= 3:
                confidence = min(confidence + 0.1, 0.85)
        else:
            confidence = 0.3
        
        return max_category, confidence
    
    def _detect_countries(self, text: str) -> List[str]:
        """Extract country codes from text"""
        found_countries = []
        
        for keyword, code in COUNTRY_CODES.items():
            if keyword in text and code != 'REGION' and code not in found_countries:
                found_countries.append(code)
        
        return found_countries
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple word frequency analysis
        words = re.findall(r'\b[a-z가-힣]{3,}\b', text.lower())
        
        # Filter stop words
        words = [w for w in words if w not in STOP_WORDS]
        
        # Count frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:5]]
    
    def _detect_crisis(self, text: str) -> bool:
        """Detect if article is about crisis/disruption"""
        crisis_indicators = [
            'strike', 'crisis', 'disruption', 'delay', 'accident', 'conflict',
            'war', 'closure', 'shortage', 'congestion', 'disaster', 'storm',
            'attack', 'threat', 'suspend', 'halt', 'emergency', 'severe',
            '파업', '위기', '지연', '사고', '혼잡', '부족', '마비', '폐쇄',
            '중단', '긴급', '재난', '피해', '위험'
        ]
        
        return any(indicator in text for indicator in crisis_indicators)
    
    def _batch_ai_analysis(self, articles_to_analyze: List[Tuple[int, Dict]], results: List[Dict]):
        """
        Process articles in batches using AI.
        
        Args:
            articles_to_analyze: List of (index, article) tuples
            results: Results list to update in-place
        """
        # Process in batches of BATCH_SIZE
        for batch_start in range(0, len(articles_to_analyze), self.BATCH_SIZE):
            batch = articles_to_analyze[batch_start:batch_start + self.BATCH_SIZE]
            
            try:
                batch_results = self._analyze_batch_with_ai(batch)
                self.stats['batch_count'] += 1
                
                # Update results
                for (idx, article), ai_result in zip(batch, batch_results):
                    # Clean up temporary fields
                    article.pop('_rule_result', None)
                    article.pop('_confidence', None)
                    
                    article.update(ai_result)
                    article['confidence'] = 0.9
                    article['analysis_method'] = 'ai_gemini_batch'
                    results[idx] = article
                    
            except Exception as e:
                self.logger.error(f"Batch AI analysis failed: {e}")
                # Fallback to rule-based for this batch
                for idx, article in batch:
                    rule_result = article.pop('_rule_result', {})
                    confidence = article.pop('_confidence', 0.5)
                    article.update(rule_result)
                    article['confidence'] = confidence
                    article['analysis_method'] = 'rule_based_fallback'
                    results[idx] = article
    
    def _analyze_batch_with_ai(self, batch: List[Tuple[int, Dict]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple articles in a single AI API call using Gemini (google-genai).
        
        Args:
            batch: List of (index, article) tuples
            
        Returns:
            List of analysis results
        """
        # Build batch prompt
        articles_text = []
        for i, (idx, article) in enumerate(batch):
            title = article.get('title', '')[:100]
            summary = article.get('content_summary', '')[:200]
            articles_text.append(f"[{i}] Title: {title}\nContent: {summary}")
        
        prompt = f"""You are a logistics news analyst. Analyze these {len(batch)} logistics news articles. For each, provide:
- category: One of [Crisis, Ocean, Air, Inland, Economy, ETC]
- countries: ISO 2-letter country codes mentioned (max 3)
- keywords: 3 important keywords
- is_crisis: true if about supply chain disruption

Articles:
{chr(10).join(articles_text)}

Respond ONLY with a valid JSON array (no markdown, no explanation):
[{{"id": 0, "category": "...", "countries": ["XX"], "keywords": ["..."], "is_crisis": false}}, ...]"""

        # Use new google-genai API
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 1000,
            }
        )
        result_text = response.text.strip()
        
        # Parse JSON response (remove markdown code blocks if present)
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        results = json.loads(result_text)
        
        # Convert to list of analysis dicts
        analysis_results = []
        for i in range(len(batch)):
            # Find result for this article
            article_result = next((r for r in results if r.get('id') == i), None)
            
            if article_result:
                analysis_results.append({
                    'category': article_result.get('category', 'ETC'),
                    'country_tags': article_result.get('countries', [])[:5],
                    'keywords': article_result.get('keywords', [])[:5],
                    'is_crisis': article_result.get('is_crisis', False),
                })
            else:
                # Fallback if result not found
                analysis_results.append({
                    'category': 'ETC',
                    'country_tags': [],
                    'keywords': [],
                    'is_crisis': False,
                })
        
        return analysis_results
    
    def _analyze_with_ai(self, title: str, summary: str) -> Dict[str, Any]:
        """
        Analyze single article using Gemini API (google-genai).
        """
        prompt = f"""You are a logistics news analyst. Analyze this logistics news article and provide:
1. Category: One of [Crisis, Ocean, Air, Inland, Economy, ETC]
2. Countries: List of ISO 2-letter country codes mentioned (max 5)
3. Keywords: 3-5 important keywords/phrases
4. Is Crisis: true if about supply chain disruption

Title: {title}
Content: {summary}

Respond ONLY with valid JSON (no markdown, no explanation):
{{"category": "...", "countries": ["XX", "YY"], "keywords": ["word1", "word2"], "is_crisis": true/false}}"""
        
        # Use new google-genai API
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 200,
            }
        )
        result_text = response.text.strip()
        
        # Parse JSON response (remove markdown code blocks if present)
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        
        return {
            'category': result.get('category', 'ETC'),
            'country_tags': result.get('countries', [])[:5],
            'keywords': result.get('keywords', [])[:5],
            'is_crisis': result.get('is_crisis', False),
        }
    
    def _analyze_with_rules(self, title: str, summary: str) -> Dict[str, Any]:
        """Backward compatible rule-based analysis"""
        result, _ = self._analyze_with_rules_scored(title, summary)
        return result
    
    def generate_crisis_summary(self, crisis_articles: List[Dict[str, Any]], max_articles: int = 5) -> str:
        """
        Generate a summary of current crisis/critical alerts using Gemini.
        """
        if not crisis_articles:
            return "No critical alerts at this time."
        
        articles_to_summarize = crisis_articles[:max_articles]
        
        if self.client:
            try:
                return self._generate_summary_with_ai(articles_to_summarize)
            except Exception as e:
                self.logger.error(f"Gemini summary failed, using fallback: {e}")
        
        # Fallback: Simple list format
        summaries = []
        for article in articles_to_summarize:
            title = article.get('title', 'Unknown')
            source = article.get('source_name', '')
            summaries.append(f"• {title} ({source})")
        
        return "\n".join(summaries)
    
    def _generate_summary_with_ai(self, articles: List[Dict[str, Any]]) -> str:
        """Generate crisis summary using Gemini (google-genai)"""
        articles_text = "\n".join([
            f"- {a.get('title', '')}: {a.get('content_summary', '')[:200]}"
            for a in articles
        ])
        
        prompt = f"""You are a logistics crisis analyst. Summarize these logistics crisis alerts in 2-3 concise bullet points.
Focus on: What happened, where, and potential supply chain impact.

Articles:
{articles_text}

Provide a brief, actionable summary for logistics professionals. Be concise and actionable."""

        # Use new google-genai API
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "temperature": 0.5,
                "max_output_tokens": 300,
            }
        )
        return response.text.strip()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        total = self.stats['rule_based_count'] + self.stats['ai_count']
        return {
            'total_analyzed': total,
            'rule_based_count': self.stats['rule_based_count'],
            'ai_count': self.stats['ai_count'],
            'batch_count': self.stats['batch_count'],
            'ai_reduction_percent': round(
                (self.stats['rule_based_count'] / total * 100) if total > 0 else 0, 1
            ),
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'rule_based_count': 0,
            'ai_count': 0,
            'batch_count': 0,
        }
    
    def extract_keywords_for_wordcloud(self, articles: List[Dict[str, Any]], max_keywords: int = 100) -> Dict[str, int]:
        """
        Extract keywords from articles for word cloud visualization.
        
        v2.4 개선:
        - 2-3단어 구문(bigram/trigram) 추출
        - 조사/관사 필터링
        - 키워드 수 50개 → 100개
        - 우선순위: trigram > bigram > 고유명사 > 이슈 키워드
        
        Args:
            articles: 분석할 기사 목록
            max_keywords: 반환할 최대 키워드 수 (기본 100)
            
        Returns:
            키워드와 빈도수 딕셔너리
        """
        word_freq = {}
        bigram_freq = {}
        trigram_freq = {}
        
        for article in articles:
            title = article.get('title', '')
            summary = article.get('content_summary', '')
            text = f"{title} {summary}".strip()
            
            if not text:
                continue
            
            # Extract n-grams
            words = self._tokenize_for_ngrams(text)
            
            # 단일 단어 추출
            for word in words:
                if self._is_valid_keyword(word):
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Bigram 추출 (2단어 구문)
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                if self._is_valid_ngram(bigram, words[i], words[i+1]):
                    bigram_freq[bigram] = bigram_freq.get(bigram, 0) + 1
            
            # Trigram 추출 (3단어 구문)
            for i in range(len(words) - 2):
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                if self._is_valid_trigram(trigram, words[i], words[i+1], words[i+2]):
                    trigram_freq[trigram] = trigram_freq.get(trigram, 0) + 1
            
            # 기사에 이미 추출된 키워드가 있으면 가중치 추가
            keywords = article.get('keywords', [])
            for keyword in keywords:
                keyword = keyword.lower().strip()
                if keyword and self._is_valid_keyword(keyword):
                    word_freq[keyword] = word_freq.get(keyword, 0) + 2  # 가중치 2
        
        # 결과 통합 및 우선순위 적용
        result = {}
        
        # 1. Trigram 우선 (중요한 이슈)
        for trigram, freq in sorted(trigram_freq.items(), key=lambda x: x[1], reverse=True):
            if freq >= 2 and len(result) < max_keywords // 3:  # 최소 2회 이상 등장
                result[trigram] = freq * 3  # 가중치 3
        
        # 2. Bigram (구체적 사건/현상)
        for bigram, freq in sorted(bigram_freq.items(), key=lambda x: x[1], reverse=True):
            if freq >= 2 and len(result) < max_keywords * 2 // 3:
                # 이미 trigram에 포함된 bigram은 제외
                if not any(bigram in t for t in result.keys()):
                    result[bigram] = freq * 2  # 가중치 2
        
        # 3. 단일 단어
        for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True):
            if freq >= 2 and len(result) < max_keywords:
                # 이미 bigram/trigram에 포함된 단어는 낮은 우선순위
                if not any(word in ng for ng in result.keys()):
                    result[word] = freq
        
        return result
    
    def _tokenize_for_ngrams(self, text: str) -> List[str]:
        """텍스트를 n-gram 추출을 위해 토큰화"""
        # 소문자 변환 및 정규화
        text = text.lower()
        
        # 특수문자 제거 (하이픈은 유지)
        text = re.sub(r'[^\w\s\-가-힣]', ' ', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 토큰화
        words = text.split()
        
        # 너무 짧은 단어 제거 (2글자 이하)
        words = [w for w in words if len(w) > 2 or re.match(r'^[가-힣]+$', w)]
        
        return words
    
    def _is_valid_keyword(self, word: str) -> bool:
        """유효한 키워드인지 확인"""
        if not word or len(word) < 2:
            return False
        if word in STOP_WORDS:
            return False
        if word.isdigit():
            return False
        return True
    
    def _is_valid_ngram(self, ngram: str, word1: str, word2: str) -> bool:
        """유효한 bigram인지 확인"""
        # 불용어로 시작하거나 끝나는 bigram 제외
        filler_words = {'the', 'a', 'an', 'of', 'in', 'to', 'for', 'at', 'by', 'on', 'is', 'are', 'was', 'were', 'be', 'has', 'have', 'had', 'will', 'would', 'with', 'from', 'as'}
        
        if word1 in filler_words or word2 in filler_words:
            return False
        
        if ngram in STOP_WORDS:
            return False
        
        # 둘 다 유효한 키워드여야 함
        return self._is_valid_keyword(word1) and self._is_valid_keyword(word2)
    
    def _is_valid_trigram(self, trigram: str, word1: str, word2: str, word3: str) -> bool:
        """유효한 trigram인지 확인"""
        # 불용어로 시작하거나 끝나는 trigram 제외
        filler_words = {'the', 'a', 'an', 'of', 'in', 'to', 'for', 'at', 'by', 'on', 'is', 'are', 'was', 'were', 'be', 'has', 'have', 'had', 'will', 'would', 'with', 'from', 'as'}
        
        if word1 in filler_words or word3 in filler_words:
            return False
        
        if trigram in STOP_WORDS:
            return False
        
        # 최소 2개 이상의 유효한 키워드 포함
        valid_count = sum([
            self._is_valid_keyword(word1),
            self._is_valid_keyword(word2),
            self._is_valid_keyword(word3)
        ])
        
        return valid_count >= 2
