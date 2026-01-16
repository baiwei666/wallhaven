import requests

class WallhavenAPI:
    BASE_URL = "https://wallhaven.cc/api/v1"

    def __init__(self, api_key=None):
        self.api_key = api_key

    def search(self, q="", categories="111", purity="100", sorting="date_added", 
               order="desc", resolutions=None, ratios=None, atleast=None, colors=None, page=1):
        """
        Search for wallpapers on Wallhaven.
        atleast: minimum resolution (e.g., '1920x1080')
        """
        params = {
            "q": q,
            "categories": categories,
            "purity": purity,
            "sorting": sorting,
            "order": order,
            "page": page
        }
        if self.api_key:
            params["apikey"] = self.api_key
        if resolutions:
            params["resolutions"] = resolutions
        if ratios:
            params["ratios"] = ratios
        if atleast:
            params["atleast"] = atleast
        if colors:
            params["colors"] = colors

        try:
            response = requests.get(f"{self.BASE_URL}/search", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching data from Wallhaven: {e}")
            return None

    def get_details(self, wallpaper_id):
        """Get details for a specific wallpaper."""
        params = {}
        if self.api_key:
            params["apikey"] = self.api_key
        
        try:
            response = requests.get(f"{self.BASE_URL}/w/{wallpaper_id}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching detail for {wallpaper_id}: {e}")
            return None
