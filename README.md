# IndustryQSAR — 반도체 제조공정 화학물질의 혈액독성 우선평가

**최신 데이터 작업본: v0.24-nite (공식 유해성 후보 추출 완료, 판정 대기) | 최신 실험: v0.23-pilot1 | 공개 A/B CSV: v0.18**

## 현행 연구 목적 및 방향

일본 정부 NITE GHS의 공식 혈액계 특정표적장기 독성(STOT) 분류와 분자구조적 특성을 이용하여 산업화학물질의 혈액계 유해성 평가 우선순위를 도출하고, 반도체 제조공정 관련 물질에 적용한다. ATSDR·PubMed 인체 흡입/직업성 근거를 활용해 인체 관련성을 별도로 검토한다. 공식 유해성은 인체 흡입 양성 또는 실제 위해도를 의미하지 않는다. 인체·동물 및 노출경로별 근거를 구분한다. 백혈병 인과 규명, 독성 발생 확률, 안전성 판정은 목표가 아니다. 최종 참조집합 및 실험 계획은 근거 정제 후 확정한다.

**[현행 연구 프로토콜 v0.24](docs/hematotoxicity_research_protocol_v24_ko.md)**

## 최신 작업 v0.24-nite — NITE 공식 분류 통합

[562종 공개 후보 색인](data/supplementary/hematotoxicity_v24_nite/nite_blood_public_index.csv) · [작업 설명](data/supplementary/hematotoxicity_v24_nite/README.md) · [실제 집계](data/supplementary/hematotoxicity_v24_nite/summary.json) · [재현 코드](data/supplementary/hematotoxicity_v24_nite/audit_nite.py) · [파일 manifest](data/supplementary/hematotoxicity_v24_nite/manifest.json)

| 자료 | 수량 및 상태 |
|---|---|
| NITE 전체 분류 항목 | 3,476 (Excel/상세 페이지 대조 완료) |
| 혈액계 STOT 분류 | 747행, 고유 단일 CAS 562종 |
| 기존 A에 없는 신규 검토 후보 | 537종 |
| 기존 B 구조 기준 충족 신규 후보 | 123종 (우선 검토 63종) |
| 골수·조혈계 표적 | 60종 |
| Dataset A | 기존 39종, 인체 주 분석 잠정 16종 유지 |
| Dataset B | 기존 8,110종, 현행 스크리닝 후보 2,642종 유지 |

NITE 분류 플래그만 기존 A/B에 병합했다. 신규 양성 라벨 0, 신규 모델 실행 없음. NITE에서 확인된 B 후보 123종은 향후 신규 미평가 우선순위와 분리하여 다룬다. 원본과 전체 상세 작업본은 로컬 hematotoxicity_v24_nite.zip에 보존. 공개 저장소에는 562종 후보 투영, 실제 추출 코드, 집계와 해시를 게시한다. 전체 A/B 공개 CSV는 v0.18 유지.

## 데이터 출처 원칙

NITE 공식 분류를 신규 참조 발굴의 핵심으로, ATSDR과 PubMed 원저를 인체/동물·경로·독성 근거 검토 및 인체 관련성 평가에 사용한다. EPA CompTox/PubChem은 화학물질 식별 및 구조 확인용. Hua/Long 1,127종은 문헌 검색 시드만. NIOSH 및 기타 기관은 당분간 보류한다. 동일 원저는 독립 증거로 중복 계산하지 않는다. 미등재 또는 자료 부족을 음성으로 해석하지 않는다.

## 이전 실험 v0.23-pilot1 — 인체 중심 예비실험

[실행 방법 및 분석 설계](hematotoxicity/pilot_v23/README.md) · [실행 코드](hematotoxicity/pilot_v23/run_pilot.py) · [예비실험 집계](hematotoxicity/pilot_v23/retrieval_metrics.csv)

인체 단독(16종)과 인체+동물(18종, 중복 제거)을 동일 Morgan/Tanimoto 방식으로 비교. 미확인 산업 후보 2,642종 배경에서 compound-out 및 구조군 제외 인체 참조 회수 평가 실행 완료. 구조군 제외 상위 5% 회수율은 각각 37.5%, 31.25%; 개선 미확인. 9종 핵심 인체 참조 민감도 실행 완료. 독립 검증이나 독성 분류 모델은 아직 없다. 기존 A/B 및 라벨을 변경하지 않음. 로컬 v0.23 ZIP의 원본 CSV를 입력으로 사용한다.

## 이전 데이터 작업 v0.23 — 인체·동물 흡입 근거 통합

