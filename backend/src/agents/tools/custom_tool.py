from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests
from urllib.parse import urlencode

class MyCustomToolInput(BaseModel):
    """Input schema for Hospital Finder Tool."""
    city: str = Field(..., description="City name, e.g., Aurangabad")
    state: str = Field(..., description="State name, e.g., Maharashtra")
    country: str = Field(..., description="Country name, e.g., India")
    limit: int = Field(10, description="Number of hospitals to return (default 10)")

class MyCustomTool(BaseTool):
    name: str = "Hospital Finder Tool"
    description: str = (
        "Fetches top hospitals in a given city using Nominatim OpenStreetMap API, "
        "including phone numbers where OpenStreetMap has them on file."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, city: str, state: str, country: str, limit: int = 10) -> str:
        """Fetch hospitals using Nominatim Search API."""
        try:
            params = {
                "city": city,
                "state": state,
                "country": country,
                "amenity": "hospital",
                "format": "json",
                "limit": limit,
                # extratags=1 makes Nominatim return each result's raw OSM tags
                # (phone, contact:phone, website, opening_hours, etc.) when
                # present - at no extra cost and no extra request. This is how
                # we get phone numbers without switching to a paid API like
                # Google Places.
                "extratags": 1,
            }
            url = f"https://nominatim.openstreetmap.org/search?{urlencode(params)}"
            headers = {"User-Agent": "NearbyHospitalsApp/1.0"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return f"Error fetching hospitals: {response.status_code}"

            data = response.json()
            if not data:
                return "No hospitals found."

            lines = []
            for i, item in enumerate(data):
                extratags = item.get("extratags") or {}
                # OSM tags phone info under a few different keys depending on
                # who mapped the place - check the common ones, in priority
                # order. Most hospitals will NOT have this set; that's a real
                # OpenStreetMap data-completeness limitation, not a bug here.
                phone = (
                    extratags.get("phone")
                    or extratags.get("contact:phone")
                    or extratags.get("contact:mobile")
                    or ""
                ).strip()
                phone_str = phone if phone else "Not available"

                lines.append(
                    f"{i+1}. {item.get('display_name')} | Phone: {phone_str} "
                    f"(lat: {item.get('lat')}, lon: {item.get('lon')})"
                )

            return "\n".join(lines)

        except Exception as e:
            return f"Error occurred: {str(e)}"