# 연구방향: EPA 단일 해외자료원, QSAR 중심의 국내 인체급성 지정 검토 스크리닝

## 권장 논문 제목

국문: QSAR 기반 화학구조 유사성과 급성독성 정보의 통합을 통한 국내 인체급성유해성물질 규제 후보 스크리닝

영문: QSAR-Based Screening of Chemicals for Prioritizing Acute Human Health Hazard Regulatory Review in South Korea

### 핵심 연구 질문

한국 인체급성 지정목록의 구조 유사성, **미리 학습된 EPA TEST의 흰쥐 급성경구 LD50 QSAR 예측**, KOSHA MSDS 참고 독성값을 사용하여 규제 검토가 필요한 화학물질의 우선순위를 근거와 함께 제시할 수 있는가?

**국외 자료원은 미국 EPA 한 곳만** 사용합니다. ECHA/일본의 제도 비교를 본 분석에서 제외합니다. EPA CompTox는 미국의 법적 규제물질 지정 목록이 아닙니다.

## 단계와 역할

1. **국내 참조집단:** 기존에 정리한 인체급성 지정목록(CAS 1,711개, 업로드한 사용자의 임시 스냅샷)을 유해성 검토의 양성 참조로 사용합니다. 법률적 적용범위/시행일은 별도 검증이 필요합니다. 지정사유가 경구 LD50인 것으로 단정하지 않습니다.
2. **후보집단:** 가능하면 국내 산업용 화학물질 취급·등록의 CAS 목록을 별도로 정합니다. 지정목록에서 CAS가 검색되지 않더라도 '규제 비대상' 또는 '무독성'이라고 가정하지 않습니다. 해외 EPA 전체 목록만 넣으면 국내 물질을 대표한다고 주장할 수 없습니다.
3. **EPA CompTox:** 후보와 참조 CAS의 구조/SMILES 및 DTXSID를 일괄 다운로드합니다. CAS와 원구조·QSAR-ready 구조의 차이를 검토합니다.
4. **RDKit:** 중성 단일성분 유기화합물에 한해서 Morgan fingerprint, Tanimoto nearest-analogue 및 분자기술자를 계산합니다. **유사도는 LD50 예측값도 EPA TEST 모델의 적용영역도 아닙니다.**
5. **EPA TEST:** 기존 TEST 모델의 흰쥐 경구 LD50 예측값, 원단위, 모델명/버전 및 사용자가 확인한 AD 결과를 가져옵니다. TEST 결과의 -log10(mol/kg) 출력은 해당 분자량을 확인한 후 mg/kg로 변환합니다.
6. **KOSHA MSDS:** 우선검토 후보의 경구 LD50과 출처/시험종/범위 정보를 별도 대조합니다. 여러 데이터에 같은 원실험이 재인용되었는지 주의합니다.
7. **후속 검증:** QSAR 단독과 QSAR+구조 유사도 및 QSAR+구조+MSDS의 후보 순위를 비교합니다. 구조적 cluster / scaffold holdout 과 독립 확인된 급성경구 LD50 참조값을 사용해 후보 재현율, 검토 업무량, 누락 우려를 정량 평가합니다. 국내 미지정은 독성 '음성' 레이블이 아닙니다.

현재 GitHub 코드는 3~5단계 중 **EPA CompTox 파일과 기존 TEST 예측의 통합·RDKit 구조 기술자 계산·후보 분류**를 지원합니다. 모델 신규학습, EPA 자동 다운로드, 공식 법적 지정 판단, 독립 검증을 구현했다고 주장하지 않습니다.

### 기존 코드와 새 코드의 구분

| 프로그램 | 역할 |
|---|---|
| kosha_msds.py | 기존 KOSHA 원문 수집 |
| human_acute_extract.py | MSDS 11번 경구/경피/흡입 항목 추출 |
| regulatory_screen.py | 국내 인체급성 지정목록 CAS 및 MSDS의 예비 대조 |
| prepare_epa_batch.py | 국내 참조·후보 CAS를 EPA 일괄검색용 txt로 생성 |
| qsar_candidate_screen.py | EPA 구조 + EPA TEST QSAR를 통합한 후보의 RDKit 분석 |

## 지금 사용자가 수행할 순서

### 1. GitHub 최신 버전 받기

