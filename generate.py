import yt_dlp
import time
import re
import os
import json
import signal

QUALITY_PROFILES = {
    'hd': {'min_height': 1080, 'suffix': '[HD]'},
    'mobile': {'max_height': 480, 'suffix': '[Mobile]'},
    'audio': {'format': 'bestaudio', 'suffix': '[Audio]'}
}

# ⏱️ Timeout handler (prevents GitHub Actions kill)
def timeout_handler(signum, frame):
    raise Exception("Timeout")

signal.signal(signal.SIGALRM, timeout_handler)


class YouTubePlaylistGenerator:
    def __init__(self, cookies_file='cookies.txt'):
        self.cookies_file = cookies_file
        self.cache_file = '.channel_cache.json'
        self.logos_dir = 'logos'
        self.channels_dir = 'channels'
        self.load_cache()

        for d in [self.logos_dir, self.channels_dir]:
            os.makedirs(d, exist_ok=True)

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

    def detect_channel_country(self, name):
        name = name.lower()
        if any(k in name for k in ['nigeria', 'lagos', 'abuja', 'naija']):
            return 'NG'
        if any(k in name for k in ['ghana', 'accra']):
            return 'GH'
        return 'US'

    def get_stream_info(self, url):
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False, process=False)
                channel_name = info.get('channel', '') if info else ''
        except:
            channel_name = ''

        country = self.detect_channel_country(channel_name)

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,   # ⬅️ reduced timeout
            'retries': 2,           # ⬅️ reduced retries
            'geo_bypass': True,
            'geo_bypass_country': country,
            'noplaylist': True      # ⬅️ prevent delays
        }

        if os.path.exists(self.cookies_file):
            print("🍪 Using cookies")
            ydl_opts['cookiefile'] = self.cookies_file
        else:
            print("⚠️ No cookies")

        # 🔁 Reduced retry attempts
        for attempt in range(2):
            try:
                # ⏱️ Hard timeout per URL (20 sec)
                signal.alarm(20)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                signal.alarm(0)

                if not info:
                    return None

                formats = [f for f in info.get('formats', []) if f.get('url')]
                formats.sort(key=lambda x: x.get('height', 0), reverse=True)

                streams = {}

                for f in formats:
                    if f.get('height', 0) >= 720:
                        streams['hd'] = {'url': f['url'], 'height': f.get('height')}
                        break

                for f in reversed(formats):
                    if f.get('height', 0) <= 480:
                        streams['mobile'] = {'url': f['url'], 'height': f.get('height')}
                        break

                if not streams and formats:
                    streams['main'] = {'url': formats[0]['url']}

                return {
                    'status': 'live' if info.get('is_live') else 'offline',
                    'name': info.get('channel', 'Unknown'),
                    'title': info.get('title', ''),
                    'channel_id': info.get('channel_id'),
                    'video_id': info.get('id'),
                    'streams': streams,
                    'country': country
                }

            except Exception as e:
                signal.alarm(0)
                print(f"Retry {attempt+1}: {e}")
                time.sleep(1)

        return None

    # ✅ UPDATED PLAYLIST GENERATOR
    def generate_playlists(self, channels):
        m3u8_lines = ["#EXTM3U"]
        m3u_lines = ['#EXTM3U x-tvg-url="https://example.com/epg.xml"']

        for ch in channels:
            if ch['status'] != 'live':
                continue

            stream = ch['streams'].get('hd') or next(iter(ch['streams'].values()))
            url = stream['url']

            name = ch["name"]
            safe_id = self.safe_filename(name)
            logo = f"{self.logos_dir}/{safe_id}.png"
            group = "YouTube"

            # streams.m3u8 (original)
            m3u8_lines.append(f'#EXTINF:-1,{name}')
            m3u8_lines.append(url)

            # playlist.m3u (enhanced)
            m3u_lines.append(
                f'#EXTINF:-1 tvg-id="{safe_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}'
            )
            m3u_lines.append(url)

        with open("streams.m3u8", "w") as f:
            f.write("\n".join(m3u8_lines))

        with open("playlist.m3u", "w") as f:
            f.write("\n".join(m3u_lines))

        print("✅ streams.m3u8 + playlist.m3u generated")


def main():
    if not os.path.exists("streams.txt"):
        print("Missing streams.txt")
        return

    with open("streams.txt") as f:
        urls = [l.strip() for l in f if l.strip()]

    # ⚠️ Safety limit (prevents GitHub kill)
    urls = urls[:50]

    gen = YouTubePlaylistGenerator()

    results = []
    for url in urls:
        print("Processing:", url)
        data = gen.get_stream_info(url)
        if data:
            print("✔ Added:", data['name'], data['status'])
            results.append(data)
        else:
            print("✖ Failed:", url)

    gen.generate_playlists(results)
    gen.save_cache()


if __name__ == "__main__":
    main()
