import sys
import yt_dlp
import os
from PyQt6.QtCore import QThread, pyqtSignal

from core.analyzer import analyze_url_is_playlist, filter_available_subtitles


class DownloadThread(QThread):
    """
    yt_dlp 다운로드를 별도 스레드에서 수행
    - progress_signal: (percent, status_text)
    - finished_signal: 완료 메시지
    - error_signal: 오류 메시지
    """

    # 시그널
    progress_signal = pyqtSignal(float, str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, options: dict):
        super().__init__()
        self.options = options
        self._is_canceled = False

    # -------------------------------------
    # 내부 메서드
    # -------------------------------------
    def get_infos(self, url):
        try:
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            self.error_signal.emit(f"다운로드 중 오류 발생: {e}")



    def progress_hook(self, d):
        if self._is_canceled:
            raise Exception("사용자에 의해 다운로드 취소됨.")
        
        # 파일명 파싱
        extension = d.get("info_dict", []).get("ext", "null")
        pre_fix_msg = "영상"
        if extension == "vtt":
            title = d.get("filename", "알 수 없는 영상").strip("'").split("\\")[-1]
            pre_fix_msg = "자막"
        elif extension == "null":
            title = "알 수 없는 영상"
        else:
            title = d.get("info_dict").get("title")

        display_title = ""
        max_len = 50  # 한 줄에 보여줄 최대 문자 수 (적절히 조정)
        if len(title) > max_len:
            display_title = title[:max_len] + "\n" + title[max_len:]

        # 다운로드 상태 확인

        if d["status"] == "downloading":
            percent = d.get("_percent_str", "").replace("%", "").strip()
            self.progress_signal.emit(float(percent or 0), f"{pre_fix_msg} 다운로드 중 : {display_title}")

        elif d["status"] == "finished":
            for p in range(90, 100):
                if self._is_canceled:
                    break
                self.progress_signal.emit(p, f"{pre_fix_msg} 병합 중... : {display_title}")
                QThread.msleep(50)

            self.progress_signal.emit(100, f"{pre_fix_msg} 병합 중... : {display_title}")

    # -------------------------------------
    # 메인 실행 로직
    # -------------------------------------
    def run(self):
        url = self.options["url"]
        fmt = self.options["format"]
        out_dir = self.options["output_path"]
        fragments = self.options["max_fragments"]
        # self.container = self.options.get("container", "mp4")
        subtitle_only = self.options.get("subtitle_only", False)
        subtitle_enabled = self.options.get("subtitle", False)
        is_playlist = analyze_url_is_playlist(url)

        ffmpeg_path = self._get_ffmpeg_path()

        # 진행 상태 초기화
        self.progress_signal.emit(0, "플레이리스트 감지 중..." if is_playlist else "영상 분석 중...")

        # yt_dlp 정보 가져오기
        # infos = self.get_infos(url)
        # if not infos:
        #     self.error_signal.emit("영상 정보를 가져올 수 없습니다.")
        #     return

        # -------------------------------------
        # 자막 필터링
        # -------------------------------------
        valid_langs = []
        if subtitle_enabled:
            requested_langs = self.options.get("subtitle_langs", [])
            if is_playlist:
                valid_langs = requested_langs
            else:
                # 단일 영상은 실제 자막 존재 여부 확인
                valid_langs = filter_available_subtitles(url, requested_langs)

            if not valid_langs:
                msg = "선택한 자막 언어는 제공되지 않습니다."
                if subtitle_only:
                    self.progress_signal.emit(0, msg)
                    self.finished_signal.emit("자막만 다운로드 모드 — 종료")
                    return
                else:
                    self.progress_signal.emit(0, msg + " (영상만 다운로드)")
            elif not is_playlist:
                self.progress_signal.emit(0, f"자막 다운로드 가능 언어: {', '.join(valid_langs)}")


        # -------------------------------------
        # yt_dlp 옵션 구성
        # -------------------------------------
        ydl_opts = {
            "outtmpl": os.path.join(out_dir, f"%(title)s.%(ext)s"),
            "quiet": True,
            "progress_hooks": [self.progress_hook],
            "noplaylist": not is_playlist,
            "ffmpeg_location": ffmpeg_path,
        }

        # 자막 존재 시
        if valid_langs:
            ydl_opts.update({
                "writesubtitles": True,
                "subtitleslangs": valid_langs,
                "skip_auto_subtitle": True,
            })

        # 자막만 다운 시
        if subtitle_only:
            ydl_opts["skip_download"] = True
        else:
            ydl_opts.update({
                "format": fmt,
                "concurrent_fragment_downloads": fragments,
                # 추후 mp3 추가 되면
                # "merge_output_format": container,
            })

        # -------------------------------------
        # 다운로드 실행
        # -------------------------------------
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # 완료 메시지
            if subtitle_only:
                msg = "자막 다운로드 완료 ✅"
                if is_playlist:
                    msg += " (플레이리스트 자막 미지원 영상은 건너뜀)"
                self.finished_signal.emit(msg)
            else:
                self.finished_signal.emit("다운로드 완료 ✅")

        except Exception as e:
            if "취소됨" in str(e):
                self.error_signal.emit("사용자가 다운로드를 취소했습니다.")
            else:
                self.error_signal.emit(f"다운로드 중 오류 발생: {e}")

    # -------------------------------------
    # 다운로드 취소
    # -------------------------------------
    def cancel(self):
        """다운로드 중단"""
        print("다운로드 중단")
        self._is_canceled = True

    def _get_ffmpeg_path(self):
        """PyInstaller 빌드 시 ffmpeg 경로 자동 탐지"""
        if hasattr(sys, "_MEIPASS"):
            # exe 실행 시 임시폴더(_MEIxxxx)에 풀림
            ffmpeg_dir = os.path.join(sys._MEIPASS, "ffmpeg")
            return ffmpeg_dir
        return os.path.join(os.getcwd(), "ffmpeg")  # 개발 중엔 로컬 ffmpeg 폴더 사용

    @staticmethod
    def _extract_lang_code(label):
        """'한국어(ko)' → 'ko'"""
        if "(" in label and ")" in label:
            return label[label.find("(") + 1: label.find(")")]
        return label