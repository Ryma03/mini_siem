"""
IP Enrichment module for Mini SIEM
Adds geolocation, ASN, and organization information to alerts
"""

import json
import logging
from typing import Dict, Any, Optional
from functools import lru_cache
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache to store enrichment data for 24 hours
enrichment_cache = {}
CACHE_DURATION = timedelta(hours=24)


class IPEnricher:
    """Enriches IP addresses with geolocation and network information"""

    def __init__(self, use_free_api: bool = True):
        """
        Initialize IP enricher
        
        Args:
            use_free_api: Use free IP-API.com service (set to False for MaxMind)
        """
        self.use_free_api = use_free_api
        self.session = requests.Session()
        self.session.timeout = 5

    def _is_cached(self, ip: str) -> bool:
        """Check if IP enrichment is in cache and still valid"""
        if ip in enrichment_cache:
            cached_time = enrichment_cache[ip].get('cached_at')
            if cached_time and datetime.now() - cached_time < CACHE_DURATION:
                return True
            else:
                del enrichment_cache[ip]
        return False

    def _get_from_cache(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get cached enrichment data"""
        if self._is_cached(ip):
            cached_data = enrichment_cache[ip].copy()
            cached_data.pop('cached_at', None)
            return cached_data
        return None

    def _cache_enrichment(self, ip: str, data: Dict[str, Any]):
        """Cache enrichment data"""
        data['cached_at'] = datetime.now()
        enrichment_cache[ip] = data

    def enrich_ip_free_api(self, ip: str) -> Dict[str, Any]:
        """
        Enrich IP using free IP-API.com service
        
        Args:
            ip: IP address to enrich
            
        Returns:
            Dictionary with enrichment data
        """
        # Check cache first
        cached = self._get_from_cache(ip)
        if cached:
            return cached

        try:
            url = f"http://ip-api.com/json/{ip}"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            enrichment = {
                'country': data.get('country', 'Unknown'),
                'country_code': data.get('countryCode', 'XX'),
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'latitude': data.get('lat', None),
                'longitude': data.get('lon', None),
                'org': data.get('org', 'Unknown'),
                'asn': data.get('as', 'Unknown'),
                'isp': data.get('isp', 'Unknown'),
                'timezone': data.get('timezone', 'Unknown'),
                'is_vpn': data.get('proxy', False)
            }
            
            self._cache_enrichment(ip, enrichment)
            return enrichment
            
        except Exception as e:
            logger.warning(f"Failed to enrich IP {ip} from free API: {str(e)}")
            return self._get_default_enrichment()

    def enrich_ip_ipwhois(self, ip: str) -> Dict[str, Any]:
        """
        Enrich IP using ipwhois library
        
        Args:
            ip: IP address to enrich
            
        Returns:
            Dictionary with enrichment data
        """
        # Check cache first
        cached = self._get_from_cache(ip)
        if cached:
            return cached

        try:
            from ipwhois import IPWhois
            
            obj = IPWhois(ip)
            results = obj.lookup(ip_version=4)
            
            enrichment = {
                'country': results.get('country', 'Unknown'),
                'country_code': results.get('country_code', 'XX'),
                'city': 'Unknown',
                'region': results.get('asn_description', 'Unknown'),
                'latitude': None,
                'longitude': None,
                'org': results.get('asn_description', 'Unknown'),
                'asn': results.get('asn', 'Unknown'),
                'isp': results.get('nets', [{}])[0].get('description', 'Unknown'),
                'timezone': 'Unknown',
                'is_vpn': False
            }
            
            self._cache_enrichment(ip, enrichment)
            return enrichment
            
        except Exception as e:
            logger.warning(f"Failed to enrich IP {ip} using ipwhois: {str(e)}")
            return self._get_default_enrichment()

    def enrich_ip(self, ip: str) -> Dict[str, Any]:
        """
        Enrich IP address with geolocation and network data
        
        Args:
            ip: IP address to enrich
            
        Returns:
            Dictionary with enrichment data
        """
        # Skip private IPs
        if self._is_private_ip(ip):
            return self._get_private_ip_enrichment()

        if self.use_free_api:
            return self.enrich_ip_free_api(ip)
        else:
            return self.enrich_ip_ipwhois(ip)

    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        """Check if IP is private"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            octets = [int(p) for p in parts]
            
            # RFC 1918 private ranges
            if octets[0] == 10:
                return True
            if octets[0] == 172 and 16 <= octets[1] <= 31:
                return True
            if octets[0] == 192 and octets[1] == 168:
                return True
            # Loopback
            if octets[0] == 127:
                return True
            
            return False
        except:
            return False

    @staticmethod
    def _get_default_enrichment() -> Dict[str, Any]:
        """Get default enrichment data when lookup fails"""
        return {
            'country': 'Unknown',
            'country_code': 'XX',
            'city': 'Unknown',
            'region': 'Unknown',
            'latitude': None,
            'longitude': None,
            'org': 'Unknown',
            'asn': 'Unknown',
            'isp': 'Unknown',
            'timezone': 'Unknown',
            'is_vpn': False
        }

    @staticmethod
    def _get_private_ip_enrichment() -> Dict[str, Any]:
        """Get enrichment data for private IPs"""
        return {
            'country': 'Private',
            'country_code': 'XX',
            'city': 'Internal Network',
            'region': 'Private Range',
            'latitude': None,
            'longitude': None,
            'org': 'Internal',
            'asn': 'Internal',
            'isp': 'Internal',
            'timezone': 'Unknown',
            'is_vpn': False
        }

    def enrich_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich an entire alert with IP information
        
        Args:
            alert: Alert dictionary
            
        Returns:
            Enriched alert dictionary
        """
        src_ip = alert.get('src_ip', '')
        dst_ip = alert.get('dst_ip', '')
        
        enrichment_data = {
            'source': self.enrich_ip(src_ip),
            'destination': self.enrich_ip(dst_ip),
            'enriched_at': datetime.now().isoformat()
        }
        
        alert['enrichment'] = enrichment_data
        return alert
