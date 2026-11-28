# IndustryQSAR — 반도체 제조공정 화학물질의 혈액독성 우선평가

**최신 데이터 작업본: v0.29-validation-in-progress (정밀 검증 진행 중) | 최신 실험: v0.26-pilot2 | 공개 A/B CSV: v0.18**

## 현행 연구 목적 및 방향

일본 정부 NITE GHS의 공식 혈액계 특정표적장기 독성(STOT) 분류와 분자구조적 특성을 이용하여 산업화학물질의 혈액계 유해성 평가 우선순위를 도출하고, 반도체 제조공정 관련 물질에 적용한다. ATSDR·PubMed 인체 흡입/직업성 근거를 활용해 인체 관련성을 별도로 검토한다. 공식 유해성은 인체 흡입 양성 또는 실제 위해도를 의미하지 않는다. 인체·동물 및 노출경로별 근거를 구분한다. 백혈병 인과 규명, 독성 발생 확률, 안전성 판정은 목표가 아니다. 최종 참조집합 및 실험 계획은 근거 정제 후 확정한다.

**[현행 연구 프로토콜 및 인수인계 v0.29](docs/hematotoxicity_research_protocol_v29_ko.md)** · **[v0.28 역사적 인수인계](docs/hematotoxicity_handoff_v28_ko.md)**

## 최신 작업 v0.29 — 데이터 검증 후속

[실행 결과 및 v0.28 감사 정정](data/supplementary/hematotoxicity_v29/README.md) · [실행 집계](data/supplementary/hematotoxicity_v29/summary.json) · [파일 해시](data/supplementary/hematotoxicity_v29/manifest.json)

v0.27 원본 417행 독립 보수적 자동 선별, 2,235 단위, 단위 테스트 7개 통과. 40 구조 보류 재계산 결과 37종 표준화 차이 후보(기존 A 3, 신규 34), 3종 보류 유지. 인체 16종 중 12종 신규 출처 확인(원저 관련 절 2, 초록 전문 1, 색인 부분 8, 제목만 1). MBT 치료 교란 보류 권고, v0.28 신규 동물 단서 2행도 모두 편입 보류. v0.28 323행은 자동 전문 처리이지 독성학적 수동 검증 완료가 아니다. 149건 골수 문구는 직접 손상 확정 아님. 기존 A349/B8110/후보2519 및 예비실험 유지, 신규 양성 0. v0.28 전체 ZIP/workbook 및 신규 EPA 원본 미확보로 전체 재실행은 대기. 로컬 hematotoxicity_v29_validation.zip에 실제 실행 코드와 결과 보존.


## 이전 작업 v0.28 — 공식 분류 근거 전수 재도출 및 노출경로·독성유형 분류

[작업 설명](data/supplementary/hematotoxicity_v28/README.md) · [영문 설명](data/supplementary/hematotoxicity_v28/README_EN.md) · [데이터 사전](data/supplementary/hematotoxicity_v28/DATA_DICTIONARY.md) · [물질별 공개 색인](data/supplementary/hematotoxicity_v28/nite_evidence_public_index.csv) · [417행 판독 결과](data/supplementary/hematotoxicity_v28/S05c_v27_evidence_review_reconciliation.csv) · [실행 집계](data/supplementary/hematotoxicity_v28/summary.json) · [공백 등록부](data/supplementary/hematotoxicity_v28/S11_gap_register.csv) · [재현 코드](data/supplementary/hematotoxicity_v28/code) · [manifest](data/supplementary/hematotoxicity_v28/manifest.json)

NITE 공식 다운로드 페이지에 분류 근거 전문 일괄 파일 `list_rational_e.xlsx`(117,026행)가 있음을 확인했다. v0.24~v0.27 입력 목록에 없던 파일이다. 따라서 v0.27에 남아 있던 323행 부분 검토 대신 **혈액계 분류 749행 전체**의 근거 원문을 재도출하여 **3,634개 근거 단위**로 분할하고 각 단위 원문을 보존했다.

| 재현 검증 | v0.24~v0.27 기록 | v0.28 재도출 |
|---|---:|---:|
| 혈액계 STOT 근거행 | 747 | 747 (완전일치) |
| 단일 CAS | 562 | 562 전부 회수, 누락 0 |
| 골수·조혈계 표적 | 60 | 60 (완전일치) |

