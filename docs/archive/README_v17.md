# IndustryQSAR — 반도체 제조공정 화학물질의 혈액독성 우선평가

**최신 기준 버전: v0.17 | 2026-11-27 | 데이터 구축 단계 (provisional)**

## 연구 목적

인체 흡입 혈액독성 근거와 분자구조적 특성을 활용하여 반도체 제조공정 관련 화학물질 중 정밀 독성평가가 필요한 물질의 우선순위를 제시한다. 한 가지 근거 기반 구조 유사성 스크리닝 방법에 집중한다. 독성 발생 확률, 만성 저농도 독성의 정량 예측, 백혈병 원인 규명 또는 안전성 판정은 연구 목표가 아니다.

*Prioritization of Potential Hematotoxicants in Semiconductor Manufacturing Based on Human Inhalation Evidence and Molecular Structural Characteristics*

## 최신 데이터 v0.17

| 데이터 | 물질 수 | 현재 상태 |
|---|---:|---|
| [Dataset A — 인체 흡입 혈액독성 참조](data/supplementary/hematotoxicity_v17/dataset_A_human_inhalation_references.csv) | 27 | 핵심 9, 직업성 확장 6, 불확실 12. 최종 라벨 0 |
| [Dataset B — 반도체 관련 후보 모집단](data/supplementary/hematotoxicity_v17/dataset_B_semiconductor_249.csv) | 249 | 잠정 유기 단일성분 110, 구조 미해결 55, 범위 외 84 |
| B의 신규 검토 후보 | 99 | 110종에서 A 중복 11종 제외. 독성 미평가 여부와 공정 사용 근거 추가 확인 필요 |

[데이터 설명 및 공개 범위](data/supplementary/hematotoxicity_v17/README.md) · [공정 출처 등록부](data/supplementary/hematotoxicity_v17/source_register.csv) · [집계/메타데이터](data/supplementary/hematotoxicity_v17/summary.json) · [최신 연구 프로토콜](docs/hematotoxicity_research_protocol_v17_ko.md)

독성 근거의 핵심 수집원은 ATSDR 및 PubMed 등재 원 연구 두 곳이다. PubMed 색인은 연구의 신뢰도를 보증하지 않으며, ATSDR의 인용 연구와 원 연구는 독립 증거로 중복 계산하지 않는다. 기존 Hua/Long 일반 혈액독성 자료 1,127종과 v0.9 이전 실험은 이력 보존용으로 두고 현행 핵심 분석에는 사용하지 않는다.

## 연구 진행

- [x] 반도체 관련 후보 모집단 249종 복원 및 CAS 목록 대조
- [x] 잠정 참조 27종과 대상 목록 통합 및 공개용 스냅샷 무결성 검사
- [ ] 참조 근거의 독립 재검증 및 추가 인체 혈액·골수독성 물질 확보
- [ ] 구조 식별 미해결 55종 및 CAS–구조 신원 확인; 적용범위 확정
- [ ] 공정·흡입 노출 및 기존 독성평가 여부 검증
- [ ] 구조 유사성 스크리닝 방법 사전 정의와 구조군 제외 검증
- [ ] 정밀평가 우선순위 및 불확실성 제시

## 공개용 데이터 검증

```bash
python data/supplementary/hematotoxicity_v17/validate_release.py
```

이 검사는 공개 CSV의 해시, 물질 수, 중복, 근거 수준, 스크리닝 역할 및 참조 연결을 검사한다. 독성 근거·CAS 신원·실제 노출의 독립 검증이나 모델 성능 검증을 대신하지 않는다.

공개 저장소에는 로컬 v0.17 원본의 핵심 컬럼만 정확히 추출하여 게시한다. 전체 근거표와 원자료, 원문 발췌, 상세 CDR 및 재현 입력 파일은 로컬 hematotoxicity_v17.zip 및 원본 파일에 보존한다. B의 249종은 후보 목록이며 현재 실제 공정 사용 또는 개인 노출 목록이 아니다. 비유기·혼합물 등 적용범위 밖 물질도 목록에 남겨 별도 검토한다. 자료 부족을 음성으로 간주하지 않는다.

## 이전 버전 및 코드

- [이전 v0.9 README 원문 보존](docs/archive/README_v09.md) (원문 상대 링크는 저장소 루트 기준)
- [v0.9 4개 출처 예비 자료](data/supplementary/hematotoxicity_four_sources_v09/)
- [v0.6](data/supplementary/human_inhalation_v06/), [v0.5](data/supplementary/human_inhalation_v05/), [v0.4](data/supplementary/human_inhalation_v04/), [v0.3](data/supplementary/human_inhalation_v03/), [v0.2](data/supplementary/human_inhalation_v02/)
- [이전 연구 프로토콜](docs/hematotoxicity_research_protocol_ko.md) — 현행 설계는 v0.17 프로토콜이 우선한다.

기존 루트 Python 코드와 테스트는 과거 LD50 예비 연구용이다. v0.17 스크리닝 모델은 아직 구현 또는 실행하지 않았다.
