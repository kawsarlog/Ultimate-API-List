import asyncio
import aiohttp
import json
import os
import re

# Categories list
CATEGORIES = [
    "Agents", "AI", "Automation", "Developer_tools", "Ecommerce",
    "Integrations", "Jobs", "Lead_generation", "MCP_servers", "News",
    "Open_source", "Real_estate", "SEO_tools", "Social_media", "Travel",
    "Videos", "Other"
]

# Proxies
PROXIES = "http://rnvefjue-US-rotate:vltalliulpt3@p.webshare.io:80/"

HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://apify.com',
    'Referer': 'https://apify.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
    'content-type': 'application/x-www-form-urlencoded',
    'sec-ch-ua': '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'x-algolia-api-key': '0ecccd09f50396a4dbbe5dbfb17f4525',
    'x-algolia-application-id': 'OW0O5I3QO7',
}

API_URL = 'https://ow0o5i3qo7-2.algolianet.com/1/indexes/prod_PUBLIC_STORE/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.22.1)%3B%20Browser'

async def fetch_category_data(session, category):
    offset = 0
    length = 1000
    all_hits = []
    
    while True:
        payload = {
            "query": "",
            "length": length,
            "offset": offset,
            "filters": f"categories:{category}",
            "restrictSearchableAttributes": [],
            "attributesToHighlight": [],
            "attributesToRetrieve": [
                "objectId", "title", "name", "username", "userFullName",
                "stats", "description", "pictureUrl", "userPictureUrl",
                "notice", "currentPricingInfo", "categories",
                "actorReviewRating", "actorReviewCount", "bookmarkCount",
                "isWhiteListedForAgenticPayments", "badge"
            ],
            "enableABTest": True,
            "analyticsTags": ["web", "store-search"],
            "clickAnalytics": True,
            "userToken": "0e8e5a7c-fc92-4059-81d2-cc30a0eaa292"
        }

        try:
            async with session.post(API_URL, headers=HEADERS, data=json.dumps(payload), proxy=PROXIES) as response:
                if response.status != 200:
                    print(f"Error fetching category {category} offset {offset}: {response.status}")
                    break
                
                data = await response.json()
                hits = data.get('hits', [])
                
                if not hits:
                    break
                
                all_hits.extend(hits)
                offset += length
                
                if len(hits) < length:
                    break
                    
        except Exception as e:
            print(f"Exception fetching category {category}: {e}")
            break
            
    return category, all_hits

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

def process_category(category, hits):
    total_count = len(hits)
    folder_name = f"{category} {total_count}"
    
    # Create folder
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    readme_path = os.path.join(folder_name, "README.md")
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("| Title | Description | Rating | Total Users |\n")
        f.write("| --- | --- | --- | --- |\n")
        
        for item in hits:
            title = item.get('title')
            if title is None: title = "null"
            
            description = item.get('description')
            if description is None: 
                description = "null"
            else: 
                # Remove newlines and pipes to keep table format clean
                description = description.replace('\n', ' ').replace('\r', '').replace('|', '-')
            
            stats = item.get('stats', {})
            total_users = stats.get('totalUsers')
            if total_users is None: total_users = "null"
                
            rating = stats.get('actorReviewRating')
            if rating is None: rating = "null"
                
            name = item.get('name')
            username = item.get('username')
            
            if username and name:
                 url = f"https://apify.com/{username}/{name}"
            else:
                 url = "null"
            
            line = f"| [{title}]({url}) | {description} | {rating} | {total_users} |\n"
            f.write(line)
            
    return folder_name

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_category_data(session, category) for category in CATEGORIES]
        results = await asyncio.gather(*tasks)
        
    category_folders = {}
    
    for category, hits in results:
        print(f"Processed {category}: {len(hits)} items")
        folder_name = process_category(category, hits)
        category_folders[category] = folder_name
        
    # Update root README.md
    update_root_readme(category_folders)

def update_root_readme(category_folders):
    root_readme_path = "README.md"
    
    # Check if README exists, if not create basic one
    if not os.path.exists(root_readme_path):
         with open(root_readme_path, "w", encoding="utf-8") as f:
             f.write("# Ultimate API List\n\n")

    with open(root_readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    toc_marker = "## Categories Table of Contents"
    
    # Remove existing TOC if present (simple regex assumption)
    if toc_marker in content:
        content = content.split(toc_marker)[0]
        
    toc = f"\n\n{toc_marker}\n\n"
    for category in CATEGORIES:
        if category in category_folders:
            folder_name = category_folders[category]
            # Url encode folder name for markdown link
            folder_link = folder_name.replace(" ", "%20") 
            toc += f"- [{category}](./{folder_link})\n"
            
    with open(root_readme_path, "w", encoding="utf-8") as f:
        f.write(content + toc)

if __name__ == "__main__":
    # Fix for Windows asyncio loop policy if needed
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
