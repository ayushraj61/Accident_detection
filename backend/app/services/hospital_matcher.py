import math

def haversine(lat1, lng1, lat2, lng2) -> float:
    """Calculates distance between two GPS points in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def rank_hospitals(alert, hospitals) -> list:
    """Rank hospitals by weighted score (distance, beds, ICU, acceptance, ER load)."""
    scored_hospitals = []
    
    # Alert usually has lat/lng or location.lat/location.lng
    alert_lat = getattr(alert, 'lat', None) or (alert.location.lat if hasattr(alert, 'location') else 0)
    alert_lng = getattr(alert, 'lng', None) or (alert.location.lng if hasattr(alert, 'location') else (alert.location.lon if hasattr(alert, 'location') else 0))

    for h in hospitals:
        # DB models use lat/lng
        h_lat = h.lat
        h_lng = h.lng
        
        dist = haversine(alert_lat, alert_lng, h_lat, h_lng)
        
        # Max reasonable distance to normalize against (e.g. 50km)
        dist_score = max(0, 100 - (dist / 50 * 100)) 
        
        # Bed availability score
        bed_score = min(100, (h.available_beds or 0) * 10) 
        
        # Specialty match: MVP assumes severe accidents need ICU
        specialty_score = 100 if h.icu_available else 0
        
        # We can add historical_acceptance_rate to DB later, use default for now
        acceptance_score = getattr(h, 'historical_acceptance_rate', 0.95) * 100
        er_load_score = 100 - (h.current_er_load or 0)
        
        final_score = (
            (dist_score * 0.30) +
            (bed_score * 0.25) +
            (specialty_score * 0.20) +
            (acceptance_score * 0.15) +
            (er_load_score * 0.10)
        )
        scored_hospitals.append((final_score, h))
        
    scored_hospitals.sort(key=lambda x: x[0], reverse=True)
    return [h for score, h in scored_hospitals]
