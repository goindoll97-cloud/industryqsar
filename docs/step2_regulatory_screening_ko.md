# 2단계 실행 가이드: 인체급성유해성물질 스크리닝

## 연구 범위

새 독성시험이나 QSAR 모델 재학습 없이 기존 KOSHA MSDS 11번 자료를 이용하여 추가 심사가 필요한 물질을 우선순위로 분류합니다.

정량적 규제 기준 비교는 **설치류 급성경구 LD50 300 mg/kg 이하**에 한정됩니다. 경피 LD50 및 흡입 LC50은 자료의 확보와 시험조건을 검토하지만 법적 기준과 자동 비교하지 않습니다. 물벼룩 및 생태독성 정보는 제외합니다.

이 결과는 법적 지정 확정 또는 산업현장 노출위험 평가가 아닙니다.

## 1. 지금 바로 실행하기

이미 가지고 계신 KOSHA 배치 폴더를 사용합니다. PowerShell 터미널:

~~~powershell
git pull origin main
python -m pip install -r requirements.txt
python regulatory_screen.py --batch outputs/kosha_batch --out outputs/regulatory_step2
~~~

기존에 만든 ZIP 파일을 그대로 사용할 수도 있습니다. ZIP 파일을 프로젝트 폴더에 놓은 경우:

~~~powershell
python regulatory_screen.py --batch-zip kosha_batch.zip --out outputs/regulatory_step2
~~~

ZIP의 경로가 다른 곳에 있다면 절대 경로를 지정하세요.

~~~powershell
python regulatory_screen.py --batch-zip "C:\Users\사용자\Downloads\kosha_batch.zip" --out outputs/regulatory_step2
~~~

**이 작업은 API 키가 필요하지 않습니다.** 이미 내려받은 기존 MSDS 결과를 분석합니다.

## 2. 생성되는 네 가지 결과물

| 파일 | 용도 |
|---|---|
| screening_priorities.csv | 물질별 CAS, 규제목록 대조상태, 경구독성 기준 부합 신호, 품질 경고 및 우선순위 |
| review_queue.csv | 근거를 우선 점검할 후보 목록 |
| endpoint_quality_review.csv | 경구·경피·흡입 독성값의 추출 정확성·단위·시험종·출처 검토 |
| screening_summary.json | 분석 규모, 신뢰성 및 규제목록 제공 여부에 대한 요약 |

위 파일이 들어 있는 **outputs/regulatory_step2 폴더 전체를 ZIP으로 압축하여 채팅에 업로드**해 주시면 됩니다.

규제목록이 아직 없다면 registry_not_provided로 나오는 것이 정상입니다. 이를 '현재 미지정'이라고 단정해서는 안 됩니다.

## 3. 공식 규제 지정목록 추가하기

공식 자료를 다운로드할 수 있는 곳:

- 화학물질정보처리시스템: https://kreach.me.go.kr/repwrt/mttr/kr/mttrList.do
- 기존화학물질 및 유해성 정보: https://kreach.me.go.kr/repwrt/mttrInfoOpen/existedMttrHzrdsList.do
- 인체급성·인체만성·생태유해성물질 지정고시: https://www.law.go.kr/admRulLsInfoP.do?admRulSeq=2100000285142&chrClsCd=010202

**먼저 원본 공식 목록 파일을 그대로 저장하세요.** Excel일 경우 처리용으로 CSV UTF-8을 별도 저장하시면 됩니다.

추천 CSV 헤더:

~~~csv
cas,유해성물질,고유번호
~~~

원본 목록에 'CAS No', '유해성물질', '고유번호' 등의 열이 있으면 코드에서 일부 자동 인식합니다. 인체만성 또는 생태유해성으로만 지정된 행은 인체급성 매칭에서 제외합니다.

주의: 단일 CAS에 포함되지 않는 그룹물질, 염류·수화물, 혼합물, 함량기준, 개별 시행일은 CAS 자동 매칭만으로 확인할 수 없습니다. 공식 고시 원문과 대조해야 합니다.

- 목록 저장 경로: data/private/acute_registry.csv
- 메타데이터 경로: data/private/registry_metadata.json

메타데이터는 data/registry_metadata_TEMPLATE.json을 복사해서 실제 출처 및 다운로드 일자로 수정합니다.

~~~json
{
  "source_url": "https://kreach.me.go.kr/repwrt/mttrInfoOpen/existedMttrHzrdsList.do",
  "snapshot_date": "2026-11-20",
  "coverage": "partial",
  "acute_only": false
}
~~~

날짜는 예시이므로 실제로 목록을 확보한 날짜로 수정해야 합니다. 전체 인체급성 지정목록의 완전성이 검증되지 않았다면 coverage는 반드시 partial을 사용하세요.

공식 목록까지 비교하려면:

~~~powershell
python regulatory_screen.py --batch outputs/kosha_batch --registry data/private/acute_registry.csv --registry-meta data/private/registry_metadata.json --out outputs/regulatory_with_registry
~~~

기존 ZIP을 사용하는 경우 --batch 대신 --batch-zip kosha_batch.zip을 사용합니다.

등록 여부 변수의 해석:

- listed_in_supplied_acute_registry: 제공한 목록에 동일 CAS가 존재한다는 의미. 실제 지정 범위 재확인 필요
- not_found_in_partial_snapshot_unknown: 부분목록에 없다는 뜻일 뿐, 비규제 확인이 아님
- not_found_in_claimed_complete_snapshot: 완전하다고 선언한 사용자 제공 목록에서 검색되지 않았다는 뜻일 뿐, 법적 비지정 판단이 아님
- registry_not_provided: 지정목록을 아직 받지 않은 상태

CAS 없는 공식 그룹물질 행을 발견하면 소프트웨어는 완전목록 선언을 자동으로 보수적으로 낮춥니다.

## 4. 기존 QSAR 예측자료는 선택 사항

인체급성 **설치류 경구 LD50** 예측자료가 이미 있다면 다음 헤더로 CSV UTF-8을 준비합니다.

~~~csv
cas,qsar_oral_ld50,qsar_ad,model_name
~~~

qsar_oral_ld50은 mg/kg 수치, qsar_ad는 inside/outside/unknown 중 하나입니다. 물벼룩 EC50 예측 결과를 이 파일에 입력하면 안 됩니다.

~~~powershell
python regulatory_screen.py --batch outputs/kosha_batch --registry data/private/acute_registry.csv --registry-meta data/private/registry_metadata.json --qsar data/private/qsar_oral.csv --out outputs/regulatory_with_qsar
~~~

QSAR 예측은 근거 보완 자료이지 공식 지정 또는 독립적인 실험적 정답이 아닙니다. MSDS와 QSAR가 동일한 학습/독성 원출처를 썼는지 별도 검증이 필요합니다.

## 5. 논문을 위한 다음 평가

- 물질별 정보 확보율, 자동 추출 성공률 및 검토대상 비율
- 공식 지정 양성물질에 대한 기준 부합 후보 선별률
- 품질이 낮은 독성자료를 어떻게 처리하는지에 따른 후보 순위 변화
- 선택적으로 QSAR 도입 전후의 불일치, 검토 업무량 및 누락 가능성 변화

아직 공식 지정목록이 없거나 4종의 데이터만 있다면 위 지표를 일반화할 수 없습니다. 인체급성 법정 기준에 해당할 수 있는 물질, 현재 지정된 참고물질, 정보 부족 물질을 함께 포함한 다수 물질로 검증해야 합니다.

**보안:** .env 파일, API 인증키, 서비스키가 포함된 URL은 GitHub와 결과 ZIP에 넣지 마세요.
