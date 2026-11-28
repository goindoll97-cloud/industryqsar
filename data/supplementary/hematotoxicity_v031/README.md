# v0.31 — 골수·조혈계 손상 보완 및 특화 descriptor 예비 작업본

v0.29 전체 데이터 검증 작업과 병행하는 공개자료 기반 소규모 예비 실험 분기이다. 전체 A349/B8110/후보2519 원본은 이번 작업에 미확보. v0.29 데이터 동결 상태, 공개 v0.18 CSV 및 v0.26-pilot2 실험 기록은 변경하지 않는다.

- v0.30의 A32/B105를 A33/B102로 보완. Benzo[a]pyrene 추가(공식 NITE 분류 및 구조 감사, 원저 초록); formaldehyde, catechol, hydroquinone은 신규 미확인 대상에서 보류. 모든 final_label 공란.
- 골수·조혈계 근거 18행(12 CAS), 문헌 16건(철회 논문 M14는 사용 제외). 원저 초록/색인 발췌와 전문 검증 구분; 세포실험 또는 단순 보상성 조혈만으로 생체 내 Type 3 확정 금지.
- 기존 A benzene, 2-bromopropane, 2-methoxyethanol, ethylene glycol 근거 강화. NMP는 공식 전 경로 참조 유지, 흡입 Type 3 보류.
- HT01–HT10은 문헌에서 영감을 얻어 정의한 탐색적 구조 변수로 검증된 독성 규칙이 아니다. HT11–HT13은 별도 후보로 유지하며 기본 모델에 포함하지 않는다(HT11 A 1종; 나머지 A/B 모두 0). HT01–HT10 모두 0인 물질 A25/33, B100/102. 0은 무독성을 뜻하지 않는다.
- 기존 구조검출 테스트 31건, 추가 11건 통과 기록. v0.31 특성 생성 코드를 로컬에서 다시 실행하여 A/B 특성표와 coverage의 모든 셀 일치를 확인했다. 성능 실험은 미실행.
- A는 공식 혈액계 유해성 참조 후보, B는 미확인 대상이며 음성물질이 아니다. 전체 A/B 동결 전에는 본 실험 결과로 사용하지 않는다.

## 파일
물질별 A/B, A_evidence_v031.csv (70행), B_provenance_legacy.csv (131행; 보류 3종 포함), B_new_holds.csv; Marrow_Literature.csv, Marrow_Evidence.csv, Marrow_Descriptor_candidates.csv, Marrow_SMARTS_tests.csv; v0.30의 문헌·정의·SMARTS·검증 표; HT10 및 HT13 후보 특성표와 coverage를 포함한다. CSV는 로컬 산출물과 파싱된 셀 내용을 대조하였다. 줄바꿈/BOM/인용부호 등의 직렬화 차이는 있을 수 있다. 원문 전체나 전체 로컬 아카이브는 재게시하지 않는다.

## 재현 (기본 10개 변수 + Morgan)
```bash
cd data/supplementary/hematotoxicity_v031
python -m pip install -r requirements.txt
python generate_features.py --a Dataset_A_pilot_v031.csv --b Dataset_B_pilot_v031.csv --out reproduced
```
생성되는 NPZ와 feature_manifest.json은 코드로 재생성하므로 커밋하지 않는다. 추가 3개 후보의 SMARTS 및 검출 테스트는 별도 CSV로 제공한다. 전체 로컬 구축 스크립트/ZIP은 이 커밋에 포함하지 않는다.

다음: 전체 원본 확보, 구조 및 출처 확인, descriptor 출처 연구와 검증물질 간 중복 감사, 특성/데이터 동결 후 구조군 분할 평가. 기본 기준선은 Morgan+Maximum Tanimoto, 추가 후보는 Morgan 기반 one-class와 기전 특성 결합. 독성확률/실제 위해도/안전성 주장은 하지 않는다.
