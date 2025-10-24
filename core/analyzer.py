import yt_dlp

def analyze_url_is_playlist(url: str) -> bool:
    """
    URL이 단일 영상인지, 플레이리스트인지 판별한다.
    """
    if "playlist" in url:
        return True
    else:
        return False


def filter_available_subtitles(url, requested_langs):
    """yt_dlp로 영상 메타데이터 확인 후, 실제 존재하는 자막만 반환"""
    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            available = set(info.get("subtitles", {}).keys())
            return [lang for lang in requested_langs if lang in available]
    except Exception:
        return []