[작업 manifest](data/supplementary/hematotoxicity_v23/summary.json) · [작업 설명](data/supplementary/hematotoxicity_v23/README.md)

A 39종(기존 인체 36종 유지, 신규 동물 전용 3종), B 8,110종 유지, 신규 후보 2,642종. 동물 잠정 근거 7종, 구조 기준 충족 4종. 인체 주 분석 잠정 참조 16종 유지. 최종 라벨 없음. 이후 v0.23-pilot1에서 탐색적 구조 유사성 실험을 실행했다. 전체 로컬 파일은 hematotoxicity_v23.zip, 공개 저장소에는 manifest만 등록.

## 이전 작업 v0.22 — 인체 혈액독성 문헌 근거 병합

[작업 manifest](data/supplementary/hematotoxicity_v22/summary.json) · [작업 설명](data/supplementary/hematotoxicity_v22/README.md)

A 36종(주 분석 잠정 16종 유지, 신규 불확실 근거 7종). B 8,110종 유지, 신규 후보 2,643종(참조 중복 6종 및 원소 탄소 범위 수정 1종 분리). 문헌 연결 861건 우선순위화; 66종 중 18종 개별 검토 및 추가 10종 판정. 남은 48종 개별 검토 대기. 전체 로컬 작업본 hematotoxicity_v22.zip, 공개 저장소에는 manifest만 등록. 최종 라벨 및 점수 없음.

## 이전 작업 v0.21 — EPA 전체 모집단 조회 병합

[작업 manifest](data/supplementary/hematotoxicity_v21/summary.json) · [작업 설명](data/supplementary/hematotoxicity_v21/README.md)

B 전체 8,110 CAS 조회 완료(8,112 반환행, 다중 매칭 2종 보류). 기존 v0.20 기준으로 잠정 구조 대조 통과 2,674종, A 중복 제외 신규 후보 2,650종. 구조 미확보 2,058종, 신원 재검토 766종, 적용범위 외 또는 범위 보류 2,612종. A 29종(주 분석 잠정 16) 유지. 신규 후보 중 기존 문헌 단서 66종을 우선 검토한다. 전체 파일은 로컬 hematotoxicity_v21.zip, GitHub에는 manifest만 공개한다. 독성 라벨, 최종 점수 및 모델 실행 없음.

## 이전 작업 v0.20 — EPA 우선 조회 실제 병합

[실제 작업 결과 manifest](data/supplementary/hematotoxicity_v20/summary.json) · [v0.20 작업 설명](data/supplementary/hematotoxicity_v20/README.md)

A 29종(주 분석 잠정 16), B 8,110종. EPA 우선 조회 2,020종을 실제 병합했으며, CAS 및 전체 InChIKey와 RDKit 계산이 일치하고 잠정 유기 단일성분 범위를 통과한 물질 779종(신규 762, 참조 중복 17). 미조회 기존 구조 52종을 포함한 잠정 구조 831종. 나머지 6,090종은 미조회이다. 전체 로컬 데이터 및 코드는 hematotoxicity_v20.zip에 보존하고 GitHub에는 manifest만 공개한다. 독성 판정은 변경하지 않았으며 점수와 최종 라벨은 없다.

## 이전 작업 v0.19 — 산업화학물질 확장

[실제 작업 결과 manifest](data/supplementary/hematotoxicity_v19/summary.json) · [v0.19 작업 설명](data/supplementary/hematotoxicity_v19/README.md)

A 29종(주 분석 잠정 참조 16종, 민감도 13종), B 8,110종(반도체 핵심 모집단 249종 보존). B의 잠정 유기 단일성분 237종 중 A 중복 25종을 제외한 212종이 신규 검토 후보이다. 반도체 121종 및 확장 산업 후보 91종. 구조 미해결 6,861종이며 대량 EPA 구조 등록부 확인은 미완료이다. 기존 1,127개 일반 혈액독성 후보는 신규 문헌 검색 시드로만 활용한다. 실험 방법/독성 판정 출처는 변경하지 않는다. 전체 로컬 작업본은 hematotoxicity_v19.zip에 보존하며 GitHub에는 v0.19 manifest만 등록했다. 공개 분석 CSV의 최신 버전은 아래 v0.18이다.

## 최신 공개 데이터 v0.18

