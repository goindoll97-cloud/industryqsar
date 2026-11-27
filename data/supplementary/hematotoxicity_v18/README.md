# v0.18 — provisional public projection

기존 v0.17 두 데이터셋과 연구 프로토콜 유지. A 28종(핵심 9, 확장 7, 불확실 12), B 249종(잠정 유기 단일성분 134, 범위 외 114, 신원 보류 1); A 중복 11종 제외 후 신규 검토 123종.

## 변경 사항
- A 기존 10종의 수집된 PubMed 원저 초록 재검토. 4-Chloroaniline 1종 확장 참조 추가 (PMID 18608262; 경피 기여 미분리). Tetrachloroethylene endpoint 분류 수정, 불확실군 유지. 다른 기존 참조는 상속 판정이다.
- B 기존 미해결 55종 중 26종 PubChem CAS/name/CID 연결을 확인하고 이름 기반 그래프를 복원하여 RDKit으로 점검. 독립 registry InChIKey 전수 비교는 미완료. 28종은 무기물·혼합물·고분자 등 범위 외, 1종 CAS–명칭 충돌 보류. 기존 적격 CO와 1,2-dichloroethylene 혼합물도 범위 외로 재분류.
- 원래 모집단, 원래 ID 및 출처 추적 정보 유지. 589-81-1은 원본 명칭과 CAS 충돌로 보류. 범위 외는 무독성 의미가 아니다.
- 공개용 CSV는 로컬 v0.18 원본의 핵심 컬럼 정확한 투영본. A의 evidence_review_v18 및 B의 identity_review_v18과 관련 출처/설명 컬럼 추가. 상세 근거 및 재현 스크립트는 로컬 hematotoxicity_v18.zip 보존.
- final_label 및 priority_score 모두 비어 있음. 신규 후보의 실제 공정 사용/흡입 노출 및 독성 미평가 여부는 전수 확인 전이다. 성능 검증과 스크리닝 모델 실행은 미수행.

[현행 프로토콜](../../../docs/hematotoxicity_research_protocol_v17_ko.md), [v0.17 공정 출처 등록부](../hematotoxicity_v17/source_register.csv).
