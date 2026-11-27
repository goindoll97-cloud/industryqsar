# 인체 흡입 혈액독성 근거 데이터 v0.2 (2026-11-27)

인체 생체 내 흡입만 학습/검증 대상으로 한다. 농도/기간에 일률적인 제한은 두지 않는다. 동물, 시험관 단독, 비흡입, 경로 미확인 근거는 학습에 사용하지 않는다. 직업성 공기 중 노출과 다른 경로의 동시 노출 가능성은 별도 검토한다.

## 실제 작업 결과

- 원본 ATSDR CSV 11,724행, SHA-256 170e849fface5973258561a5b0eaf9efc9b8296974667a892314dd7ebc05f5c9.
- 기존 인체 관련 949개 후보(157개 보고서)와 전체 탐색의 인체+흡입 키워드 후보 합집합: 949개. 모두 후보이지 확정 연구가 아니다.
- 기존 14개 예비 관찰을 포함하여 21개 물질의 49개 인체 관찰 레코드 구축(혈액학 45, 혈액종양 4); 경로 불명확 관찰 1건 별도 격리. 연결 원본 문맥 90개. 동일 연구의 노출군 및 복수 인용문헌 묶음 포함.
- 혈액학: 유해영향 신호 7, 혈액학적 변화 7, 조건부 영향 미관찰 23, 불확실 8.
- 물질 수준 예비 상태: 유해영향 후보 5, 조건부 영향 미관찰만 6, 변화 또는 불확실 10. 혈액암 근거는 별도 집계.
- CAS/SMILES 후보 매핑 21개. 독립 레지스트리 검증 전이며 최종 이진 학습 라벨 0개.
- 별도 양성 참조 신호: 벤젠(Lan et al. 2004, https://pmc.ncbi.nlm.nih.gov/articles/PMC1256034/), 니트로벤젠(Lee et al. 2013, https://pmc.ncbi.nlm.nih.gov/articles/PMC3916109/), 1,3-디니트로벤젠(Okubo and Shigeta 1982, https://pubmed.ncbi.nlm.nih.gov/7153063/; 경피 기여 가능성 검토 필요). 기존 ATSDR 인용과 중복되므로 독립 연구로 중복 집계하지 않음.
- 혈액종양 사례: 에틸렌옥사이드(Steenland et al. 2004, https://pmc.ncbi.nlm.nih.gov/articles/PMC1757803/), 부타디엔(Sathiakumar et al. 2021, https://pmc.ncbi.nlm.nih.gov/articles/PMC8606437/) 등. 일반 혈액학적 영향 미관찰이 발암성 음성을 의미하지 않는다.

## 로컬 산출물

human_inhalation_hematotoxicity_v02.zip: human_inhalation_review_queue.csv, human_inhalation_study_evidence.csv, hematologic_cancer_evidence.csv, chemical_evidence_summary.csv, reviewed_source_contexts.csv, route_uncertain_excluded.csv, training_labels_pending.csv(빈 확정 라벨 양식), summary.json, 후보 구조 매핑/수기 정리/재현 스크립트 및 참조 근거 파일. 원자료와 원문 발췌는 공개 저장소에 게시하지 않았다. 정리된 예비 근거 및 출처 위치 메타데이터의 보충자료 스냅샷은 [공개 데이터 디렉터리](../data/supplementary/human_inhalation_v02/)에서 확인한다. 확정 학습자료는 아니다.

## 제한 및 다음 작업

전체 949개 문맥을 완전 판정한 것은 아니다. ATSDR 원 PDF 전체와 각 인용 논문 전문 검토는 미완료. IRIS/OEHHA 기존 원본 통합은 미완료. 적절한 음성 근거가 확보되기 전에는 지도학습 및 분류 성능을 주장하지 않는다. 인간 흡입 자료만으로 규모가 부족하면 양성 유사물질 기반 탐색과 적용영역 경고로 시작하고 실제 검증 수준을 명시한다. 동물 자료로 대체하지 않는다.
