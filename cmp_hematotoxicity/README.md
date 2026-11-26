# CMP human hematotoxicity pilot

현재 단계는 SIDER 인체 이상반응 후보 및 IRIS 산업물질 검증 후보의 재현 가능한 인벤토리 구축, CMP 유기물질의 식별자 확인이다.

## 실행 (저장소 루트)
```powershell
python -m pip install -r cmp_hematotoxicity/requirements.txt
python cmp_hematotoxicity/build_human_base.py --raw data/private/cmp_hematotoxicity/raw
python cmp_hematotoxicity/build_dataset.py
```

[HUMAN_BASE_V1.md](HUMAN_BASE_V1.md): 원자료 4개, SHA-256, 출처, 데이터 사전, 라벨 한계. `data/cmp_organic_evidence.csv`: 69개 출처 기록, 56개 물질 명칭, 특허 및 논문 근거. 실제 사용 확인이나 독성 정답이 아님.

`build_dataset.py`는 PubChem 이름 기반 잠정 구조 매칭을 실행한다. CAS, 입체화학, 염 형태 수기 확인이 필요하다. 일반 혈액독성 벤치마크 수집 기능은 현재 연구 범위에서 제외했다. 원본과 출력은 기본적으로 data/private/ 아래에 저장.

## 다음 단계
인체 근거 판정, STITCH/CAS/SMILES 확인, 구조 표준화 및 중복 제거, 화학적 공간/AD 분석, 충분한 검증자료 확보 후 모델 개발. 미보고를 음성으로 사용하지 않는다. 동물독성, 급성경구 LD50, 수생 EC50은 학습 라벨로 사용하지 않는다. 실측 노출량 없이는 위해성 정량평가를 하지 않는다.

## 검증
현재 코드의 실제 외부 API/원자료 재현 실행은 미검증이다. CI는 문법 검사와 명령행 도움말 실행만 확인하도록 구성한다.
