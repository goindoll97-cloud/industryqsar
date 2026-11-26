# IndustryQSAR — CMP 유기화학물질의 인체 혈액독성 파일럿

반도체 CMP 관련 유기화합물의 잠재적 인체 혈액 유해성을 탐색하는 연구. 현재는 데이터 구축 단계이며, 확정된 인체 독성 음성 라벨이나 검증된 예측모델은 없다.

## 데이터셋 타당성 검토 (2026-11-26)

**병합 보류: 기초 근거 인벤토리만 승인.** 원본 해시와 추출 수치는 재검증했으나 인체 산업용 흡입 혈액독성 학습·검증 라벨은 미확정이다. 현재 SIDER는 허가자료 이상반응 등록 여부이며 실제 독성 확률이 아니다. [리뷰 및 병합 조건](cmp_hematotoxicity/DATASET_VALIDITY_REVIEW.md)을 먼저 확인할 것.

## 실행
Python 3.11 이상, 저장소 루트:
```powershell
python -m pip install -r cmp_hematotoxicity/requirements.txt
python cmp_hematotoxicity/build_human_base.py --raw data/private/cmp_hematotoxicity/raw
python cmp_hematotoxicity/build_dataset.py
```

- [연구 실행 안내](cmp_hematotoxicity/README.md)
- [데이터 출처, 스냅샷, 변수 정의](cmp_hematotoxicity/HUMAN_BASE_V1.md)
- [CMP 후보물질 및 출처](cmp_hematotoxicity/data/cmp_organic_evidence.csv)

SIDER 미보고는 음성이 아니며 IRIS는 인체 근거 확인 전 검증 라벨로 사용하지 않는다. Long et al. 일반 혈액독성 벤치마크는 혼합 출처이므로 인체 전용 학습에서 제외한다. ToxRefDB 동물자료 역시 제외한다. 실제 사업장 노출이나 발암 위험을 추정하지 않는다. 외부 원자료 및 생성 데이터는 data/private/에 보관한다.

기존 급성경구 LD50 규제 연구는 [archive-acute-ld50-20261126](https://github.com/goindoll97-cloud/industryqsar/tree/archive-acute-ld50-20261126)에 보존했다. 기존 코드 중 구조유사도, CAS 검증, 원문 추적, ablation 아이디어는 추후 혈액독성에 맞게 재구현할 수 있다. 기존 LD50 판정 코드는 현재 분석에서 사용하지 않는다.
