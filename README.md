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
