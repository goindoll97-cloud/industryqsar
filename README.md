# IndustryQSAR: 인체급성유해성물질 규제 스크리닝 파일럿

기존 MSDS **설치류 급성경구 LD50** 및 외부 QSAR 예측을 이용해 **추가 검토 우선순위**를 산출하는 연구용 프로토타입입니다. **규제 지정 판정 도구가 아닙니다.** 신규 독성시험 자료 수집이나 QSAR 재학습은 수행하지 않습니다.

## 빠른 실행

Python 3.11 이상:

```bash
python -m pip install -r requirements.txt
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
python pilot.py --input data/sample_synthetic.csv --out outputs/demo --demo
python -m pytest -q
```

데모 데이터는 전부 합성값입니다. 논문 결과로 사용하지 마세요.

### 법령 API 연결

1. **본인의 컴퓨터**에서 `.env`에 승인받은 `LAW_API_OC`를 입력합니다. 키를 GitHub, Issues, PR, 채팅, 로그에 게시하지 마세요.
2. API 확인 및 법령 원문 보관:

```bash
python pilot.py --input data/sample_synthetic.csv --out outputs/demo_law --demo --live-law
```

법제처 `lawSearch.do` (법령명 검색)와 `lawService.do` (본문 조회)를 호출합니다. 원본을 `law_search.xml`, `law_detail.xml`, 메타데이터를 `law_audit.json`에 저장합니다. **법령 API로 화학물질 지정목록이나 MSDS를 가져오는 기능은 없습니다.** 조회에 성공해도 별표 기준과 적용일은 연구자가 확인해야 합니다. 인증 상태, API 응답 구조에 따라 호출이 실패할 수 있습니다.

### 본인 데이터로 실행

```bash
python pilot.py --input data/private/compounds.csv --out outputs/real_pilot --live-law
```

API 인증 전, 로컬 분석만 점검하려면 `--live-law`를 생략할 수 있습니다. 그러나 법령의 최신 별표 기준이 기계적으로 검증되었다고 주장해서는 안 됩니다.

입력 CSV 열 이름은 `data/sample_synthetic.csv` 참고. 중요한 열:

| 열 | 의미 |
|---|---|
| `compound_id, name, cas` | 물질 식별자(실험대상은 단일물질) |
| `substance_type` | `single`만 본 분석에 포함, `mixture`는 제외 |
| `designation_status` | `designated`, `not_designated`, `unknown` (이미 검증한 외부 고시 정보) |
| `designation_status_source` | **규제 지정 여부를 확인한 출처/확인일** (빈칸이면 미지정으로 취급하지 않음) |
| `msds_oral_ld50_raw` | 예: `150`, `<300`, `>2000`, `100-200`, 단위 mg/kg |
| `msds_basis, msds_species, msds_route, msds_unit, msds_source` | 자료 종류·동물종·노출경로·단위·출처; 실험값과 해당 메타데이터가 확인되어야 확정 신호로 사용 |
| `qsar_oral_ld50_raw, qsar_ad, qsar_source` | 기존 QSAR 예측 LD50, `inside/outside/unknown`, 예측 출처. AD는 사용자 입력이며 소프트웨어가 재계산하지 않음 |

`msds_basis=experimental`, `msds_species=rat/mouse/rodent`, `msds_route=oral`, `msds_unit=mg/kg` 및 `msds_source`가 모두 있어야 실험자료를 기준 비교에 사용합니다. **MSDS 표기만으로 실험의 질이나 독립성이 입증되는 것은 아니며**, 출처 확인이 필요합니다. `qsar_ad=inside`도 외부 모델의 AD 판단이 이미 이루어졌다는 사용자 제공값입니다.

### 연구 범위와 법적 기준

2025-08-05 개정 「화학물질의 등록 및 평가 등에 관한 법률 시행령」 별표 1의 설치류 급성경구 LD50 기준인 **300 mg/kg 이하**만 계산합니다(50 mg/kg 이하, 50 초과~300 이하 구간을 합산). **경피·흡입·피부부식·표적장기독성·혼합물** 기준을 평가하지 않습니다. 2026년 현재 적용법령/신규 개정 여부는 별도로 확인해야 합니다.

- 법령 기준: https://www.law.go.kr/법령별표서식/(화학물질의 등록 및 평가 등에 관한 법률 시행령,20260512,별표1)
- Open API 가이드: https://open.law.go.kr/LSO/openApi/guideResult.do
- 지정 고시: https://www.law.go.kr/행정규칙/인체급성유해성물질,인체만성유해성물질및생태유해성물질의지정고시

**법령 API는 최신 규제물질 CAS 지정여부를 판정하지 않습니다.** 이 파일럿은 `designation_status`를 사용자 확인 정보로 받으며, 이를 검증 없이 자동 생성하지 않습니다. 미지정 상태를 음성 독성 정답으로 간주하지 않습니다.

### 출력

`screening_results.csv`: 전체 물질 + 규제기준 비교, AD, 신뢰성 경고, 후보 등급

`manual_review.csv`: 기존 지정 물질·경구 후순위를 제외하고 검토할 대상

`summary.json`: 범위, 기준, 등급별 수, 모드 및 법령 확인 상태

