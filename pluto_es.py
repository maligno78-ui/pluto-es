import requests
import uuid
import unicodedata
from datetime import datetime
from typing import List, Dict, Any


class PlutoProvider:
    """Generador de M3U para Pluto TV España"""

    USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36")
    BOOT_URL = "https://boot.pluto.tv/v4/start"
    CHANNELS_URL = "https://service-channels.clusters.pluto.tv/v2/guide/channels"
    STITCHER_BASE = "https://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/v2/stitch/hls/channel"
    EPG_URL = "https://github.com/matthuisman/i.mjh.nz/raw/master/PlutoTV/es.xml.gz"
    GROUP_LOGO = ("https://play-lh.googleusercontent.com/"
                  "uYuzRkAmitXSVzx5J3zKJR3WlYKbMr6kffslwSxLiWWGgUIUm6kFB2ZeEjFJLclIZxox=w240-h480-rw")
    GROUP_TITLE = "PLUTO TV"
    REGION_IP = "88.26.241.248"
    TIMEOUT = 30

    def __init__(self):
        self.device_id = str(uuid.uuid1())
        self.session_token = None
        self.stitcher_params = ""
        self.session_expires_at = 0

        self.headers = {
            "authority": "boot.pluto.tv",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://pluto.tv",
            "referer": "https://pluto.tv/",
            "user-agent": self.USER_AGENT,
            "X-Forwarded-For": self.REGION_IP,
        }

    def _get_session_token(self) -> str:
        if self.session_token and datetime.now().timestamp() < self.session_expires_at:
            return self.session_token
        try:
            params = {
                "appName": "web", "appVersion": "8.1.0", "deviceVersion": "150.0.0",
                "deviceModel": "web", "deviceMake": "chrome", "deviceType": "web",
                "clientID": self.device_id, "clientModelNumber": "1.0.0",
                "serverSideAds": "false", "architecture": "x86_64",
                "buildVersion": "1.0.0", "drmCapabilities": "widevine:L3",
            }
            response = requests.get(self.BOOT_URL, headers=self.headers,
                                    params=params, timeout=self.TIMEOUT)
            data = response.json()
            self.session_token = data.get("sessionToken", "")
            self.stitcher_params = data.get("stitcherParams", "")
            self.session_expires_at = datetime.now().timestamp() + 4 * 3600
            return self.session_token
        except Exception:
            return ""

    def get_channels(self) -> List[Dict[str, Any]]:
        try:
            token = self._get_session_token()
            if not token:
                return []

            headers = self.headers.copy()
            headers["authorization"] = f"Bearer {token}"

            response = requests.get(self.CHANNELS_URL, params={"limit": "1000"},
                                    headers=headers, timeout=self.TIMEOUT)
            channel_data = response.json().get("data", [])

            quality_suffix = (
                "&quality=720p&deviceMake=chrome&deviceType=web&deviceModel=web"
                "&deviceVersion=133.0.0&architecture=x86_64&buildVersion=1.0.0"
                "&includeExtendedEvents=true&masterJWTPassthrough=true"
            )

            processed_channels = []
            for channel in channel_data:
                channel_id = channel.get("id")
                name = channel.get("name")
                if not channel_id or not name:
                    continue

                logo = next((img.get("url") for img in channel.get("images", [])
                            if img.get("type") == "colorLogoPNG"), "")

                stream_url = (
                    f"{self.STITCHER_BASE}/{channel_id}/master.m3u8"
                    f"?{self.stitcher_params}&jwt={token}{quality_suffix}"
                )

                processed_channels.append({
                    "id": str(channel_id),
                    "name": name,
                    "stream_url": stream_url,
                    "logo": logo,
                })
            return processed_channels
        except Exception:
            return []

    def _sort_key(self, name: str) -> str:
        """Normaliza tildes y mayúsculas para orden alfabético español"""
        normalized = unicodedata.normalize("NFKD", name)
        return normalized.encode("ascii", "ignore").decode("ascii").lower()

    def generate_m3u(self, channels: List[Dict[str, Any]]) -> str:
        channels = sorted(channels, key=lambda ch: self._sort_key(ch["name"]))

        m3u = f'#EXTM3U url-tvg="{self.EPG_URL}"\n\n'

        for i, ch in enumerate(channels):
            if i == 0:
                m3u += (f'#EXTINF:-1 group-logo="{self.GROUP_LOGO}" '
                        f'tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" '
                        f'group-title="{self.GROUP_TITLE}",{ch["name"]}\n')
            else:
                m3u += (f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-logo="{ch["logo"]}" '
                        f'group-title="{self.GROUP_TITLE}",{ch["name"]}\n')
            m3u += f'{ch["stream_url"]}\n\n'

        return m3u


if __name__ == "__main__":
    provider = PlutoProvider()
    channels = provider.get_channels()
    with open("pluto_es.m3u", "w", encoding="utf-8") as f:
        f.write(provider.generate_m3u(channels))
    print(f"Generado pluto_es.m3u con {len(channels)} canales")
