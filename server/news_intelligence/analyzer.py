"""
News Analyzer Module (Optimized Version)

Provides AI-powered analysis for news articles with optimization:
1. Rule-based first + AI supplementary (reduces API calls by ~70%)
2. Batch processing (10 articles per API call)
3. Designed for async background processing

Categories: Crisis, Ocean, Air, Inland, Economy, ETC
"""

import os
import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. AI analysis will use fallback methods.")


# Stop words to exclude from word cloud
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
    # Logistics-generic words (too common)
    'logistics', 'company', 'market', 'industry', 'business', 'report',
    'news', 'says', 'said', 'new', 'year', 'month', 'week', 'day',
    'percent', 'million', 'billion', 'according', 'also', 'however',
    # GDELT-specific terms (should not appear in word cloud)
    'goldstein', 'goldstein scale', 'average tone', 'avg tone', 'mentions',
    'sources', 'articles', 'material conflict', 'verbal conflict',
    'material cooperation', 'verbal cooperation', 'category', 'event',
    'location', 'involves', 'unknown',
    # Korean common words
    '있다', '하다', '되다', '이다', '있는', '하는', '되는', '대한', '위한', '통해',
    '따르면', '것으로', '지난', '오는', '관련', '등', '및', '위해', '대해', '있어',
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
    """
    
    CATEGORIES = ['Crisis', 'Ocean', 'Air', 'Inland', 'Economy', 'ETC']
    
    # Confidence threshold - articles below this need AI verification
    CONFIDENCE_THRESHOLD = 0.6
    
    # Batch size for AI processing
    BATCH_SIZE = 10
    
    def __init__(self, api_key: str = None, model: str = 'gpt-4o-mini'):
        """
        Initialize analyzer.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use
        """
        self.model = model
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        
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
                ai_result['analysis_method'] = 'ai'
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
            self.logger.info(f"Processing {len(needs_ai)} articles with AI (batch mode)")
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
                    article['analysis_method'] = 'ai_batch'
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
        Analyze multiple articles in a single AI API call.
        
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
        
        prompt = f"""Analyze these {len(batch)} logistics news articles. For each, provide:
- category: One of [Crisis, Ocean, Air, Inland, Economy, ETC]
- countries: ISO 2-letter country codes mentioned (max 3)
- keywords: 3 important keywords
- is_crisis: true if about supply chain disruption

Articles:
{chr(10).join(articles_text)}

Respond with a JSON array:
[{{"id": 0, "category": "...", "countries": ["XX"], "keywords": ["..."], "is_crisis": false}}, ...]"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a logistics news analyst. Respond only with valid JSON array."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
        
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
        Analyze single article using OpenAI API (fallback for single articles).
        """
        prompt = f"""Analyze this logistics news article and provide:
1. Category: One of [Crisis, Ocean, Air, Inland, Economy, ETC]
2. Countries: List of ISO 2-letter country codes mentioned (max 5)
3. Keywords: 3-5 important keywords/phrases
4. Is Crisis: true if about supply chain disruption

Title: {title}
Content: {summary}

Respond in JSON format:
{{"category": "...", "countries": ["XX", "YY"], "keywords": ["word1", "word2"], "is_crisis": true/false}}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a logistics news analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200,
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
        
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
        Generate a summary of current crisis/critical alerts.
        """
        if not crisis_articles:
            return "No critical alerts at this time."
        
        articles_to_summarize = crisis_articles[:max_articles]
        
        if self.client:
            try:
                return self._generate_summary_with_ai(articles_to_summarize)
            except Exception as e:
                self.logger.error(f"AI summary failed, using fallback: {e}")
        
        # Fallback: Simple list format
        summaries = []
        for article in articles_to_summarize:
            title = article.get('title', 'Unknown')
            source = article.get('source_name', '')
            summaries.append(f"• {title} ({source})")
        
        return "\n".join(summaries)
    
    def _generate_summary_with_ai(self, articles: List[Dict[str, Any]]) -> str:
        """Generate crisis summary using AI"""
        articles_text = "\n".join([
            f"- {a.get('title', '')}: {a.get('content_summary', '')[:200]}"
            for a in articles
        ])
        
        prompt = f"""Summarize these logistics crisis alerts in 2-3 concise bullet points.
Focus on: What happened, where, and potential supply chain impact.

Articles:
{articles_text}

Provide a brief, actionable summary for logistics professionals."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a logistics crisis analyst. Be concise and actionable."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300,
        )
        
        return response.choices[0].message.content.strip()
    
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
    
    def extract_keywords_for_wordcloud(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Extract keywords from articles for word cloud visualization.
        """
        keyword_freq = {}
        
        for article in articles:
            keywords = article.get('keywords', [])
            for keyword in keywords:
                keyword = keyword.lower().strip()
                if keyword and keyword not in STOP_WORDS and len(keyword) > 2:
                    keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        return keyword_freq
