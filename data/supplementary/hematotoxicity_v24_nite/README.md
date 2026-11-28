# v0.24-nite — 공식 혈액계 분류 후보 staging

[현행 연구 프로토콜](../../../docs/hematotoxicity_research_protocol_v24_ko.md) · [NITE 공식 다운로드](https://www.chem-info.nite.go.jp/chem/english/ghs/ghs_nite_download_e.html)

## 실제 작업 결과

3,476 Excel 항목과 3,476 상세 페이지, 6,952 STOT 행 대조. 혈액계 Category 1/2 분류 747행, 단일 CAS 562종, 미확정 6행. 기타 표적장기 표기 차이 2행(혈액계 판정 동일). 원본 캐시 HTML 해시를 대조했다. 개별 분류 연도 FY2006~FY2025. NITE 데이터는 다양한 종과 노출경로, read-across 근거를 포함한다.

- 기존 A와 중복 25; 신규 검토 537.
- 신규 중 기존 B 구조 기준 충족 123, 기존 B 보류 91, B 외 323.
- 골수/조혈계 표적 60; 동일 근거행 인체·흡입 키워드 152(검색 단서만).
- 구조 기준 충족 신규 123 중 우선 검토 63.
- A 39 / 인체 주 분석 잠정 16 / B 8,110 / 기존 후보 2,642 유지. 신규 확정 라벨 0, 신규 모델 실행 없음.

## 공개 파일과 로컬 보존

- [nite_blood_public_index.csv](nite_blood_public_index.csv): 원본 통합 목록 562종의 11개 컬럼 공개용 투영. CAS, 공식 source ID·분류연도, SE/RE, 골수·조혈계 표적, 인체·흡입 단서, A/B 대조, 기존 B 상태, 검토 우선순위. 단순 검색 단서 또는 공식 분류이며 인체 양성 라벨이 아니다. source ID는 공식 통합 목록/상세 페이지에서 확인한다. 전체 562행을 로컬 CSV에서 동일 규칙으로 추출한 결과와 Git blob 해시 일치.
- [summary.json](summary.json): 실제 로컬 집계 원본.
- [audit_nite.py](audit_nite.py): 실제 로컬 재현 코드 원본.
- [manifest.json](manifest.json): 로컬 파일 SHA256, 공개 파일 범위 및 연구 버전.
- [validate_public_index.py](validate_public_index.py): 공개 CSV 무결성/수량 점검.

전체 상세 근거 747행, NITE 원본 Excel 및 HTML ZIP, A/B 전체 플래그 병합본 및 원본 문헌 등은 사용자 로컬 자료에 보존(hematotoxicity_v24_nite.zip). 공개 저장소는 원본 분류 근거 문장이나 전체 산업 원자료를 재게시하지 않는다. 전체 분석 A/B 공개 CSV 버전은 v0.18 유지. NITE 공개 후보 목록은 v0.24이지만 확정 학습자료가 아니다.

## 재현

전체 원본 세 가지(사용자 제공 list_nite_all_e.xlsx, official_nite_results.zip, v0.23 압축 해제 폴더)가 있어야 한다. audit_nite.py는 artifact_tool 설치 환경에서 실행한다(일반 환경에서 설치/실행을 별도 검증하지 않음).

```bash
python data/supplementary/hematotoxicity_v24_nite/validate_public_index.py
python data/supplementary/hematotoxicity_v24_nite/audit_nite.py --excel list_nite_all_e.xlsx --zip official_nite_results.zip --base hematotoxicity_v23 --out nite_audit_out
```

v0.23 예비실험은 기존 해시 일치 입력으로만 재실행한다. NITE 플래그 파일을 기존 예비실험 입력으로 바로 대체하지 않는다.
