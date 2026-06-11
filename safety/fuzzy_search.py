import difflib
import requests
from django.core.cache import cache


class FuzzyMatcher:
    """
    Fuzzy matching for typo tolerance.
    Handles common misspellings and variations.
    """
    
    # Common typo patterns for major cities/locations
    COMMON_TYPOS = {
        # Indian cities
        'banglore': 'bangalore',
        'bengaluruu': 'bangalore',
        'bengaluru': 'bangalore',
        'bangluru': 'bangalore',
        'bangaluru': 'bangalore',
        'mumbay': 'mumbai',
        'bombay': 'mumbai',
        'delhii': 'delhi',
        'delhi ': 'delhi',
        'hydrebad': 'hyderabad',
        'chnnai': 'chennai',
        'kolkota': 'kolkata',
        'puna': 'pune',
        'noida': 'noida',
        'gurgaon': 'gurugram',
        'haryana': 'haryana',
        'rajasthan': 'rajasthan',
        'gujart': 'gujarat',
        'karnatka': 'karnataka',
        'tamilnadu': 'tamil nadu',
        'chandigarh': 'chandigarh',
        'lucknow': 'lucknow',
        
        # International cities
        'tokiyo': 'tokyo',
        'londan': 'london',
        'londyn': 'london',
        'newyork': 'new york',
        'newyork': 'new york',
        'lasvegas': 'las vegas',
        'sanfransisco': 'san francisco',
        'sanfran': 'san francisco',
        'toront': 'toronto',
        'sydneey': 'sydney',
        'melbourne': 'melbourne',
        'singaproe': 'singapore',
        'dubay': 'dubai',
        'hongkong': 'hong kong',
        'shanghia': 'shanghai',
        'beijng': 'beijing',
        'paaris': 'paris',
        'berln': 'berlin',
        'newyrok': 'new york',
        'lasvega': 'las vegas',
    }
    
    SIMILARITY_THRESHOLD = 0.70  # 70% similarity for fuzzy match
    
    @classmethod
    def get_fuzzy_suggestions(cls, query):
        """
        Generate fuzzy match suggestions for a query.
        """
        query_lower = query.lower().strip()
        
        # Check common typos
        if query_lower in cls.COMMON_TYPOS:
            return [cls.COMMON_TYPOS[query_lower]]
        
        # Generate similar suggestions from known typos
        suggestions = []
        for typo, correct in cls.COMMON_TYPOS.items():
            similarity = difflib.SequenceMatcher(None, query_lower, typo).ratio()
            if similarity >= cls.SIMILARITY_THRESHOLD:
                if correct not in suggestions:
                    suggestions.append(correct)
        
        return suggestions
    
    @classmethod
    def fuzzy_search(cls, query, limit=10):
        """
        Perform fuzzy search with typo tolerance.
        Returns results for fuzzy-matched queries.
        """
        from safety.location_search import LocationSearcher
        
        query_lower = query.lower().strip()
        
        # Get fuzzy suggestions
        suggestions = cls.get_fuzzy_suggestions(query)
        
        if suggestions:
            # Search using first suggestion
            corrected_query = suggestions[0]
            results = LocationSearcher.search_nominatim(corrected_query, limit)
            return results
        
        # If no common typos, try direct fuzzy matching with Nominatim results
        # Get results for close queries
        direct_results = LocationSearcher.search_nominatim(query, limit * 2)
        return direct_results[:limit]
    
    @classmethod
    def enhance_search_results(cls, results, original_query):
        """
        Enhance search results with fuzzy matching scores.
        Rerank results based on similarity to query.
        """
        original_query_lower = original_query.lower()
        
        # Add similarity score to each result
        scored_results = []
        for result in results:
            name = result.get('name', '').lower()
            display_name = result.get('display_name', '').lower()
            
            # Calculate similarity
            name_sim = difflib.SequenceMatcher(None, original_query_lower, name).ratio()
            display_sim = difflib.SequenceMatcher(None, original_query_lower, display_name).ratio()
            
            max_sim = max(name_sim, display_sim)
            
            result['match_score'] = max_sim
            scored_results.append(result)
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return scored_results
