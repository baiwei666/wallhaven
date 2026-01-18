import requests

def test_search(q):
    url = "https://wallhaven.cc/api/v1/search"
    params = {
        "q": q,
        "categories": "111",
        "purity": "100",
        "sorting": "toplist",
        "page": 1
    }
    with open("debug_results.txt", "a", encoding="utf-8") as f:
        f.write(f"Testing query: '{q}'\n")
        try:
            response = requests.get(url, params=params, timeout=10)
            f.write(f"URL: {response.url}\n")
            f.write(f"Status Code: {response.status_code}\n")
            data = response.json()
            if 'data' in data:
                f.write(f"Results found: {len(data['data'])}\n")
                if len(data['data']) > 0:
                    f.write(f"First result ID: {data['data'][0]['id']}\n")
            else:
                f.write("No 'data' field in response.\n")
                f.write(str(data) + "\n")
        except Exception as e:
            f.write(f"Error: {e}\n")
        f.write("-" * 20 + "\n")
    print(f"Tested {q}")

if __name__ == "__main__":
    # Test 1: Standard query
    test_search("anime")
    
    # Test 2: Favorites filter only
    test_search("favorites:>=100")
    
    # Test 3: Views filter only
    test_search("views:>=5000")
    
    # Test 4: Combined query (what the app does)
    test_search("anime favorites:>=100")

    # Test 6: Range syntax (100..)
    test_search("favorites:100..")

    # Test 9: Known ID search
    test_search("id:3qqdg6")

    # Test 10: Manual URL construction (bypass params encoding)
    q_manual = "favorites:>=100"
    url_manual = f"https://wallhaven.cc/api/v1/search?q={q_manual}&categories=111&purity=100&sorting=toplist"
    with open("debug_results.txt", "a", encoding="utf-8") as f:
        f.write(f"Testing Manual URL: '{url_manual}'\n")
        try:
            response = requests.get(url_manual, timeout=10)
            f.write(f"URL: {response.url}\n")
            f.write(f"Status Code: {response.status_code}\n")
            data = response.json()
            if 'data' in data:
                f.write(f"Results found: {len(data['data'])}\n")
            else:
                f.write("No 'data' field.\n")
        except Exception as e:
            f.write(f"Error: {e}\n")
        f.write("-" * 20 + "\n")
    # Test 11: Get details of the known ID to check its stats
    video_id = "3qqdg6"
    print(f"Fetching details for {video_id}...")
    try:
        r = requests.get(f"https://wallhaven.cc/api/v1/w/{video_id}", params={"apikey": ""}) # apikey optional
        d = r.json()
        if 'data' in d:
            favs = d['data']['favorites']
            views = d['data']['views']
            print(f"ID: {video_id} | Favorites: {favs} | Views: {views}")
            
            # Now test filter with lower threshold
            test_search(f"favorites:>={favs-1}")
            test_search(f"views:>={views-1}")
        else:
            print("Could not fetch details.")
            print(d)
    except Exception as e:
        print(e)
