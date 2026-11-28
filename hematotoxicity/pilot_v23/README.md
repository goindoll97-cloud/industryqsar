# v0.23-pilot1 — 인체 중심 구조 유사성 예비실험

## 실행 (저장소 루트, Python 3.11 권장)

기존 hematotoxicity_v23.zip을 압축 해제하고 아래 --data에 두 CSV가 실제로 있는 폴더를 지정한다. 전체 로컬 자료의 공개 업로드를 하지 않았으므로 저장소만 복제해서는 실행되지 않는다. 원본 파일 해시가 일치해야 실행된다.

```bash
python -m pip install -r hematotoxicity/pilot_v23/requirements.txt
python hematotoxicity/pilot_v23/run_pilot.py --data path/to/hematotoxicity_v23 --out pilot_results
python hematotoxicity/pilot_v23/run_pilot.py --data path/to/hematotoxicity_v23 --out pilot_core_results --core-only
```

--out은 존재하지 않는 새 디렉터리를 사용한다.

## 고정 설계

- A 39종 중 인체 주 분석 잠정 참조 16종(핵심 9+직업성 확장 7), 동물 잠정 구조 기준 충족 4종(인체 중복 2). 조건 1 인체 16종, 조건 2 합집합 18종. 불확실 인체 20종 및 동물 신원 보류/종 특이 민감도 자료는 기본 제외. 동물 근거를 인체 양성으로 취급하지 않는다.
- B의 v23 신규 후보 색인 2,642종. CAS 및 InChIKey 연결성 기준 A/B 중복 금지. 배경 순위 평가에서는 동일 연결성 후보를 최대 점수 기준으로 통합(2,615 그룹), 실제 후보 순위 출력에는 모두 보존.
- Morgan binary fingerprint(radius=2, 2048 bits, chirality off), 최대 Tanimoto 유사도 단일 방법. 동일 구조에 두 종류 근거가 있어도 한 번만 비교. 점수는 독성 확률이 아니다.
- 동일 인체 참조의 leave-one-compound-out 및 유사 구조군 제외 평가. 구조군은 합집합에서 Tanimoto >= 0.50 또는 동일 연결성으로 연결한 single-linkage component. 두 조건에서 같은 holdout을 제외하며 동일 물질의 동물자료도 제외. 구조군 기준은 탐색용이며 외부검증이 아니다.
- 각 fold에서 제외된 인체 참조를 B 배경과 함께 순위화. 동률은 보수적으로 최하위 동률 순위 사용. 상위 1/5/10% 인체 참조 회수율 및 중앙 순위 비율 보고. B는 음성이 아니라 미확인 배경이며 AUROC, specificity, precision을 산출하지 않는다.
- 헤모글로빈 기능, 적혈구, 혈구/골수의 별도 최대 유사도 및 MW/logP/TPSA는 해석용 출력. 전체 순위에는 descriptor, 작용기 가중치, 농도 및 종별 가중치를 넣지 않는다. 최종 동률은 target_id 순. 0.3/0.5 유사도 기준은 기술적 분포이며 보정된 적용영역이 아니다.
- 9종 핵심 인체 참조만 사용하는 민감도 분석 제공. 동물 추가 효과는 참조 수 및 구조 분포 변화와 구별할 수 없는 탐색적 비교이다.

## 출력

| 파일 | 설명 |
|---|---|
| retrieval_metrics.csv | 두 holdout 방식의 집계 |
| holdout_predictions.csv | 인체 참조별 점수와 순위 |
| fold_membership.csv | holdout 구성과 종별 근거 |
| candidate_ranking.csv | 조건별 2,642종(5,284행), 독성 유형별 유사도, 근접 참조 |
| similarity_coverage.csv | 업종/공정 범위별 유사도 분포 |
| run_metadata.json | 입력 해시, RDKit 버전, 조건/한계 |

## 실제 로컬 실행 결과 (RDKit 2025.09.4)

[주 분석 집계](retrieval_metrics.csv), [핵심 인체 민감도 집계](retrieval_metrics_core.csv).

구조군 제외 평가에서 상위 5% 회수는 인체 단독 6/16, 동물 추가 5/16; 상위 10%는 각각 6/16. 상위 1%는 모두 0/16. 동물 추가의 개선 근거가 확인되지 않았다. 표본이 작고 독립 인체 검증자료가 없으므로 동물자료의 일반적 무용성이나 실제 유해성 판정으로 해석할 수 없다. 전체 자료와 개별 순위는 로컬 결과로 보존한다. 기존 v0.23 데이터와 라벨은 변경하지 않았다.