| 데이터 | 물질 수 | 현재 상태 |
|---|---:|---|
| [Dataset A — 인체 흡입 혈액독성 참조](data/supplementary/hematotoxicity_v18/dataset_A_human_inhalation_references.csv) | 28 | 핵심 9, 직업성 확장 7, 불확실 12. 최종 라벨 0 |
| [Dataset B — 반도체 관련 후보 모집단](data/supplementary/hematotoxicity_v18/dataset_B_semiconductor_249.csv) | 249 | 잠정 유기 단일성분 134, 신원 미해결 1, 범위 외 114 |
| B의 신규 검토 후보 | 123 | 134종에서 A 중복 11종 제외. 독성 미평가 여부와 공정 사용 근거 추가 확인 필요 |

[데이터 설명 및 공개 범위](data/supplementary/hematotoxicity_v18/README.md) · [공정 출처 등록부](data/supplementary/hematotoxicity_v17/source_register.csv) · [집계/메타데이터](data/supplementary/hematotoxicity_v18/summary.json) · [당시 연구 프로토콜 v0.17](docs/hematotoxicity_research_protocol_v17_ko.md)

v0.18 당시 독성 근거의 핵심 수집원은 ATSDR 및 PubMed 등재 원 연구 두 곳이었다. PubMed 색인은 연구의 신뢰도를 보증하지 않으며, ATSDR의 인용 연구와 원 연구는 독립 증거로 중복 계산하지 않는다. 기존 Hua/Long 일반 혈액독성 자료 1,127종과 v0.9 이전 실험은 이력 보존용으로 두고 현행 핵심 분석에는 사용하지 않는다.

## 연구 진행 및 다음 단계

- [x] 반도체 후보 249종 보존 및 산업 모집단 8,110종 통합
- [x] EPA 전체 CAS 조회 및 잠정 구조 검증
- [x] 기존 인체·동물 분리 참조 A 39종 구축
- [x] v0.23-pilot1 기준선 및 내부 구조군 제외 평가
- [x] NITE 공식 분류 562종 추출, 기존 A/B 플래그 병합
- [ ] NITE 전체 후보의 구조·산업 적용범위 확인
- [ ] 구조 확보 신규 123종 중 우선 검토 63종의 인체·동물 및 흡입/조혈계 근거 판정
- [ ] NITE 공식 유해성 참조와 인체 흡입 검증 역할 확정, 구조/근거 누출 방지
- [ ] A/B 재병합, 알려진 참조와 미확인 후보 분리
- [ ] 동일 검증 조건에서 기준선 및 확대 참조 비교
- [ ] 실제 반도체 관련성 검토 및 정밀평가 우선순위 도출

## 공개용 데이터 검증

```bash
python data/supplementary/hematotoxicity_v18/validate_release.py
```

이 검사는 공개 CSV의 해시, 물질 수, 중복, 근거 수준, 스크리닝 역할 및 참조 연결을 검사한다. 독성 근거·CAS 신원·실제 노출의 독립 검증이나 모델 성능 검증을 대신하지 않는다.

공개 저장소에는 로컬 v0.18 원본의 핵심 컬럼만 정확히 추출하여 게시한다. 전체 근거표와 원자료, 원문 발췌, 상세 CDR 및 재현 입력 파일은 로컬 hematotoxicity_v18.zip 및 원본 파일에 보존한다. B의 249종은 후보 목록이며 현재 실제 공정 사용 또는 개인 노출 목록이 아니다. 비유기·혼합물 등 적용범위 밖 물질도 목록에 남겨 별도 검토한다. 자료 부족을 음성으로 간주하지 않는다.

## 이전 버전 및 코드

- [v0.17 이전 통합 데이터](data/supplementary/hematotoxicity_v17/); 당시 방법은 v0.17 프로토콜 참조.

- [이전 v0.9 README 원문 보존](docs/archive/README_v09.md) (원문 상대 링크는 저장소 루트 기준)
- [v0.9 4개 출처 예비 자료](data/supplementary/hematotoxicity_four_sources_v09/)
- [v0.6](data/supplementary/human_inhalation_v06/), [v0.5](data/supplementary/human_inhalation_v05/), [v0.4](data/supplementary/human_inhalation_v04/), [v0.3](data/supplementary/human_inhalation_v03/), [v0.2](data/supplementary/human_inhalation_v02/)
- [이전 연구 프로토콜](docs/hematotoxicity_research_protocol_ko.md) — 현행 방향은 v0.24 프로토콜이 우선한다.

기존 루트 Python 코드와 테스트는 과거 LD50 예비 연구용이다. 현행 NITE 기반 실험은 아직 실행하지 않았으며 v0.23-pilot1만 탐색적 내부 평가를 완료했다.
