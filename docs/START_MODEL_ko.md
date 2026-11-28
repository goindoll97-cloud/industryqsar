# 모델 시작 안내 — v0.32 (예비 스크리닝 실행 환경)

**GitHub main ZIP 다운로드 후 압축을 푼 상태에서 실행.** 기본 입력은 저장소에 포함된 v0.31 A 33종/B 102종이다. 최종 349/8,110/2,519 자료를 대체하지 않으며, 본 실험이나 검증된 독성 예측기가 아니다.

## Windows (권장)
Python 3.11, 3.12 또는 3.13을 설치하고, 저장소 루트의 `start_model.bat`를 더블 클릭한다. 첫 실행에서 인터넷으로 패키지를 설치한다. 별도 가상환경(.venv-hematotoxicity)을 만들며 GPU가 필요 없다. 실패하면 콘솔 메시지를 확인한다.

## 직접 실행 / macOS, Linux, JupyterLab 터미널
저장소 루트에서 다음을 실행한다(Windows는 가상환경 Python 경로를 .venv-hematotoxicity/Scripts/python.exe로 변경).
```sh
python -m venv .venv-hematotoxicity
.venv-hematotoxicity/bin/python -m pip install -r data/supplementary/hematotoxicity_v031/requirements_model.txt
.venv-hematotoxicity/bin/python data/supplementary/hematotoxicity_v031/run_pilot.py
```
기존 Python 환경 사용 시 `python -m pip install -r data/supplementary/hematotoxicity_v031/requirements_model.txt` 후 `python data/supplementary/hematotoxicity_v031/run_pilot.py` 실행. Windows 명령 프롬프트의 `start_model.bat --ht13` 또는 Python 명령에 `--ht13` 추가하면 HT11~13 탐색 민감도 분석. 기본은 HT01~10.

## 실행 내용
- CAS 및 연결성 중복/교집합, 구조 키, 물질별 제목/출처 URL 존재, B의 비라벨 상태 검사. 출처의 독립 검증을 대신하지 않음.
- RDKit 구조 검출 테스트 31건, 기존 HT 계산표와 대조. HT13 옵션에서 추가 11건 검증.
- Morgan radius 2, 2048 bits. Tanimoto >= 0.5 단일연결 구조군을 만든 뒤 그룹 전체를 제외하는 교차검증. A만 학습, B는 미확인 배경 및 순위 산정용.
- 최대 Tanimoto, Morgan Tanimoto-kernel One-Class SVM, HT exp(-Hamming count) kernel One-Class SVM, 두 kernel 0.5:0.5 결합 One-Class SVM. 기본 nu=0.1. 고정 탐색 설정이며 최적화 결과가 아님.
- 홀드아웃 그룹과 B를 함께 순위화. 상위 5%, 10% (ceil) 회수율 및 enrichment factor, 순위분율. 10자리 반올림 후 동점 내 무작위 순위의 기대값을 부여. B를 음성으로 계산하지 않음.
- 전체 A를 재학습하여 B를 모델별 순위화. 모델 간 원점수 비교/독성확률 해석 금지. HT 모두 0인 물질도 미확인이다.

## 결과 파일
`data/supplementary/hematotoxicity_v031/results/<UTC 실행시각>/`
- retrieval_metrics.csv: 네 모델의 홀드아웃 비교
- candidate_ranking.csv: 네 모델별 B 순위 및 동점범위
- holdout_predictions.csv, fold_membership.csv: 검증 재현 기록
- model_features.npz, features/: 계산된 모델 특성
- run_manifest.json: 설정, 버전, 입력 및 코드 SHA-256, 제한사항

기본 및 HT13 로컬 실행 검증: Python 3.13.5, RDKit 2025.09.4, NumPy 2.3.5, scikit-learn 1.8.0. A33/B102, 구조군 30개, 최대 그룹 2종. Windows 배치 자체는 Windows 환경에서 미실행. 예비 회수율은 낮으며 독립적인 검증이나 결합 효과 입증 결과가 아니다. 본 실험에서 descriptor 유래 연구와 검증물질의 중복을 점검하고 모델/특성 설정을 동결해야 한다.

## 전체 데이터로 교체 (최종 정제 후)
기존 원본을 새로 수집하거나 임의로 대체하지 않는다. CAS, SMILES 및 물질명, 구조 검증 키를 포함하는 적격 A/B CSV와 각 물질에 대응하는 CAS, title, source_url을 포함한 근거표/출처표를 준비한다. B final_label은 공란, A/B는 중복 제거. 출처 제목/URL 검사는 실제 근거 검증이 아니다. 동일 디렉터리에는 쓰지 않으며 사용자 지정 출력은 새 폴더여야 한다.
```sh
python data/supplementary/hematotoxicity_v031/run_pilot.py --a curated_A.csv --b curated_B.csv --a-evidence A_evidence.csv --b-provenance B_provenance.csv --acknowledge-curated --out results/full_exploratory
```
현재 349종 전체 A와 2,519종 전체 스크리닝 원본은 저장소 미공개. 사용자 제공 자료도 이 실행기의 성능을 자동 확정하지 않는다.
