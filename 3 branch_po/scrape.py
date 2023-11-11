import aiohttp
import asyncio
import json
import geojson

baseurl = "https://webgis.nic.in/publishing/rest/services/misc/post/MapServer/3/query?token=LFFsVAR6Zo17lk12KOYg6216EquuOdsywx2LbAGfPkD7MI6N2p25JhH3XQJ3aUizvQW9EJ5TNhgAVvlaZITRFA..&f=json&where=&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=*&objectIds="
minId = 1
maxId = 89161

hedaers = {
    "Origin": "https://postalgis.nic.in",
    "Referer": "https://postalgis.nic.in",
    "Host": "webgis.nic.in",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
}

# result = requests.get(baseurl + str(minId), headers=hedaers)
# json_data = json.loads(result.text)
# print(json_data.get("features")[0].get("attributes"))


def getUrl(start, end):
    url = baseurl
    for i in range(start, end):
        url += str(i) + "%2C"
    url += str(end)
    return url


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def fetch_all(s: aiohttp.ClientSession, start, end, interval=100):
    tasks = []
    i = start
    while i < end:
        tasks.append(
            asyncio.create_task(fetch(s, getUrl(i, min(i + interval - 1, end))))
        )
        i += interval
    return await asyncio.gather(*tasks)


features = []
brokenFeatures = []


async def main():
    async with aiohttp.ClientSession(headers=hedaers) as session:
        c = 1
        while c < maxId:
            print(
                "Fetching",
                str(c).zfill(6),
                "to",
                str(min(c + 20000 - 1, maxId)).zfill(6),
            )
            results = await fetch_all(session, c, min(c + 20000 - 1, maxId), 100)

            for i in results:
                json_data = json.loads(i)
                for j in json_data.get("features"):
                    try:
                        geo = j.get("geometry")
                        atrbs = j.get("attributes")
                        lat, lon = geo.get("y"), geo.get("x")

                        if lat and lon:
                            features.append(
                                geojson.Feature(
                                    geometry=geojson.Point((lon, lat)),
                                    properties=atrbs,
                                )
                            )
                        else:
                            brokenFeatures.append(
                                geojson.Feature(
                                    geometry=geojson.Point((lon, lat)),
                                    properties=atrbs,
                                )
                            )

                    except Exception as e:
                        print(e)
                        print("Error", atrbs["objectid"])

            c += 20000


asyncio.run(main())
print("Done scraping")

with open("branch_po.geojson", "w") as f:
    geojson.dump(geojson.FeatureCollection(features), f)

with open("broken.geojson", "w") as f:
    geojson.dump(geojson.FeatureCollection(brokenFeatures), f)

print("Completed")
