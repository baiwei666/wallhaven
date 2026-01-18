import requests

def check_fields():
    url = "https://wallhaven.cc/api/v1/search?q=anime&page=1"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if 'data' in data and len(data['data']) > 0:
            item = data['data'][0]
            print("Keys in first item:")
            print(list(item.keys()))
            if 'favorites' in item:
                print(f"Favorites: {item['favorites']}")
            if 'views' in item:
                print(f"Views: {item['views']}")
        else:
            print("No data found.")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_fields()