근거종·노출경로·독성유형을 **전체 셀이 아닌 개별 근거 단위 단위로** 판정했다. 하나의 NITE 근거 셀에 인체 직업성·동물 흡입·동물 경구 자료가 연속 문장으로 함께 기술되므로, 전체 셀 키워드로는 "흡입 언급"과 "흡입시험에서 확인된 혈액독성"을 구분할 수 없다. 근거 수준은 tier A 인체 흡입 11종, B 29, C 143, D 동물 흡입 47, E 168, F 99, G 69. 독성유형은 Type 1 163종, Type 2 376종, Type 3 268종, 응고계 88종. Type 3은 보상성 조혈 반응을 분리해 골수손상 지지 149종, 말초 혈구수 변화만 96종, 보상성 단독으로 **골수손상 판정 보류 23종**으로 구분했다.

확인된 주요 사항. 562종 중 **5종은 혈액응고계 단독 분류**로 Type 1~3 틀 밖이며 규칙 R02로 분리했다(Estrone, Chlormadinone acetate 등 두 스테로이드는 혈전 경향으로 기전상 반대 방향). NITE가 한 셀에 CAS를 두 개 기재해 **v0.24에서 2종이 누락**되었고, 그중 Thiouracil은 혈액계 STOT-RE Category 1이며 thiouracil계는 무과립백혈구증의 확립된 원인물질이다. 혈액계 근거 인용 3,007건 중 원저 시험보고서 직접 인용은 249건뿐이고 **tier A 인체 흡입 11종 중 원저 학술논문을 인용한 물질은 없다**. 즉 NITE 분류는 공식 유해성과 그 근거를 확립하지만 인체 흡입 혈액독성의 원저 검증을 대체하지 않는다.

공개 v0.18 인체 참조 28건을 공식 분류와 대조했다. Naphthalene·Methanethiol은 tier A, Benzene·2-Bromopropane은 tier B로 교차 확인된다. 반면 **4건은 공식 NITE 혈액계 분류가 전혀 없으며 그중 3건이 최상위 `1_core`** 이다(4-Bromo-2-fluoroaniline, 5-Amino-2-(trifluoromethyl)pyridine, Dichloromethane, 그리고 2-Ethoxyethyl acetate). tier A 5종은 PubMed 원저를 탐색·열독해 수동 판정했고 **5건 중 3건에서 원저가 NITE 요약의 주장을 제한**했다(2-Ethoxyethanol은 장갑 중재로 경피 기여 시사, 1,2-Dichloropropane은 혼합제품·경구, Lindane은 경피 주류).

### v0.27 로컬 아카이브 병합 결과

`hematotoxicity_v27_supplement.zip` 를 확보·검증했다. 아카이브 SHA-256이 공개 manifest 기록값과 일치하고 **기록된 내부 파일 해시 31개 전부 일치**(불일치·누락·미기록 0).

구조 확보 417행을 복원해 94검토 / 323대기 분할을 정확히 재현하고, **323행 전부를 전문 판독**했다. 결과: 동물 소견 다른·미해결 경로 169, 인체 소견 경로 분리 불가 89, 근거종 미해결 44, 독성지표 없음 19, **동일 단위 내 동물 흡입 2, 인체 흡입 0**. 즉 **전수 판독으로 신규 동물 흡입 2행, 신규 인체 흡입 0행**이며, `no_inhalation_text_cue` 분류 행이 흡입 소견으로 전환된 사례는 없다. 기존 우선순위 검토가 타당했고 이 자료에 대한 추가 전수 검토는 불필요하다.

Dataset A 349종을 CAS 기준 병합(335종 매칭, 14종 미매칭)했고 `final_label` 은 **349종 전부 공란 유지**. 구조 교차검증에서 단일성분 유기 390종 중 완전일치 331, 연결성만 일치 42, 충돌 4. **연결성만 일치 42건은 EPA가 비표준 InChIKey(`...NA-N`)를 저장한 계통적 인공산물**이며 연결성은 전부 동일하다. v0.27 `same_connectivity_only_hold` 의 원인으로, 해제 시 구조 확보 참조가 실질 증가한다. 실제 유기물 신원 충돌은 4건(Vernolate는 PubChem 오매칭, EPA 정확)이고 전체 24건 중 23건은 무기물이다.

STEP 6 공백은 해소 대신 **영향 범위를 확정**했다. TRI 전용 28종 중 스크리닝 후보에 포함된 것은 9종(0.36%)으로 전부 농약·제초제이며 흡입 후보·인체 플래그·반도체 관련 없음. 반도체 핵심 인용 대기 4건 중 3건은 독립 심사논문 출처를 보유하고, 미인용 표 단독 의존은 1건(CAS 25322-68-3 중합체)이며 이미 `outside_domain` 이므로 **분석 영향 없음**.

