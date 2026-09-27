# 서울사랑상품권 가맹점 현황 시각화 대시보드

<img width="1418" height="792" alt="Image" src="https://github.com/user-attachments/assets/4e4c0107-fceb-48b1-b8fc-9435671a5d9d" />

엑셀(`.xlsx`, `.xls`) / CSV 파일을 업로드해 웹에서 시각화하는 Streamlit 대시보드.

> **현재 상태: 스켈레톤 단계.** 계층 구조와 클래스 배선은 갖춰져 있지만, 데이터 로딩·정제·차트 생성 등 핵심 로직은 아직 채워지지 않은 부분이 많습니다. 상세 설계는 [dashboard_design.md](dashboard_design.md) 참고.

## 기술 스택

- 데이터 처리: `pandas`, `openpyxl`, `pyarrow`
- 시각화: `plotly`
- UI: `streamlit`
- 검증: `pydantic`

## 요구 사항

- Python 3.9 이상

## 설치

```bash
pip install -r requirements.txt
```

## 실행

저장소 루트에서:

```bash
python -m streamlit run dashboard/app.py
```

## 참고

- 계층별 책임, 데이터 흐름 등 전체 설계는 [dashboard_design.md](dashboard_design.md)에 있습니다.
- 코드 위주로 문서와 실제 구현이 계속 바뀌는 중이라, 두 문서가 잠깐씩 어긋날 수 있습니다 — 최종 기준은 코드입니다.