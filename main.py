from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(
    title="Hyperlocal Weather & AQI Precaution API",
    description="Backend API using WeatherAPI Key for weather, AQI, and health advisories."
)

# 🛑 YAHAN APNI WEATHERAPI.COM KI KEY PASTE KAREIN 🛑
WEATHER_API_KEY = "f67ab0a275564c42a5a122537261408"

# CORS enable karna zaroori hai taaki local index.html connect ho sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_aqi_advisory(epa_index: int) -> dict:
    """
    WeatherAPI provides 'us-epa-index' (1 to 6).
    We map it to clear health precautions.
    """
    if epa_index == 1:
        return {
            "status": "Good",
            "danger_level": "Low",
            "precautions": [
                "Air quality is ideal and clean.",
                "Safe for all outdoor activities and exercise."
            ]
        }
    elif epa_index == 2:
        return {
            "status": "Moderate",
            "danger_level": "Moderate",
            "precautions": [
                "Air quality is acceptable.",
                "Unusually sensitive individuals should monitor outdoor exertion."
            ]
        }
    elif epa_index == 3:
        return {
            "status": "Unhealthy for Sensitive Groups",
            "danger_level": "High",
            "precautions": [
                "Sensitive groups (asthma, heart issues, kids) should wear a mask.",
                "Limit prolonged heavy exertion outdoors."
            ]
        }
    elif epa_index == 4:
        return {
            "status": "Unhealthy",
            "danger_level": "Very High",
            "precautions": [
                "N95 mask recommended for all outdoor movement.",
                "Avoid outdoor running or intense exercise.",
                "Keep windows closed during high-traffic hours."
            ]
        }
    elif epa_index == 5:
        return {
            "status": "Very Unhealthy",
            "danger_level": "Severe",
            "precautions": [
                "High health risk! Keep indoor air purifiers running.",
                "Avoid going outdoors unless absolutely necessary.",
                "N95/N99 masks are strictly required."
            ]
        }
    else:
        return {
            "status": "Hazardous",
            "danger_level": "Extreme Danger",
            "precautions": [
                "Emergency conditions: stay strictly indoors.",
                "Keep all windows and doors closed.",
                "Consult a doctor if experiencing respiratory irritation."
            ]
        }


@app.get("/")
def root():
    return {"message": "Server is running! Visit /docs for Swagger UI testing."}


@app.get("/api/v1/forecast")
async def get_weather_and_aqi(
    locality: str = Query(..., example="Kalkaji, New Delhi", description="Locality or city name")
):
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={locality}&aqi=yes"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        data = response.json()

        if "error" in data:
            raise HTTPException(
                status_code=400,
                detail=f"WeatherAPI Error: {data['error']['message']}"
            )

        current = data["current"]
        location = data["location"]
        air_quality = current.get("air_quality", {})
        
        # us-epa-index ranges 1 (Good) to 6 (Hazardous)
        epa_index = air_quality.get("us-epa-index", 1)
        advisory = get_aqi_advisory(epa_index)

        return {
            "query": locality,
            "resolved_location": f"{location.get('name')}, {location.get('region')}, {location.get('country')}",
            "coordinates": {
                "latitude": location.get("lat"),
                "longitude": location.get("lon")
            },
            "weather": {
                "temperature_celsius": current.get("temp_c"),
                "feels_like_celsius": current.get("feelslike_c"),
                "condition": current.get("condition", {}).get("text"),
                "humidity_percentage": current.get("humidity"),
                "wind_kph": current.get("wind_kph")
            },
            "air_quality": {
                "epa_index": epa_index,
                "pm2_5": round(air_quality.get("pm2_5", 0), 2),
                "pm10": round(air_quality.get("pm10", 0), 2),
                "carbon_monoxide_ug_m3": round(air_quality.get("co", 0), 2)
            },
            "health_advisory": advisory
        }