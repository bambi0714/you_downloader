from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt


class ProgressDialog(QDialog):
    """
    다운로드 진행률 팝업
    - 제목 / 상태 텍스트 / 진행률 표시
    - 취소 버튼으로 다운로드 중단
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("다운로드 진행 중")
        self.setFixedSize(400, 200)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()
        self.label_status = QLabel("다운로드 준비 중...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.btn_cancel = QPushButton("취소")

        layout.addWidget(self.label_status)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def update_progress(self, percent, text):
        self.label_status.setText(text)
        self.progress_bar.setValue(int(percent))
