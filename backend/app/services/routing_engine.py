import httpx
from app.models import Location
from typing import Tuple, Optional

OSRM_URL = "http://127.0.0.1:5000"

async def get_route(source: Location, destination: Location) -> Tuple[Optional[float], Optional[float]]:
    """Get driving distance (km) and duration (min) from OSRM."""
    try:
        # OSRM expects coordinates in order: {longitude},{latitude}
        loc_str = f"{source.lon},{source.lat};{destination.lon},{destination.lat}"
        url = f"{OSRM_URL}/route/v1/driving/{loc_str}?overview=false"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=2.0)
            
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok":
                route = data["routes"][0]
                dist_km = route["distance"] / 1000.0     # OSRM returns meters
                dur_min = route["duration"] / 60.0       # OSRM returns seconds
                return dist_km, dur_min
                
    except Exception as e:
        print(f"[RoutingEngine] OSRM Request Failed (Ensure Docker is running): {e}")
        
    return None, None
