# ATSDR 전체 후보 재선별 v0.1 (2026-11-27)

## 범위 변경 안내 (v0.2)

아래는 이전 전 경로 탐색 단계의 역사적 감사 결과이다. 현행 연구의 학습 및 독립검증은 흡입 경로가 확인된 인체·동물 근거로 제한하며, 농도 및 기간은 일률적으로 제한하지 않는다. 전 경로 선별 코드는 원자료 감사용으로 보존한다. 비흡입 및 경로 불명 자료는 학습에서 제외하며, 아래 수치는 흡입 전용 확정 데이터 규모가 아니다. Long 원자료 역시 흡입 근거가 개별 확인되지 않으면 본 모델 학습 및 검증에 사용하지 않는다. 상세 기준은 [현행 연구 프로토콜](hematotoxicity_research_protocol_ko.md)을 따른다.

## 실제 실행 결과

이전 수집 CSV 11,724행(184개 보고서)의 SHA-256:
`170e849fface5973258561a5b0eaf9efc9b8296974667a892314dd7ebc05f5c9`.

- 고유 문맥 11,580행, 정확히 일치하는 중복 144행.
- 기존 인체 흡입 우선 검토 949행 전부 보존. 신규 검토 문맥 10,631행.
- 인체 표현 2,228, 동물 표현 4,785, 혼재 1,499, 미확인 3,068.
- 흡입 표현 1,249, 경구 2,852, 경피 722, 주사 495 (중복 가능).
- 노출기간 표현 4,926, 농도/용량 표현 3,401.
- 혈액암 관련 키워드 문맥 194행(68개 보고서), 135개 검토 블록.
- 전체 인접 문맥 검토 블록 5,187개. 독립 연구 수가 아님.
- 우선순위 1: 혈액암 키워드 194; 2: 특정 endpoint 및 변화/미변화 표현 6,078; 3: 특정 endpoint 3,750; 4: 일반 문맥 1,558.
- 7개 물질 16개 연구/조건별 예비 관찰 정리(8 adverse_observed, 4 change_observed, 3 no_effect_at_condition, 1 mixed_or_uncertain). 이 중 14개 관찰 행은 이전 우선 검토 대상에 포함되지 않았던 원본 행에 연결된다. 동일 연구의 여러 조건 및 복수 인용문헌 묶음 포함. 원 연구 전문 검증 및 최종 물질 학습 라벨 0건.

## 로컬 실행

원본 및 분석 산출물은 공개 저장소에 포함하지 않는다. 기존 수집본과 이전 priority_review.csv를 로컬에 복사한 다음 실행한다.

```powershell
git pull origin main
python hematotoxicity/screen_all_atsdr.py data/private/hematology_candidates.csv --prior data/private/priority_review.csv --out outputs/atsdr_broad_v01
```

원본 순서가 동일해야 이전 record_id 연결이 의미 있다. 원본 해시와 행 수를 반드시 확인한다. --prior는 선택이지만 생략하면 기존 949행 연결을 재현하지 못한다.

산출물: all_candidates.csv, unique_review_queue.csv, cancer_mentions_existing_context.csv, review_blocks.csv, profile_summary.csv, summary.json. 문맥 기반 키워드 플래그이며 실험종·노출경로·독성의 확정값이 아니다. 약어와 표/인용문맥 때문에 오탐 가능. 동일 문맥 제거 및 페이지 내 인접행 묶음은 검토 효율화일 뿐 연구 중복 제거가 아니다. 전체 및 고유 자료, 기존 ID, 블록 전체 ID 연결과 빈 training_label을 로컬에서 검사했다.

## 전체 PDF 발암성 검색

```powershell
python -m pip install pymupdf
python hematotoxicity/scan_full_pdf_cancer.py data/private/hematology_candidates.csv --collection-root data/private/atsdr_profile_collection --out outputs/atsdr_full_pdf_cancer
```

--collection-root 아래 CSV의 file 컬럼에 해당하는 원본 raw/ PDF가 있어야 한다. 현재 작업 환경에는 PDF 184개가 없어서 실제 전체 검색은 0/184 완료, 184개 파일 부재로 실패했다. 이 경우 혈액암 근거가 없다는 뜻이 아니다. 합성 PDF 1개에서 검출 및 감사 기능만 시험했다. 검색 범위는 확보한 PDF 전체 페이지이며 PDF에 포함되지 않은 다른 보고서 장은 별도 수집해야 한다. 텍스트 추출 불가 페이지 및 실패 문서는 감사 파일에서 확인한다.

## Long 데이터 입력 준비

출처: Long et al., DOI 10.1021/acs.jcim.2c01088; 공개 데이터 카드 https://huggingface.co/datasets/maomlab/HematoxLong2023. 원자료 2,382행(논문: 759/1,623), 데이터 카드의 표시/설명에 서로 다른 정제 단계 수치가 있으므로 실제 CSV를 확인하여 집계한다. 다운로드 파일의 이용조건도 확인한다. 현재 원본 CSV는 확보되지 않았으며 원본 대상 감사/학습은 미실행이다.

```powershell
python -m pip install rdkit
python hematotoxicity/audit_long_dataset.py --train data/private/long_train.csv --test data/private/long_test.csv --out outputs/long_audit
```

SMILES,Y 컬럼을 입력으로 받는다. 동일 비입체 canonical 그룹의 교차 split 중복 및 라벨 충돌을 제외 후보로 표시하며 원본 라벨을 유지한다. 염/tautomer/대사산물 등 추가 정합성 검토 필요. Long의 0은 인체 직업성 흡입 무독성 확정값이 아니다. 노출 메타데이터를 추정하지 않는다. ToxRefDB v3는 https://github.com/USEPA/CompTox-ToxRefDB/releases 에서 실제 시험·effect·dose 및 assessed/critical 정보를 확보한 뒤 별도 추출한다.

## 연구 해석

2-부톡시에탄올의 반복 경구 노출 중 빈혈 완화, 1,3-부타디엔의 같은 농도에서 기간에 따라 다른 빈혈 관찰은 단기와 장기의 독성 연결이 보편 법칙이 아님을 보여주는 예비 근거다. 따라서 다양한 노출조건을 포함하되 기간별 독립검증이 필요하다. 혈액암 언급은 실제 암종별 양성 라벨이 아니다. 최종 라벨링 및 모델 학습·성능 검증은 미완료다.
