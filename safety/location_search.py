import requests
import json
import hashlib
from datetime import datetime, timedelta
from django.core.cache import cache
from difflib import SequenceMatcher


class LocationSearcher:
    """
    Unified location search using free OpenStreetMap APIs.
    Supports Nominatim and Photon.
    """
    
    # API endpoints (free, no authentication needed)
    NOMINATIM_API = "https://nominatim.openstreetmap.org/search"
    PHOTON_API = "https://photon.komoot.io/api"
    NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
    
    # Request timeout in seconds
    TIMEOUT = 5
    
    # Cache duration in seconds (1 hour)
    CACHE_DURATION = 3600
    
    @staticmethod
    def _get_cache_key(query, method='nominatim'):
        """Generate cache key for search query"""
        cache_key = f"location_search:{method}:{query.lower()}"
        return hashlib.md5(cache_key.encode()).hexdigest()
    
    @staticmethod
    def _rate_limit_check():
        """Check rate limit - simple throttle mechanism"""
        cache_key = "location_search:rate_limit"
        count = cache.get(cache_key, 0)
        
        if count >= 50:  # Max 50 requests per minute
            return False
        
        cache.set(cache_key, count + 1, 60)  # Reset every 60 seconds
        return True
    
    @classmethod
    def search_nominatim(cls, query, limit=10):
        """
        Search using OpenStreetMap Nominatim API.
        Supports worldwide search for cities, countries, landmarks, addresses.
        """
        if not query or len(query.strip()) < 2:
            return []
        
        # Check cache
        cache_key = cls._get_cache_key(query, 'nominatim')
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            return cached_results
        
        # Rate limiting
        if not cls._rate_limit_check():
            return []
        
        try:
            headers = {
                'User-Agent': 'SmartWomenSafety/1.0'
            }
            
            params = {
                'q': query,
                'limit': limit,
                'format': 'json',
                'countrycodes': None,  # Search worldwide
            }
            
            response = requests.get(
                cls.NOMINATIM_API,
                params=params,
                headers=headers,
                timeout=cls.TIMEOUT
            )
            response.raise_for_status()
            
            results = response.json() if response.content else []
            
            # Cache successful results
            cache.set(cache_key, results, cls.CACHE_DURATION)
            
            return results
        
        except requests.RequestException as e:
            print(f"Nominatim API error: {str(e)}")
            return []
    
    @classmethod
    def search_photon(cls, query, limit=10):
        """
        Search using Photon API (faster alternative to Nominatim).
        """
        if not query or len(query.strip()) < 2:
            return []
        
        # Check cache
        cache_key = cls._get_cache_key(query, 'photon')
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            return cached_results
        
        # Rate limiting
        if not cls._rate_limit_check():
            return []
        
        try:
            params = {
                'q': query,
                'limit': limit,
                'lang': 'en',
            }
            
            response = requests.get(
                f"{cls.PHOTON_API}/search",
                params=params,
                timeout=cls.TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json() if response.content else {}
            results = data.get('features', [])
            
            # Cache successful results
            cache.set(cache_key, results, cls.CACHE_DURATION)
            
            return results
        
        except requests.RequestException as e:
            print(f"Photon API error: {str(e)}")
            return []
    
    @classmethod
    def reverse_geocode(cls, latitude, longitude):
        """
        Get location name from coordinates (reverse geocoding).
        """
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return None
        
        try:
            headers = {
                'User-Agent': 'SmartWomenSafety/1.0'
            }
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
            }
            
            response = requests.get(
                cls.NOMINATIM_REVERSE,
                params=params,
                headers=headers,
                timeout=cls.TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json() if response.content else {}
            
            return {
                'display_name': data.get('address', {}).get('road') or 
                               data.get('address', {}).get('city') or 
                               data.get('display_name', 'Unknown'),
                'latitude': latitude,
                'longitude': longitude,
            }
        
        except requests.RequestException as e:
            print(f"Reverse geocoding error: {str(e)}")
            return None
    
    @classmethod
    def format_nominatim_results(cls, results):
        """Format Nominatim results for frontend"""
        formatted = []
        
        for result in results:
            formatted.append({
                'id': result.get('place_id'),
                'name': result.get('name'),
                'display_name': result.get('display_name'),
                'latitude': float(result.get('lat')),
                'longitude': float(result.get('lon')),
                'type': result.get('type'),
                'class': result.get('class'),
                'importance': result.get('importance'),
            })
        
        return formatted
    
    @classmethod
    def format_photon_results(cls, results):
        """Format Photon results for frontend"""
        formatted = []
        
        for feature in results:
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [])
            
            if len(coords) >= 2:
                formatted.append({
                    'id': props.get('osm_id'),
                    'name': props.get('name'),
                    'display_name': props.get('name'),
                    'latitude': coords[1],
                    'longitude': coords[0],
                    'type': props.get('type'),
                    'class': props.get('class'),
                    'importance': None,
                })
        
        return formatted
    
    @classmethod
    def search(cls, query, use_fuzzy=True, limit=10):
        """
        Main search method - tries Nominatim first, with fuzzy matching.
        
        Args:
            query: Search query string
            use_fuzzy: Apply fuzzy matching for typo tolerance
            limit: Max number of results
            
        Returns:
            List of formatted location results
        """
        from safety.fuzzy_search import FuzzyMatcher
        
        query = query.strip()
        if not query or len(query) < 2:
            return []
        
        # Get results from Nominatim
        nominatim_results = cls.search_nominatim(query, limit * 2)
        formatted_results = cls.format_nominatim_results(nominatim_results)
        
        # If Nominatim has results or fuzzy is disabled, return them
        if formatted_results or not use_fuzzy:
            return formatted_results[:limit]
        
        # If no exact matches, try fuzzy search
        fuzzy_results = FuzzyMatcher.fuzzy_search(query, limit * 2)
        if fuzzy_results:
            fuzzy_formatted = cls.format_nominatim_results(fuzzy_results)
            return fuzzy_formatted[:limit]
        
        # Fallback to Photon if Nominatim fails
        photon_results = cls.search_photon(query, limit)
        return cls.format_photon_results(photon_results)[:limit]
