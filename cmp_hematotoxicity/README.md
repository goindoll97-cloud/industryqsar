# CMP organic chemicals and hematotoxicity: dataset pilot

## 실행 (저장소 루트, PowerShell)
```powershell
git fetch origin
git switch cmp-hematotoxicity-data
python -m pip install -r cmp_hematotoxicity/requirements.txt
python cmp_hematotoxicity/build_dataset.py --only candidates
python cmp_hematotoxicity/build_dataset.py
```
원본 및 생성물은 기본적으로 data/private/cmp_hematotoxicity에 저장. 외부 데이터 라이선스 확인 전 재배포 금지.
Hugging Face 데이터는 SMILES/Y를 제공하지만 route 및 개별 실험 근거가 없음. 원 논문의 scaffold train/test/external 1330/442/610과 HF 재분할 1788/594는 동일 분할이 아님. 원본 분할을 복원하기 전에는 논문 외부검증 재현이라고 주장하지 말 것.

## 데이터
- cmp_organic_evidence.csv: 69 evidence rows, 56 unique names. 특허 후보, 실시예, 출판된 모사실험을 구분. 실제 삼성 사용, 규제 미지정, 혈액독성 미확인을 입증하지 않음.
- PubChem 이름 매칭은 잠정적이며 CAS/입체화학/염 형태의 수기 검증 필요. 실패/복수 CID도 보존. 이름만으로 CAS를 추측하지 않음.
- hematox_benchmark.csv: 일반 혈액독성 분류 벤치마크. 흡입독성 정답이나 발암성 정답으로 사용 금지.
- inhalation_studies_TEMPLATE.csv: 반복 흡입 연구 원자료 추출용 빈 스키마. 현재 실측 행 없음.
- 공정 부산물은 실제 분석 확인 후 별도 등록. 현재 유기 부산물의 검출 근거 없음.
- 기존 main 코드 및 자료 보존. 급성 경구 LD50/ECOSAR/수생 EC50은 혈액독성 정답으로 사용하지 않음.

## 확보할 원자료
1. Long et al. DOI https://doi.org/10.1021/acs.jcim.2c01088 원문 및 전체 supplementary files, 원래 train/test/external split과 라벨 정의.
2. https://huggingface.co/datasets/maomlab/HematoxLong2023 (license unspecified; local retrieval only).
3. https://www.epa.gov/comptox-tools/downloadable-computational-toxicology-data ToxRefDB study/effect/dose/chemical tables 및 data dictionary; ToxValDB는 보조 근거.
4. https://repdose.item.fraunhofer.de/ 반복 흡입 혈액/골수 endpoint export 및 접근 조건.
5. CMP 제품별 SDS 1/3/8/9/11절, 작업별 공기측정/사용 후 슬러리 유기성분 분석. 자료가 없다면 후보 스크리닝으로 한정.
6. https://doi.org/10.1016/j.chemosphere.2017.10.138 원문 및 supplement (실제 실험 조성/폐기물 분석 확인).
7. KOSHA section 11 raw XML, 기존 산업물질 CAS 목록(사용자 로컬 보관); 공개 저장소에 키나 비공개 자료 업로드 금지.

## 다음 분석 원칙
반복 흡입 혈액학/골수 효과를 1차 endpoint로 설정하되 충분한 시험 수를 확인한 후 결정. 백혈구 감소와 증가, 골수 병변, 적혈구 이상을 별도 보존. 음성은 해당 endpoint를 평가했고 유해영향이 없었다는 명시적 시험 근거가 필요. 미시험/미보고는 unknown. 경구와 흡입 및 사람/동물 자료 혼합 금지. 농도 및 노출기간을 보존하고 NOAEC/LOAEC를 구분. 구조 그룹 단위 검증 및 적용영역 분석 수행. 실측 노출농도가 없으면 정량 위험도 산출 금지.

## 검증 상태
이 브랜치에서 원격 데이터 다운로드 및 코드 실행은 아직 검증되지 않았음. CSV는 문헌 기반 초기 목록이며 독성/노출 측정 데이터는 아님.