**등급은 법적 지정 결과나 산업현장 위험도(노출량 포함)를 의미하지 않습니다.** 기준 300 mg/kg을 넘는 독성 수치가 있어도 다른 유해성 항목에 따른 규제 가능성이 존재합니다. 예측이 AD 밖인 경우 안전물질로 취급하지 않습니다. MSDS의 실험 자료와 동일 원천의 QSAR를 독립된 두 증거로 중복 계산하지 마세요.

### 연구 단계별 확장 제안

1. 공개된 고시 목록의 지정 여부 및 CAS 정합성 검증(고시 자동 수집은 아직 미구현)
2. 실제 MSDS 문서에서 추출한 값의 출처 추적 및 표본 수기 검증(자동 추출은 아직 미구현)
3. CATMoS 등 외부 QSAR CSV와 AD 연동, 예측의 독립성 확인
4. 과거 시점 기준 목록으로 시간적 외부검증 및 우선순위 발견율 평가

> **제한:** `.env`에 키를 추가해야 실제 법령 API 호출이 가능합니다. 합성 데모 성공은 실물질 데이터 통합이나 API 호출 성공을 의미하지 않습니다.


## KOSHA MSDS OpenAPI: CAS 기반 조회 및 독성 근거 확보 (추가 기능)

공공데이터포털 **한국산업안전보건공단_물질안전보건자료 조회 서비스** (데이터 ID **15157612**)의 2026년 신규 `msdschem1` 경로를 이용합니다.

- 공식 소개: https://www.data.go.kr/data/15157612/openapi.do
- 기본 주소: `https://apis.data.go.kr/B552468/msdschem1`
- CAS 목록 조회: `getChemList001` (`searchWrd=CAS`, `searchCnd=1`, `numOfRows`, `pageNo`)
- 상세 MSDS: `getChemDetail111`(11. 독성), `getChemDetail121`(12. 환경영향)`
- **중요:** 상세조회 `chemId` 파라미터는 파일럿의 기본 가정입니다. 실제 계정에 제공되는 **최신 OpenAPI 활용가이드/Swagger에서 상세 요청변수명과 응답 필드를 확인**해야 합니다. 호출이 실패하면 `KOSHA_MSDS_DETAIL_ID_PARAM` 또는 `--detail-id-param`을 실제 요청변수명으로 수정하세요.

**로컬 환경변수 설정** (인증값을 채팅이나 GitHub에 게시하지 마세요):

```dotenv
LAW_API_OC=본인_법령_API_인증값
KOSHA_MSDS_SERVICE_KEY=본인_KOSHA_서비스키
KOSHA_MSDS_DETAIL_ID_PARAM=chemId
```

**예시: CAS 목록 먼저 2건 조회** (실제 API 요청, 키·서비스 승인 필요):

```bash
python kosha_msds.py --cas 71-43-2 --cas 108-88-3 --out outputs/kosha_search
```

**실제 11·12번 섹션도 조회** (기본 파라미터 명세 확인 후 실행):

```bash
python kosha_msds.py --cas 71-43-2 --fetch-details --out outputs/kosha_details
```

**CAS 목록 CSV 사용:** 입력 `data/private/cas_list.csv`에 `cas` 열을 준비합니다.

```bash
python kosha_msds.py --cas-csv data/private/cas_list.csv --max-cas 20 --fetch-details --sleep 1.0 --out outputs/kosha_batch
```

수집 결과는 `outputs/` 아래에 저장되며 Git에 커밋되지 않습니다.

| 출력 | 내용 |
|---|---|
| `kosha_search_results.csv` | CAS 조회 상태 및 원본 목록 필드, 다중/불확실 매칭 경고 |
| `kosha_sections.csv` | MSDS 11·12번 원문 텍스트 (검증 전) |
| `kosha_endpoint_mentions.csv` | LD50·LC50·EC50 언급 부분 (후보 텍스트만) |
| `raw_xml/*.xml` | 원문 XML 증거 보존 |
| `screening_input_template.csv` | 기존 `pilot.py` 입력 규격의 빈 양식 |
| `kosha_audit.json` | 조회시점, 정확한 CAS 매칭 건수 및 검증상태 기록 |

**자료 해석 유의사항:** 수집된 LD50·EC50 텍스트는 *아직 시험종·노출경로·시험시간·단위·원출처가 검증되지 않은 자료*입니다. 공단 MSDS는 참고용이므로 조회 결과를 자동으로 `msds_basis=experimental`로 채우지 않습니다. 자동 추출 후보를 곧바로 법정 지정 근거로 사용하지 마세요. `designation_status`도 `unknown`으로 두며 공식 지정고시와 별도 대조 후에만 변경하세요. 특히 12번 물벼룩 자료와 11번 설치류 자료는 서로 다른 종말점입니다. 현재 `pilot.py`는 설치류 경구 LD50 스크리닝이므로, 물벼룩 EC50은 별도 생태유해성 모델 확장 전까지 해당 법적 기준에 자동 대입하지 않습니다.

**테스트:** `python -m pytest -q` (가짜 XML을 이용한 계약 테스트; 실제 API 인증·상세조회 성공은 보장하지 않음).