PowerShell:

~~~powershell
git pull origin main
python -m pip install -r requirements-qsar.txt
~~~

### 2. EPA 일괄조회 CAS 목록 생성

사용자님이 이미 로컬에 갖고 있는 인체급성 준비 CSV로 첫 단계 확인:

~~~powershell
python prepare_epa_batch.py --registry data/private/acute_registry_for_screening.csv --candidates data/private/cas_list_pilot20.csv --out data/private/epa_batch_cas.txt
~~~

이 명령은 기존 20종 시험용 CAS를 국내 급성지정 참조 CAS와 합쳐 data/private/epa_batch_cas.txt 및 data/private/epa_batch_cas_roles.csv를 만듭니다. 그중 **16종은 이미 지정목록 참조집단**, 나머지 **4종은 미지정 여부가 검증되지 않은 비교대상**입니다. 두 파일을 구분해 보관하십시오.

국내 후보집단 CAS를 확보했을 때에는 다음과 같이 결합할 수 있습니다.

~~~powershell
python prepare_epa_batch.py --registry data/private/acute_registry_for_screening.csv --candidates data/private/domestic_candidates.csv --out data/private/epa_batch_cas.txt
~~~

후보집단 입력 CSV에는 cas 열이 필요합니다. 입력 리스트에서 CAS 체크섬이 검증된 값만 포함됩니다. 국내 목록이 없다면 임의의 국내 취급 여부를 추정하지 마세요.

### 3. 미국 EPA CompTox에서 SMILES 받기 (사용자가 수행)

- 공식 페이지: https://comptox.epa.gov/dashboard/batch-search
- Batch Search -> Substance Identifiers -> CASRN
- data/private/epa_batch_cas.txt 파일의 CAS 목록을 붙여넣기
- 검색결과에서 가능하면 **CASRN, DTXSID, QSAR_READY_SMILES 또는 SMILES** 열을 포함하여 CSV로 내보내기
- 원본 파일을 data/private/epa_structures.csv 에 보관

참고: EPA CompTox에서 QSAR-ready 구조는 원래 물질의 탈염·중성화 등 표준화된 표현일 수 있습니다. 염류, 금속 및 다성분은 일반 유기화합물 QSAR와 구분해야 합니다. 이 코드의 파일럿은 중성 단일성분 유기물만 대상으로 하며 그 밖의 물질을 수동 검토 대상으로 보냅니다.

### 4. EPA 구조만으로 먼저 적용 가능성 파악하기

~~~powershell
python qsar_candidate_screen.py --structures data/private/epa_structures.csv --registry data/private/acute_registry_for_screening.csv --candidates data/private/cas_list_pilot20.csv --out outputs/epa_qsar_structure_pilot
~~~

생성 파일:

- registry_structure_coverage.csv : 한국 지정 CAS 중 구조를 확보하고 RDKit에 사용할 수 있는 규모
- qsar_candidates.csv : 제공 목록에 없는 후보 CAS, 가장 가까운 지정 참조구조, Tanimoto, 기술자 등
- structure_manual_review.csv : 이 단계에서 제외된 염류·무기물·복합물·구조오류
- qsar_screen_summary.json : 전체 범위·해석 제약
- candidate_structure_missing.csv : 국내 후보목록에 있으나 EPA 구조파일에 없는 CAS (후보목록 지정 시)
- evidence_manual_review.csv : 식별자/AD/불일치 등 재검토 대상

**중요한 화학적 안전장치:** EPA의 원래 SMILES와 QSAR-ready SMILES가 모두 있고 표준화된 구조가 원래 구조와 다르면, 염류·다성분/구조 정합성 문제를 피하기 위해 자동 구조 유사성 산정에서 제외합니다.

**중요:** 참조집단 CAS만 EPA에서 검색하면 후보행 수는 0이 될 수 있습니다. 이는 정상입니다. 후보 스크리닝에는 별도의 국내 후보 CAS 목록이 필요합니다. 또한 이 단계는 구조 유사성 파일럿이지 독성 QSAR 모델 성능 검증이 아닙니다.

### 5. EPA TEST 예측 결과가 확보되었을 때 QSAR 연결

기존 EPA TEST 5.1.2가 제공하는 흰쥐 경구 LD50 예측을 이용합니다.

