# 인체급성 지정목록의 CAS 대조: 3단계 실행 가이드

## 적용 범위와 주의

기존 KOSHA MSDS 11번의 인체급성독성 자료와, 사용자 제공 **인체급성 지정목록 스냅샷**의 CAS를 교차 대조합니다. 엑셀 파일의 제목만으로 공식 출처와 법적 시행일을 검증할 수 없으므로, 사용자 제공 목록은 별도의 출처 확인 전까지 잠정 자료입니다.

- 인체급성으로 표시된 행만 인체급성 CAS 지정목록에 포함합니다.
- 인체만성·생태만 표시된 행을 인체급성 항목으로 잘못 분류하지 않습니다.
- CAS 미기재 그룹물질, 복수 CAS, 체크섬 오류는 수기 검토 대상으로 남깁니다.
- 목록에 CAS가 없다고 해서 비규제 또는 안전물질이라고 판단하지 않습니다.
- 현재 경구 LD50 300 mg/kg 이하만 수치적으로 기준 비교합니다. 경피와 흡입은 정보 확보 현황을 점검하는 단계입니다.

## 1. 제공된 ZIP의 구성과 준비

사용자가 받은 '인체급성_규제목록_분석입력_20261120.zip'에는 다음 파일이 들어 있습니다.

| 파일 | 용도 |
|---|---|
| acute_registry_for_screening.csv | 인체급성으로 표기된 행을 정리한 CAS 등록목록 |
| registry_metadata.json | 제공 파일명, 작성일의 근거, 출처 확인 상태 |
| registry_manual_review.csv | CAS가 없거나 검증되지 않은 행 |
| cas_list_pilot20.csv | 검증용 20종 CAS 조회목록 |
| cas_pilot20_selection_manifest.csv | 20종 표본 구분과 원본 행 추적정보 |
| four_existing_kosha_registry_context.csv | 기존 벤젠·톨루엔·아세톤·디클로로메탄의 원본 목록상 급성·만성 기재 여부 |

파일을 저장소 루트에 다운로드한 다음 PowerShell에서 실행하세요.

~~~powershell
git pull origin main
New-Item -ItemType Directory -Path data/private -Force
Expand-Archive -Path "인체급성_규제목록_분석입력_20261120.zip" -DestinationPath data/private -Force
~~~

metadata의 source_url이 비어 있고 provenance_status가 unverified_user_upload인 것은 **공식 다운로드 주소를 아직 검증하지 않았기 때문**입니다. 원본 확보처와 고시 적용일을 별도 확인하기 전까지 이 상태를 유지하세요.

## 2. 이미 수집한 KOSHA 4종과 대조

기존 KOSHA 폴더가 있을 때:

~~~powershell
python regulatory_screen.py --batch outputs/kosha_batch --registry data/private/acute_registry_for_screening.csv --registry-meta data/private/registry_metadata.json --out outputs/regulatory_with_registry
~~~

기존 KOSHA ZIP만 있을 때:

~~~powershell
python regulatory_screen.py --batch-zip kosha_batch.zip --registry data/private/acute_registry_for_screening.csv --registry-meta data/private/registry_metadata.json --out outputs/regulatory_with_registry
~~~

생성 파일:

1. screening_priorities.csv: 물질별 CAS 매칭 상태와 검토 순위
2. review_queue.csv: 추가 검토할 후보
3. endpoint_quality_review.csv: MSDS 독성 항목 품질
4. registry_cas_audit.csv: 등록목록의 원본 행/CAS/물질명/함량기준 기록과 대조 상태
5. screening_summary.json: 범위, 검증 보류 상태, 매칭 통계

outputs/regulatory_with_registry 폴더 전체를 ZIP으로 압축하여 채팅에 올려 주세요.

## 3. 선택: 20종으로 파서와 분류의 동작 검증

현재까지 조회한 4종에 사용자가 제공한 표의 인체급성 행에서 CAS가 검증된 16종을 더한, **기술 검증용 선택 표본**입니다. 일반 화학물질 모집단을 대표하는 표본도 아니고, 규제 지정 양성이 반드시 경구 LD50 기준에서 비롯되었다는 뜻도 아닙니다.

~~~powershell
python kosha_msds.py --cas-csv data/private/cas_list_pilot20.csv --max-cas 20 --fetch-details --out outputs/kosha_pilot20
python regulatory_screen.py --batch outputs/kosha_pilot20 --registry data/private/acute_registry_for_screening.csv --registry-meta data/private/registry_metadata.json --out outputs/regulatory_pilot20
~~~

필요하다면 outputs/kosha_pilot20 폴더와 outputs/regulatory_pilot20 폴더를 각각 ZIP으로 압축하여 보내 주세요. API 키와 인증 URL, .env는 절대 업로드하지 마세요.

## 연구해석

- listed_in_supplied_acute_registry는 제공된 인체급성 스냅샷에 동일 CAS가 있다는 뜻입니다. 법적 지정의 확정 판정은 아닙니다.
- not_found_in_partial_snapshot_unknown는 부분목록에서 찾지 못했다는 뜻입니다. 미지정·무독성 판정이 아닙니다.
- 그룹·염류·수화물·함량기준은 자동 CAS 매칭으로 확인하지 못하므로 원본고시 수기 확인이 필요합니다.
- 지정 상태를 독성 레이블의 음성 정답으로 사용하지 않습니다.

데이터 재현성 확인을 위해 registry_metadata.json에 원본 XLSX와 변환 CSV의 SHA-256 해시, 추출 규칙 및 표본 선정 규칙을 기록했습니다. 따라서 법정 효력·출처 검증과는 별개로 파일 변환 내용을 추적할 수 있습니다.
