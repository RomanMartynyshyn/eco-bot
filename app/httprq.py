import httpx
import logging

# This file contains function for interaction with backend api

# Main api url
import os

# Main api url
URL = os.getenv("BACKEND_URL", "http://backend:8000")

# Func to create marker
async def post_marker(payload: dict) -> httpx.Response | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{URL}/markers/", 
                json=payload, 
                timeout=10.0
            )
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error {e.response.status_code}: {e}")
    except httpx.RequestError as e:
        logging.error(f"Connection error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

    return None

# Func to uptate marker, for display pictures on frontend
async def put_marker(photo_id: str, marker_id: int) -> httpx.Response | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{URL}/markers/{marker_id}", 
                json={"photo_url": photo_id}, 
                timeout=10.0
            )
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error {e.response.status_code}: {e}")
    except httpx.RequestError as e:
        logging.error(f"Connection error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

    return None

# Func to get all markers user send
async def get_markers(user_id: int) -> httpx.Response | None:
    url = f"{URL}/users/{user_id}/markers"
    try:
         async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error {e.response.status_code}: {e}")
    except httpx.RequestError as e:
        logging.error(f"Connection error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

    return None

