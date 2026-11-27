# v0.19 — 산업화학물질 확장 작업본 (로컬 데이터, 공개 manifest)

최신 작업 버전은 v0.19이며 전체 공개 CSV 스냅샷은 v0.18이다. v0.19의 전체 A/B CSV 및 실행 코드는 대화에서 생성한 로컬 hematotoxicity_v19.zip에 보존되어 있다. 이 폴더에는 실제 생성된 결과 집계와 로컬 파일 SHA256만 공개한다. 이 폴더가 전체 데이터의 업로드를 의미하지 않는다.

- A: 29종(핵심 9, 직업성 확장 7, 민감도 13). Formaldehyde는 상충 근거 때문에 민감도 분석 전용 추가. 주 분석 16종 유지.
- B: 8,110 CAS, 반도체 249종 보존. CDR A2 7,833종과 TRI 단독 28종은 반도체 사용 확증이 아니라 산업 확장 후보이다. 전자·전기제품 업종 428종, 공정기능 후보 1,618종을 우선 처리한다.
- B: 237종 잠정 유기 단일성분, 212종 신규 검토 후보, 25종 참조 중복, 6,861종 구조 미해결, 1,012종 적용범위 외 또는 잠정 범위 보류. 이름 규칙으로 보류한 경우 최종 범위 판정 아님.
- 기존 1,127개 후보는 검색 시드만 사용하며 최종 독성 출처는 ATSDR/PubMed 원 연구 두 곳 유지. Xu Table S4는 구조 식별 보조만 사용. 키워드 또는 색인 연결은 양성 라벨 아님.
- PubChem API 접속 실패로 대량 구조 확보 미완료. EPA CompTox Batch Search에서 로컬 epa_batch_priority_CAS.txt 2,020종 또는 epa_batch_all_8110_CAS.txt 8,110종을 입력하고 원본 CASRN/SMILES/InChIKey/DTXSID를 CSV로 내려받아 병합한다. 로컬 merge_epa_registry.py는 합성 입력으로 테스트했고 실제 EPA export는 아직 미확보. CAS-이름/구조 충돌, 다중 구조, 혼합물은 보류.
- 실험 구조 A/B 두 개와 한 가지 구조 기반 우선평가 방향 유지. 249종 반도체는 핵심 사례 분석군으로 유지. 실제 노출, 독성 미평가 여부, 독립 검증 및 최종 점수 미확정.

[결과 manifest](summary.json) · [EPA Batch Search](https://comptox.epa.gov/dashboard/batch-search) · [공개 v0.18](../hematotoxicity_v18/)
