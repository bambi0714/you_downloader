from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit,
    QPushButton, QMessageBox,
)

from PyQt6.QtWebEngineWidgets import QWebEngineView

from ui.download_popup import DownloadPopup
from ui.progress_window import ProgressDialog
from core.downloader import DownloadThread


class BrowserWindow(QMainWindow):
    """
        기본 브라우저 UI:
        - 뒤로가기 버튼, 앞으로가기 버튼, 주소 표시줄, 동영상 다운로드 버튼 (이 순서로 가로 배치)
        - 하단에 QWebEngineView로 유튜브 페이지 표시
        - 주소 표시줄 Enter로 이동 / 브라우저 URL 변경 시 주소 표시줄 자동 업데이트
        - 다운로드 버튼은 현재 단계에서는 클릭 로그만 출력
    """



    def __init__(self):
        super().__init__()
        self.home_url = "https://www.youtube.com/"
        self.setWindowTitle("YouTube Downloader")
        self.resize(1200, 800)

        # --- 위쪽 컨트롤 바 ---
        self.btn_back = QPushButton("◀")
        self.btn_forward = QPushButton("▶")
        self.url_bar = QLineEdit()
        self.btn_download = QPushButton("동영상 다운로드")

        self.btn_back.setFixedWidth(80)
        self.btn_forward.setFixedWidth(90)
        self.btn_download.setFixedWidth(140)
        self.url_bar.setPlaceholderText("URL")

        # 순서: 뒤로가기, 앞으로가기, 주소 표시줄, 동영상 다운로드 버튼
        top_bar = QHBoxLayout()
        top_bar.addWidget(self.btn_back)
        top_bar.addWidget(self.btn_forward)
        top_bar.addWidget(self.url_bar, stretch=1)
        top_bar.addWidget(self.btn_download)

        # --- 웹 뷰 ---
        self.web = QWebEngineView(self)
        self.web.setUrl(QUrl(self.home_url))
        self.url_bar.setText(self.home_url)

        # --- 레이아웃 조합 ---
        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.web)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # --- 시그널 연결 ---
        self.btn_back.clicked.connect(self._go_back)
        self.btn_forward.clicked.connect(self._go_forward)
        self.url_bar.returnPressed.connect(self._navigate)
        self.web.urlChanged.connect(lambda url: self.url_bar.setText(url.toString()))
        self.btn_download.clicked.connect(self._on_download_clicked)

        # 마우스 앞/뒤 버튼(일부 마우스): 브라우저 앞/뒤 동작 매핑
        self._enable_mouse_nav = True

    # ===================
    #     동작 핸들러
    # ===================
    # url 엔터
    def _navigate(self):
        url = self.url_bar.text().strip()
        if self._is_invalid_url(url):
            return

        self.web.setUrl(QUrl(url))

    def _go_back(self):
        if self.web.history().canGoBack():
            self.web.back()

    def _go_forward(self):
        if self.web.history().canGoForward():
            self.web.forward()

    def _on_download_clicked(self):
        # 다운로드 버튼 클릭 시
        current_url = self.url_bar.text()
        if current_url == self.home_url:
            QMessageBox.warning(self, "잘못된 URL", "url를 입력해주세요.")
            return

        if self._is_invalid_url(current_url):
            return

        popup = DownloadPopup(current_url, self)

        if popup.exec():
            options = popup.result_data
            self._start_download(options)

        print("완료")

    # 마우스 앞/뒤 버튼을 브라우저 네비게이션으로 매핑
    def mousePressEvent(self, event):
        if not self._enable_mouse_nav:
            return super().mousePressEvent(event)

        # 일부 마우스의 '앞으로/뒤로' 버튼: Qt.XButton1 (뒤로), Qt.XButton2 (앞으로)
        if event.button() == Qt.MouseButton.XButton1:
            self._go_back()
            event.accept()
            return
        if event.button() == Qt.MouseButton.XButton2:
            self._go_forward()
            event.accept()
            return
        return super().mousePressEvent(event)

    # ===================
    #     valid 검사
    # ===================
    def _is_invalid_url(self, url):
        if not url or ("youtube.com" not in url and "youtu.be" not in url):
            QMessageBox.warning(self, "잘못된 URL", "유튜브 영상만 다운로드할 수 있습니다.")
            return True

        return False


    # ===================
    #     main logic
    # ===================
    def _start_download(self, options):
        self.progress_dialog = ProgressDialog(self)
        self.download_thread = DownloadThread(options)

        # 연결
        self.download_thread.progress_signal.connect(self.progress_dialog.update_progress)
        self.download_thread.finished_signal.connect(self._on_download_finished)
        self.download_thread.error_signal.connect(self._on_download_error)
        self.progress_dialog.btn_cancel.clicked.connect(self._cancel_download)

        # 실행
        self.download_thread.start()
        self.progress_dialog.exec()

    def _on_download_finished(self, msg):
        self.progress_dialog.close()
        QMessageBox.information(self, "완료", msg)

    def _on_download_error(self, msg):
        self.progress_dialog.close()
        QMessageBox.critical(self, "오류", msg)

    def _cancel_download(self):
        self.download_thread.cancel()
        self.progress_dialog.close()
        QMessageBox.information(self, "취소됨", "다운로드가 취소되었습니다.")

