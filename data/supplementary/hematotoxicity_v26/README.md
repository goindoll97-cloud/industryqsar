# v0.26-pilot2 — 공식 유해성 및 흡입 보완 참조 확대

## 완료 작업
사용자가 실행한 v0.25 결과: NITE 562종 모두 EPA 조회, RDKit 구조 정합성 통과 332종, 보류 230종. 구조 통과 332종은 공식 전 경로 유해성 후보이며 인체 흡입 양성이 아니다.
기존 A 39에 신규 NITE 310을 추가하여 A 349종. B 8,110종 보존, 기존 후보 2,642종에서 NITE 분류 확인 123종 분리하여 2,519종. 전체 NITE 플래그 B 234종, A 335종(기존 A 구조 보류 3종 포함).
NITE 구조 확보 근거 417행 중 기존 인체 26행과 신규 동물 56행(40행 포함, 16행 보류) 총 82행 요약 검토. 신규 동물 흡입 보완 36종; 인체 요약 단서 7종은 판정 대기. NMP 전신/두부 차이 및 2-butoxyethanol 종간 민감성 등 보류. 335행 미검토. 원저 독립 검증 및 신규 최종 라벨 없음.

## 실험
동일 2,519 CAS(2,492 연결성) 배경, Morgan radius 2 / 2048, 최대 Tanimoto. 인체 16, 인체+기존 동물 18, 인체+NITE 전 경로 336, 인체+기존 동물+NITE 동물 흡입 요약 49. 합집합 336종에 동일 구조군 단일연결 >=0.5: 209군, 최대 71종(인체 4종). CAS 및 연결성 제외. 인체 16종 동일 평가; core9는 평가 부분집합, 참조 풀 변경 없음.

구조군 제외 Top5% 회수 18.75/18.75/0/0%; Top10% 18.75/18.75/0/18.75%. 전체 후보 최대 유사도 >=0.5 비율 0.75/0.83/13.42/3.65%. 구조 포괄성 확대와 상위 회수 개선은 동일하지 않다. NITE 전 경로 336은 의약품 등 산업 적용성 및 경로를 아직 정제하지 않은 탐색 집합이다. v0.23과 공통 배경 및 그룹 정의가 달라 수치의 직접 비교 금지. 인체 원저의 NITE 인용 가능성, 16종 소표본, 내부 검증 한계 기록. 음성·확률·AD·위해도 주장 금지.

## 공개 범위와 재현
[summary.json](summary.json), [retrieval_metrics_rounded.csv](retrieval_metrics_rounded.csv), [coverage_rounded.csv](coverage_rounded.csv), [manifest.json](manifest.json) 공개. 전체 A/B 및 실행 코드, 수동 근거 검토표, 순위/폴드별 상세는 사용자 로컬 hematotoxicity_v26.zip에 보존. 전체 공개 A/B CSV는 v0.18 유지. NITE v0.24 공개 색인 유지.

RDKit 2025.09.4. 로컬 ZIP의 run_v26.py, animal_summary_review.tsv, input_hashes.json 동일 폴더. 실행:
```powershell
python run_v26.py --base hematotoxicity_v23 --review nite_v25_review --nite-index hematotoxicity_v24_nite/nite_blood_candidates_merged.csv --out results_reproduced
```
원본 v0.23, v0.24, v0.25 압축 해제 파일 필요. 신규 EPA 원본 CSV는 별도 보존 필요. 공개 파일은 집계이며 재현 원본 아님.