공식 다운로드: https://www.epa.gov/comptox-tools/toxicity-estimation-software-tool-test

원본 TEST 결과 파일은 별도 보존하고, 다음 필수 열 이름으로 결과 CSV를 정리합니다.

~~~csv
cas,ld50_value,ld50_unit,ad_status,model_name
~~~

- ld50_unit: mg/kg 또는 -log10(mol/kg). TEST 결과가 어떤 단위인지는 원본 출력에서 확인해야 합니다.
- ad_status: inside / outside / unknown. TEST 출력의 실제 적용영역 판단이 없다면 **unknown**으로 기록하고 inside를 추정하지 마세요.
- model_name: TEST 모델/버전/합의(consensus) 여부를 기록합니다.
- qsar 후보를 이미 학습자료에 포함한 모델일 수 있으므로 독립 예측으로서의 유효성은 반드시 별도 검토해야 합니다.

~~~powershell
python qsar_candidate_screen.py --structures data/private/epa_structures.csv --registry data/private/acute_registry_for_screening.csv --candidates data/private/cas_list_pilot20.csv --predictions data/private/epa_test_predictions.csv --kosha-endpoints outputs/kosha_pilot20/human_acute_endpoints.csv --out outputs/epa_qsar_with_predictions

python qsar_ablation.py --screen outputs/epa_qsar_with_predictions/qsar_candidates.csv --out outputs/epa_qsar_ablation
~~~

QSAR 결과를 확보하기 전에는 'QSAR 예측이 유해성을 예측했다'고 보고하지 마세요.

**세 가지 방법 비교:** ablation 분석은 (A) EPA TEST QSAR만, (B) QSAR + RDKit 유사성, (C) QSAR + RDKit + KOSHA MSDS의 **검토 후보 목록이 어떻게 달라지는지** 비교합니다. 독립 실험 정답이 없으므로 정확도·민감도·false-safe를 산출하지 않습니다. 이를 논문 성능 지표로 쓰려면 별도 외부 검증자료가 필요합니다.

기존 KOSHA CSV 경로가 없다면 --kosha-endpoints 옵션을 생략하세요. 이 옵션은 보조 근거이며 독성시험 원자료가 아닙니다. 특히 QSAR와 MSDS가 동일한 기존 실험값을 공유할 수 있으므로 두 독립 증거로 해석하지 않습니다.

### 6. ChatGPT에 보낼 파일

첫 번째 확인 단계에서는 **outputs/epa_qsar_structure_pilot 전체를 ZIP으로 압축한 파일**과 **EPA CompTox 원본 다운로드 CSV**를 업로드해 주세요. PowerShell에서 `Compress-Archive -Path outputs\epa_qsar_structure_pilot\* -DestinationPath epa_qsar_structure_pilot.zip -Force`를 실행할 수 있습니다. EPA TEST 결과가 준비되었다면 원본 TEST 출력 및 정규화한 CSV도 추가하면 됩니다. .env 파일/인증키는 절대 업로드하지 마세요.

## 평가 설계에서 주의할 점

- 한국 인체급성 지정 전체가 경구 LD50 300 mg/kg 조건으로 선정되었다고 가정하면 안 됩니다. 법적 지정 원인 분류가 불분명한 물질은 QSAR 경구독성 시험의 정답으로 사용할 수 없습니다.
- **구조 유사성 점수**와 **TEST QSAR LD50 예측**은 독립된 변수로 분석합니다. 유사도가 높다고 독성이 높다고 결론 내리지 않습니다.
- 현재 코드의 0.75 Tanimoto '높은 유사성' 기준은 잠정적인 업무용 선별 임계치로, 논문에 사용하려면 민감도 분석과 근거가 필요합니다.
- 실제 논문에서 QSAR 예측값의 정확도/유효성을 논하려면 **측정된 시험값을 기반으로 한 외부 검증집단**과 모델 학습자료 중복 검사가 필요합니다.
- 실험자료 부재와 국내 지정목록 부재를 무독성으로 치환하지 않습니다.
- EPA 데이터 하나로 국외 규제의 범위를 비교했다는 주장을 하지 않습니다. EPA는 **예측·구조·독성의 외부 근거 자료원**으로 사용합니다.
