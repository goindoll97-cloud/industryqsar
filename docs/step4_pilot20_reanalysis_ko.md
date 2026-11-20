# 20종 파일럿: 기존 원본 XML을 재사용한 재분석 방법

2026년 11월 20일의 KOSHA 20종 기술 검증 파일럿을 재분석하는 절차입니다.
조회된 MSDS 11번은 독성시험 원자료가 아닌 참고정보이며, 공개된 인체급성
지정목록에 실린 물질을 '경구 LD50 양성 정답'으로 가정하지 않습니다.

## 무엇이 개선되었나?

1. 원문에 LD50이 같은 값으로 두 번 기재된 경우에는 한 후보값으로 추출하되 'repeated_identical_value_in_text' 기록을 남깁니다.
2. LD50 범위(예: 50~300 mg/kg)는 독성분류 구간인지 실측 범위인지 불명확하므로 단일 실험값으로 자동 해석하지 않습니다.
3. '구분3'과 같은 분류값만 있는 경우는 실제 LD50 수치를 추정하지 않습니다.
4. 예전에는 기존 급성목록과 CAS가 일치한 물질 16종이 모두 'reference_listed'로만 보였지만, 이제 별도의 reference_evidence_audit.csv에서 이들 물질의 급성경구 LD50 기준 부합/초과/파싱 실패/미조회 여부를 확인할 수 있습니다.
5. manual_endpoint_review.csv로 수동 검토 대상의 MSDS 원문과 오류 유형을 따로 내보냅니다.
6. registry_vs_oral_numeric_relation 교차표를 screening_summary.json에 추가합니다.

## PowerShell 실행 방법

GitHub 저장소 폴더로 이동해서 실행합니다.

~~~powershell
git pull origin main
~~~

기존 20종 KOSHA 압축파일을 프로젝트 폴더에 둔 다음, **추가 KOSHA API 호출 없이** 내부 원본 XML을 다시 파싱합니다.

~~~powershell
python reparse_kosha_zip.py --batch-zip kosha_pilot20_results.zip --out-zip outputs/kosha_pilot20_reparsed.zip
~~~

재분석된 KOSHA ZIP을 공식 지정목록 스냅샷과 대조합니다.

~~~powershell
python regulatory_screen.py --batch-zip outputs/kosha_pilot20_reparsed.zip --registry data/private/acute_registry_for_screening.csv --registry-meta data/private/registry_metadata.json --out outputs/regulatory_pilot20_v2
~~~

검증 결과를 전달할 때는 다음 폴더를 압축하여 업로드해 주세요.

~~~powershell
Compress-Archive -Path outputs\regulatory_pilot20_v2\* -DestinationPath regulatory_pilot20_v2_results.zip -Force
~~~

**필수:** regulatory_pilot20_v2_results.zip

**추가 검증이 필요할 때:** outputs/kosha_pilot20_reparsed.zip. 이 파일에는 원본 MSDS XML이 포함되므로 공개 GitHub에 게시하지 않고, 프로젝트 외부 공유 전에 필요 자료만 포함됐는지 확인합니다.

## 신뢰성 해석

- listed_in_supplied_acute_registry는 사용자 제공 목록과 CAS가 동일함을 의미할 뿐 공식 법률상 지정 범위를 확인했다는 뜻이 아닙니다.
- reference_evidence_audit.csv의 급성경구 기준 부합 신호는 법정 지정 전체의 적합성 판정 또는 지정 이유의 규명이 아닙니다.
- 경구 LD50을 찾을 수 없는 기존 인체급성 기재 물질은 다른 노출경로의 독성이 존재하거나, 자료가 없는 경우일 수 있습니다.
- 원문 구분 3을 특정한 LD50 값으로 치환하지 않습니다.
- 경피·흡입 값은 아직 별도의 법정 기준과 자동 대조하지 않으며, 흡입시험 시간/형태 차이를 확인해야 합니다.
- 고시 시행일/법적 원본 출처, 그룹물질·염·수화물·함량 조건은 수기 검증이 필요합니다.
- 이 20종은 의도적으로 지정목록 사례를 많이 포함하도록 선정한 **편의 표본**이므로 16/20 매칭율은 선별 민감도가 아닙니다.
- QSAR 예측 CSV는 이 단계에서는 입력하지 않았으며, 추가하려면 인간 급성 경구 LD50과 모델 AD를 검증한 자료가 필요합니다.

새 데이터 수집이나 QSAR 모델 학습 없이도 분석 프로그램의 추출 성능·검증 보류 비율을 비교할 수 있습니다.
