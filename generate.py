import yt_dlp
import time
import re
import os
import json

class YouTubePlaylistGenerator:
    def __init__(self, cookies_file='cookies.txt'):
        self.cookies_file = cookies_file
        self.cache_file = '.channel_cache.json'
        self.load_cache()

    def load_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        except:
            self.cache = {'channels': {}}

    def save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)

    def safe_filename(self, name):
        safe = re.sub(r'[^\w\s-]', '', name).strip()
        return re.sub(r'[-\s]+', '_', safe).lower()

    def get_stream_info(self, url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'retries': 3,
            'socket_timeout': 30,
            'geo_bypass': True,
            'format': 'best[ext=m3u8]/best',
        }

        # Optional cookies
        if os.path.exists(self.cookies_file):
            ydl_opts['cookiefile'] = self.cookies_file
            print("🍪 Using cookies")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                return None

            # ❌ Skip non-live streams
            if not info.get('is_live'):
                print("⛔ Not live:", url)
                return None

            stream_url = info.get('url')

            if not stream_url:
                print("❌ No stream URL:", url)
                return None

            print("✅ Live:", info.get('channel'))

            return {
                'name': info.get('channel', 'Unknown'),
                'url': stream_url
            }

        except Exception as e:
            print("❌ Error:", url, "|", str(e))
            return None

    def generate_playlist(self, channels):
        lines = ["#EXTM3U"]

        for ch in channels:
            lines.append(f'#EXTINF:-1,{ch["name"]}')
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
            lines.append('#EXTVLCOPT:http-referrer=https://www.youtube.com/')
            lines.append(ch["url"])

        with open("streams.m3u8", "w") as f:
            f.write("\n".join(lines))

        print("✅ Playlist generated: streams.m3u8")


def main():
    if not os.path.exists("streams.txt"):
        print("❌ streams.txt missing")
        return

    with open("streams.txt") as f:
        urls = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    gen = YouTubePlaylistGenerator()

    results = []

    for url in urls:
        print("🔄 Processing:", url)
        data = gen.get_stream_info(url)
        if data:
            results.append(data)
        time.sleep(1)  # avoid rate-limit

    if not results:
        print("❌ No live streams found")
        return

    gen.generate_playlist(results)
    gen.save_cache()


if __name__ == "__main__":
    main()