**신규 확정 양성 라벨 0건, 독립 원저 전문 검증 완료 0건, 신규 모델·실험 없음.** PubChem 구조감사(570 CAS 중 단일성분 유기 390)는 EPA 기반 S03을 대체하지 않으며 EPA CompTox가 기준 등록 체계다. 검증 44건 통과·0건 실패·미확보 입력 1건은 `SKIP`으로 보고. 사항 14건을 공백 등록부에 기록했고 `G01`·`G02`·`G03` 은 해소, `G06`·`G07`·`G08` 은 범위 확정 또는 부분 해소다. 전체 보충자료는 로컬 `hematotoxicity_v28.zip`(632 파일), 공개 저장소는 관례대로 근거 원문과 Dataset A/B 전체를 재게시하지 않고 집계·문서·해시·물질별 색인·판독 결과·코드만 게시한다.


## 이전 작업 v0.27 — 보충자료 정제 및 근거 검토

[작업 설명](data/supplementary/hematotoxicity_v27/README.md) · [실행 집계](data/supplementary/hematotoxicity_v27/summary.json) · [로컬 파일 해시](data/supplementary/hematotoxicity_v27/manifest.json)

NITE 562종/747행과 구조 332종, B 후보 2,519종 재검증. 기존 A 349/B 8,110 유지. 구조 통과 근거 417행 중 요약문 검토 94행(신규 12), 추가 발췌문 선별 28, 자동 단서만 295; 전체 요약문 검토 대기 323행. 인체 16종 재점검(원저 관련 절 2건) 및 동물 원보고서 관련 절 1건 확인; NITE 동물 흡입 보완 39종 잠정. TRI 28종 기관 URL 보완(원래 등재 목록 버전 독립 확인 대기). S1~S10 제출 전 작업본 생성, S11 미생성. 공식 분류/구조 스냅샷만 고정; 원저 및 경로/endpoint 최종 판정 미완료, 신규 라벨/모델 없음. 전체 보충자료 및 코드 로컬 hematotoxicity_v27_supplement.zip, GitHub는 집계와 문서/해시만 공개.


## 이전 작업 v0.26-pilot2 — NITE 구조 검증 및 참조 확대 실험

[작업 설명](data/supplementary/hematotoxicity_v26/README.md) · [실험 집계](data/supplementary/hematotoxicity_v26/retrieval_metrics_rounded.csv) · [구조 포괄성](data/supplementary/hematotoxicity_v26/coverage_rounded.csv) · [manifest](data/supplementary/hematotoxicity_v26/manifest.json)

NITE 562종 EPA 조회 완료, 구조 통과 332종(230종 보류). A 349종(기존 39 + 신규 310), B 8,110종 유지, 알려진 NITE 후보 123종 분리 후 미확인 2,519종. NITE 417 근거행 중 82행 요약 검토, 동물 흡입 보완 36종 잠정 선정; 인체 16종 및 최종 라벨 공란 유지. 네 조건(16/18/336/49종) 동일 배경 비교에서 구조군 제외 Top5% 회수율 18.75/18.75/0/0%. 후보 유사도 증가에도 인체 회수 개선 없음. 내부 탐색 검증, 독립 검증 및 원저 판정 미완료. 전체 코드와 A/B는 로컬 hematotoxicity_v26.zip 보존, GitHub는 공개 집계 및 manifest 게시. 다음은 잔여 335행 근거 검토 및 기전별 스크리닝 설계.


## 이전 작업 v0.24-nite — NITE 공식 분류 통합

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
- [x] NITE 562종 EPA 전체 조회 및 구조 332종 정합성 확인
- [ ] 공식 전 경로 참조의 산업 적용범위 확인
- [x] NITE 인체 26행 및 동물 56행 요약 검토
- [ ] 잔여 335행 및 원저 검증
- [ ] NITE 공식 유해성 참조와 인체 흡입 검증 역할 확정, 구조/근거 누출 방지
- [x] 잠정 A/B 재병합, NITE 확인 123종 분리
- [x] 동일 검증 조건에서 4개 기준선/확대 참조 비교
- [ ] 기전별 스크리닝 사전 정의 및 비교
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
- [이전 연구 프로토콜](docs/hematotoxicity_research_protocol_ko.md) — 현행 방향은 v0.27 프로토콜이 우선한다.

기존 루트 Python 코드와 테스트는 과거 LD50 예비 연구용이다. v0.23-pilot1 및 v0.26-pilot2 탐색적 내부 평가 완료. 최종 검증은 미완료.
