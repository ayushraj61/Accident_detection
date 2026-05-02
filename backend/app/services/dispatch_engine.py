import math

def haversine(lat1, lng1, lat2, lng2) -> float:
    """Calculates distance between two GPS points in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def find_nearest_ambulances(alert, ambulances, limit: int = 3) -> list:
    """
    Finds the top `limit` nearest AVAILABLE ambulances.
    """
    alert_lat = getattr(alert, 'lat', None) or (alert.location.lat if hasattr(alert, 'location') else 0)
    alert_lng = getattr(alert, 'lng', None) or (alert.location.lng if hasattr(alert, 'location') else (alert.location.lon if hasattr(alert, 'location') else 0))

    available_ambs = [a for a in ambulances if a.is_available]
    
    # Sort by distance
    available_ambs.sort(key=lambda a: haversine(alert_lat, alert_lng, a.lat, a.lng))
    
    return available_ambs[:limit]
