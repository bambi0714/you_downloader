import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QCheckBox,
    QHBoxLayout, QPushButton, QFileDialog, QSpinBox, QListWidget, QListWidgetItem,
)

from PyQt6.QtCore import Qt


class DownloadPopup(QDialog):
    """
    Step 2: 다운로드 옵션 선택 팝업
    - 품질, 포맷, 자막, 세그먼트, 저장 경로를 설정
        - 품질 선택: 480p / 720p / 1080p / 4K
        - 선택한 해상도가 지원되지 않으면 자동으로 그 영상의 최고 화질로 다운로드
    - "다운로드 시작" 버튼 클릭 시 선택 결과를 콘솔에 출력
    """
    def __init__(self, url: str, parent=None):
        print("Popup init 시작")
        super().__init__(parent)
        print("Popup 호출 완료")
        self.url = url

        self.output_path =  os.path.join(os.getcwd(), "downloads")
        os.makedirs(self.output_path, exist_ok=True)

        self.setWindowTitle("다운로드 옵션 설정")
        self.setFixedSize(400, 600)


        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"URL: {self.url}"))

        # ==========================
        # 품질 선택
        # ==========================
        layout.addWidget(QLabel("품질 선택:"))
        self.combo_quality = QComboBox()

        # 사용자에게 표시할 라벨과 실제 yt-dlp format 매핑
        self.quality_map = {
            "4K (2160p)": "bestvideo[height<=2160]+bestaudio/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "1440p (QHD)": "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "1080p (Full HD)": "bestvideo[height<=1080]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "720p (HD)": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "480p (SD)": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
        }

        self.combo_quality.addItems(list(self.quality_map.keys()))
        layout.addWidget(self.combo_quality)

        # ==========================
        # 포맷 선택
        # ==========================
        layout.addWidget(QLabel("저장 포맷:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems(["mp4(4k이하) 또는 webm(4k)"])
        layout.addWidget(self.combo_format)

        # ==========================
        # 자막 설정
        # ==========================
        layout.addWidget(QLabel("자막 다운로드:"))
        self.checkbox_subtitle = QCheckBox("자막 다운로드")
        self.checkbox_subtitle_only = QCheckBox("자막만 다운로드")
        layout.addWidget(self.checkbox_subtitle)
        layout.addWidget(self.checkbox_subtitle_only)


        # 다중 선택 가능한 언어 리스트
        self.subtitle_list = QListWidget()
        self.subtitle_list.setMaximumHeight(180)
        # self.subtitle_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.AsNeeded)
        for lang_label in ["한국어(ko)", "영어(en)", "태국어(th)"]:
            item = QListWidgetItem(lang_label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.subtitle_list.addItem(item)

        layout.addWidget(self.subtitle_list)
        self.subtitle_list.setEnabled(False)  # 기본적으로 비활성화

        self.checkbox_subtitle.stateChanged.connect(self._on_subtitle_toggle)  # 체크 상태 변화 시 콤보박스 활성/비활성
        self.checkbox_subtitle_only.stateChanged.connect(self._toggle_subtitle_only) # 체크 상태 변화 시 콤보박스 활성/비활성

        # ==========================
        # 세그먼트 (병렬 다운로드 수)
        # ==========================
        layout.addWidget(QLabel("동시 세그먼트 수:"))
        self.spin_fragments = QSpinBox()
        self.spin_fragments.setRange(1, 32)
        self.spin_fragments.setValue(16)
        layout.addWidget(self.spin_fragments)

        # ==========================
        # 저장 경로 선택
        # ==========================
        self.btn_select_path = QPushButton("저장 경로 선택")
        self.btn_select_path.clicked.connect(self._select_output_path)
        layout.addWidget(self.btn_select_path)

        # ==========================
        # # 하단 버튼 (취소 / 다운로드)
        # ==========================
        btn_row = QHBoxLayout()
        self.btn_cancel = QPushButton("취소")
        self.btn_ok = QPushButton("다운로드 시작")
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_ok)
        layout.addLayout(btn_row)

        self.setLayout(layout)

        # 이벤트 연결 (시그널)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._on_download_clicked)

    # -------------------------------------
    # 자막 체크 상태에 따라 언어 선택 제어
    # -------------------------------------
    def _on_subtitle_toggle(self, state: int):
        checked = (state == Qt.CheckState.Checked.value)
        self.subtitle_list.setEnabled(checked)
        # 자막 체크되면 '자막만' 옵션도 활성화
        self.checkbox_subtitle_only.setEnabled(checked)
        if not checked:
            self.checkbox_subtitle_only.setChecked(False)

    def _toggle_subtitle_only(self, state: int):
        """'자막만 다운로드' 체크 시 영상 관련 옵션 비활성화"""
        only = (state == Qt.CheckState.Checked.value)
        if only:
            # 자막만이면 자막 체크 강제 on
            if not self.checkbox_subtitle.isChecked():
                self.checkbox_subtitle.setChecked(True)
            self.combo_quality.setEnabled(False)
            self.combo_format.setEnabled(False)
            self.spin_fragments.setEnabled(False)
        else:
            self.combo_quality.setEnabled(True)
            self.combo_format.setEnabled(True)
            self.spin_fragments.setEnabled(True)

    def _get_selected_subtitles(self):
        langs = []
        for i in range(self.subtitle_list.count()):
            item = self.subtitle_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                label = item.text()
                if "(" in label and ")" in label:
                    langs.append(label[label.find("(") + 1:label.find(")")])
        return langs

    # -------------------------------------
    # 저장 경로 선택
    # -------------------------------------
    def _select_output_path(self):
        directory = QFileDialog.getExistingDirectory(self, "저장 폴더 선택")
        if directory:
            self.output_path = directory

    # -------------------------------------
    # 다운로드 버튼 클릭
    # -------------------------------------
    def _on_download_clicked(self):
        selected_label = self.combo_quality.currentText()
        format_string = self.quality_map[selected_label]

        self.result_data = {
            "url": self.url,
            "format": format_string,
            "container": self.combo_format.currentText(),
            "subtitle_only": self.checkbox_subtitle_only.isChecked(),
            "subtitle": self.checkbox_subtitle.isChecked(),
            "max_fragments": self.spin_fragments.value(),
            "output_path": self.output_path,
        }

        # 자막 받을 때만 언어 목록 포함
        if self.checkbox_subtitle.isChecked():
            self.result_data["subtitle_langs"] = self._get_selected_subtitles()
        else:
            self.result_data["subtitle_langs"] = []

        print("\n=== 다운로드 옵션 ===")
        for k, v in self.result_data.items():
            print(f"{k}: {v}")
        print("=====================\n")

        self.accept()  # 팝업 닫기
