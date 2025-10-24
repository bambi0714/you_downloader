## Semantic Versioning 커밋 컨벤션

| 형식                             | 설명                 | 버전 증가                    |
|--------------------------------|--------------------|--------------------------|
| `fix:`                         | 버그 수정              | patch (예: 1.0.0 → 1.0.1) |
| `feat:`                        | 새로운 기능             | minor (예: 1.0.1 → 1.1.0) |
| `feat!:` 또는 `BREAKING CHANGE:` | 대규모 변경             | major (예: 1.1.0 → 2.0.0) |
| `chore:` / `docs:`             | 비기능성 변경 (버전 증가 없음) | —                        |


커밋 예시
```
fix: ffmpeg 옵션 누락 수정
feat: 자막 다운로드 기능 추가
chore: PyInstaller 스크립트 정리
feat!: UI 구조 전면 리팩터링
```

자동 계산된 버전
```
v1.0.1  (path 버전 증가)
v1.1.0  (minor 버전 증가)
증가없음
v2.0.0  (major 버전 증가)
```

## Python semantic-release
### 설치
```bash
pip install python-semantic-release
```

### 설정 파일 생성 (pyproject.toml or semantic_release.yml)
pyproject.toml
```toml
[tool.semantic_release]
version_source = "tag"
upload_to_pypi = false
branch = "master"
changelog_file = "CHANGELOG.md"
commit_parser = "conventional"
version_variable = []

```
### 첫 실행 준비 (메인 브런치)
git tag v0.0.0
git push origin v0.0.0
