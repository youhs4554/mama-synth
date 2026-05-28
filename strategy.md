# MAMA-SYNTH 2026 (MICCAI) 참가 전략

> Pre-contrast T1 유방 MRI → 합성 peak-enhancement post-contrast DCE-MRI 합성 챌린지에 대한
> Task 분석 · 선행연구 · 주최측 전처리/평가 코드 분석 · 단일 GPU(RTX A4500 20GB) 기반 접근법 제안.
>
> 작성 근거: `docs/` 내 공식 문서 + `mama-research/mama-synth` 저장소 코드 분석 + 최신 문헌 리서치.
> 작성일: 2026-05-28

---

## 문서 맵 및 작업 기준

`strategy.md`만 보고도 다음 작업을 진행할 수 있도록, 세부 근거는 아래 로컬 문서를 기준으로 확인한다.

- **챌린지 핵심**: `docs/gc_mamasynth_introduction.md`, `docs/gc_mamasynth_data.md`, `docs/gc_mamasynth_metrics.md`, `docs/gc_mamasynth_timeline.md`, `docs/gc_mamasynth_submissions.md`.
- **제출/운영**: `docs/mama_synth_custom_model_submission_guide.md`, `docs/mama_synth_identity_baseline_readme.md`, `docs/mama_synth_gan_submission_readme.md`, `docs/gc_doc_building_and_testing_the_container.md`, `docs/gc_doc_runtime_environment.md`, `docs/gc_doc_making_a_challenge_submission.md`, `docs/gc_doc_try_out_your_algorithm.md`, `docs/gc_doc_try_out_your_algorithm_and_publish_a_test_case.md`, `docs/gc_doc_upload_the_model_weights_separately.md`.
- **GC 설정**: `docs/gc_doc_create_an_algorithm_page.md`, `docs/gc_doc_choose_input_and_output_interfaces.md`, `docs/gc_doc_add_the_algorithm.md`, `docs/gc_doc_exporting_the_container.md`, `docs/gc_doc_linking_a_github_repository_to_your_algorithm.md`.
- **코드 엔트리포인트**: 전처리 `src/preprocessing/preprocess.py`, 통계 `src/preprocessing/compute_dataset_stats.py`, 평가 `src/evaluation/evaluate.py`, 메트릭 구현 `src/evaluation/evaluators/`, 제출 템플릿 `src/submission/identity-baseline/`, `src/submission/submission-gan/`.
- **공유 언어**: `CONTEXT.md`가 생기면 MAMA-SYNTH 작업의 canonical 용어집으로 취급한다. 아직 없으면 첫 용어가 사용자와 합의되는 시점에만 생성한다.
- 일부 `mama_synth` 계열 문서의 원문 URL은 개인 fork를 가리키지만, 작업 기준은 **현재 로컬 저장소 경로와 공식 `mama-research/mama-synth` I/O 계약**으로 통일한다.

## Grill-With-Docs 작업 흐름

모델 설계, 평가 해석, 데이터셋 경계, 제출 운영처럼 용어가 결과물 이름과 실험 판단에 영향을 주는 작업은 구현 전에 grill-with-docs 흐름으로 정렬한다.

1. `CONTEXT.md`가 있는지 먼저 확인한다. 없으면 빈 파일을 미리 만들지 말고, 첫 번째 프로젝트 고유 용어 또는 관계가 합의될 때 생성한다.
2. 질문은 한 번에 하나만 던지고, 각 질문마다 권장 답을 함께 제시한다. 코드나 문서에서 확인 가능한 내용은 사용자에게 묻기 전에 직접 확인한다.
3. "baseline", "validation", "test", "mask", "synthetic post", "subtraction", "ROI", "proxy metric"처럼 overloaded term은 `CONTEXT.md` 정의와 충돌하지 않는지 확인한다.
4. 합의된 용어는 즉시 `CONTEXT.md`에 저장한다. 저장 형식은 짧은 정의, 피해야 할 alias, 관계/경계, 남은 모호성이다.
5. `CONTEXT.md`에는 구현 세부사항, 학습 레시피, 실험 결과, TODO를 넣지 않는다. 이 문서는 glossary이며, `strategy.md`는 전략/근거/운영 계획을 담는다.
6. 되돌리기 어렵고, 맥락 없이는 놀랍고, 실제 trade-off가 있었던 결정은 `CONTEXT.md`가 아니라 `docs/adr/`의 ADR 후보로 분리한다.

## 0. 핵심 요약 (TL;DR)

- **Task**: pre-contrast T1 유방 MRI **2D 슬라이스 1장** → **peak-enhancement post-contrast** 슬라이스 1장 합성. 슬라이스는 "악성 종양 면적이 가장 큰" 슬라이스.
- **평가는 4개 그룹의 동등가중 평균 랭킹**: ① 영상충실도(MSE↓, LPIPS↓) ② 종양 ROI 사실성(SSIM↑, FRD↓) ③ 다운스트림 분류(AUROC pre-vs-post↑, tumor-vs-비종양↑) ④ 다운스트림 분할(Dice↑, HD95↓). **한 메트릭만 과최적화하면 진다.**
- **가장 재현성 높은 설계 원칙 3가지** (문헌·주최자 논문 공통):
  1. **Subtraction(잔차) 타깃 학습**: post 자체가 아니라 `post − pre`(조영증강 신호)를 예측 → 모든 메트릭 그룹에서 이득.
  2. **Tumor-aware 지도학습**: ROI 가중 loss 또는 mask-conditioning → SSIM-ROI·FRD·AUROC·Dice를 끌어올림.
  3. **Full-breast 학습**: 양측 유방을 함께 학습(대칭성 단서) → single-breast보다 우수.
- **20GB GPU 현실 권고**: 로컬 학습/실험 기준은 RTX A4500 20GB다. ① 1순위 = **pix2pixHD baseline 개선(+feature-matching+ROI loss+subtraction)** — 저위험·고성능. ② 2순위 = **Latent Diffusion(SD AE 동결 + ControlNet pre-contrast 조건화, CC-Net 방식)** — latent 공간이라 20GB에 들어감, FRD/AUROC 강점. **픽셀공간 full-res DDPM은 피할 것.** 제출 추론은 GC T4 16GB/A10G 24GB에서 OOM 없이 돌아야 한다.
- **검증은 FID가 아니라 FRD로**: FID는 구조를 망가뜨린 모델을 "최고"로 오인할 수 있음(주최자 FRD 논문이 명시).
- 평가용 분류기/분할(nnU-Net) **가중치는 저장소에 미포함** → 로컬에서 공식 metric 100% 재현은 일부 불가. proxy 검증 파이프라인을 직접 구축해야 함.

---

## 1. 챌린지 Task 분석

### 1.1 목표와 동기
DCE-MRI는 유방암 진단·치료계획·모니터링에 핵심이지만, gadolinium 조영제는 **체내 침착/신독성**, **환경 오염(식수에서 검출)**, **비용·접근성** 문제를 야기한다. MAMA-SYNTH는 **조영제 없이(contrast-free) 또는 저감(contrast-reduced)** 워크플로우를 위한 가상 조영증강(virtual contrast enhancement, VCE) 생성모델의 **표준 벤치마크**를 제공한다.

### 1.2 입출력 정의
- **입력**: pre-contrast T1-weighted 유방 MRI **2D 축상(axial) 슬라이스** 1장. (GC 인터페이스 slug `pre-contrast-dce-mri-slice-breast`)
- **출력**: 같은 슬라이스에 대응하는 **peak-enhancement 시점**의 합성 post-contrast DCE-MRI 슬라이스 1장. (slug `synthetic-contrast-dce-mri-slice-breast`)
- **슬라이스 선택**: 환자별 DCE 검사에서 **악성 종양 면적이 가장 큰 슬라이스**를, **peak-enhancement phase**(종양 영역 신호강도가 최대인 시점)에서 추출.
- **포맷**: 2D `float32` `.mha`, **z-score 정규화**(학습셋 pre-contrast mean/std 기준). spacing/origin/direction 메타데이터 보존 필수.

### 1.3 데이터셋
| 항목 | Training (MAMA-MIA) | Test A (Radboud UMC, NL) | Test B (Inst. A. Fleming, AR) |
|---|---|---|---|
| 역할 | 개발/학습 | 외부 테스트 | 외부 테스트 |
| 케이스 수 | 1,506 (25+ 센터, 미국) | 200 | 100 |
| 영상 크기 | 가변 | 416×416 | 512×512 |
| 자기장 | 1.5T 72% / 3T 28% | 3T | 1.5T |
| 제조사 | GE 64% / Siemens 27% / Philips 9% | Siemens | GE |
| 평면 | Axial 84% / Sagittal 16% | Axial | Axial |
| 지방억제 | - | Yes | Yes |
| 분자아형 | - | Luminal 86% 多 | Luminal 37% / TN 30% (다양) |

- **핵심 함의**: 학습은 미국 다기관, 테스트는 **네덜란드·아르헨티나 외부기관** → **도메인 시프트(스캐너·프로토콜·인구·자기장)에 대한 일반화**가 승부처. 테스트 분포(3T Siemens / 1.5T GE, 지방억제, 축상)에 맞춘 강건성이 중요.
- **데이터/모델 정책**: 챌린지 데이터 + **공개 데이터셋/공개 사전학습 모델만** 허용(private 금지). 공개 리소스는 **Validation phase 시작 전인 2026-05-07 23:59 CET 이전**에 접근 가능해야 한다. NIH CADR 사용 금지(EO 14117 / 28 CFR 202 준수). 외부 데이터·pretrained weight·오픈소스 구현 사용 시 문서화 필수. 평가 파이프라인 점수만 직접 극대화하는 metric gaming은 실격 사유이며, top-3는 전체 학습 코드 제출 요구 가능.
  - 활용 가능 공개 데이터 예: **Duke-Breast-Cancer-MRI**(주최자 baseline이 이걸로 학습), 기타 공개 유방 DCE-MRI.

### 1.4 평가 구조 (★승부의 핵심)
4개 그룹, 그룹별 랭킹 후 **4그룹 랭킹의 단순평균 = 최종 순위**. → **균형 잡힌 다목적 성능**이 좁은 단일 최적화를 이긴다.

| 그룹 | 메트릭 | 방향 | 의미 |
|---|---|---|---|
| ① 영상충실도 | MSE, LPIPS | ↓, ↓ | 픽셀+지각적 유사도 |
| ② 종양 ROI 사실성 | SSIM(tumor), FRD | ↑, ↓ | 국소 조영증강 사실성/방사체학 분포 |
| ③ 다운스트림 분류 | AUROC(pre vs post), AUROC(tumor vs 비종양) | ↑, ↑ | 조영/종양 정보 보존 |
| ④ 다운스트림 분할 | Dice, HD95 | ↑, ↓ | 병변 윤곽 묘사 유용성 |

> **중대한 긴장관계**: MSE(L2) 최적화는 **regression-to-mean 블러**를 유발해 ②③④가 보상하는 "선명한 종양 조영증강"을 뭉갠다. 반대로 GAN/diffusion은 선명하지만 hallucination으로 MSE/LPIPS를 해칠 수 있다(perception–distortion tradeoff). 4그룹 평균 랭킹이므로 **이 균형을 잡는 팀이 이긴다.**

### 1.5 단계 & 일정
- **Validation phase**: 2026-05-08 개시, 50 케이스, **최대 5회 제출**로 튜닝.
- **Test phase**: 2026-06-25 개시, 숨겨진 300 케이스, 공식 순위 결정.
- **마감**: 2026-07-10 / 결과 공개 2026-08-01 / 수상 발표 2026-09-27 (Deep-Breath Workshop @ MICCAI 2026).
- **상금**: 1st €500 / 2nd €250 / 3rd €150 / Best Paper €300(Deep-Breath 워크숍 논문, 리더보드 무관).
- **제출 형식**: Docker 컨테이너(`linux/amd64`, non-root), GC 플랫폼 업로드. SDK 불필요.

> 오늘(2026-05-28) 기준 **Validation phase 이미 개시(5/8)**, Test phase 개시까지 약 4주. 제출 5회 제한이 있으므로 **로컬 검증을 견고히 한 뒤** validation 제출을 아껴 써야 한다.

---

## 2. 선행연구 (Previous Works, 최신 위주)

### 2.1 유방 MRI 가상 조영증강 — 주최자 계열(★필독)
주최자(Osuala, Garrucho, Joshi, Han, Zhang, Lekadir, Diaz 등)가 이 파이프라인 대부분을 이미 출판했다. **이들 논문이 곧 챌린지 설계 의도**이다.

- **Osuala et al., "Pre- to Post-Contrast Breast MRI Synthesis for Enhanced Tumour Segmentation"** (SPIE MI 2024, arXiv:2311.10879, code: `RichardObi/pre_post_synthesis`).
  **← 챌린지 baseline (medigan model `00023`, pix2pixHD).** Duke 데이터, 512² 2D 축상. 핵심 발견: ① 합성 post가 pre보다 real post에 의미·지각적으로 훨씬 가까움, ② **subtraction(post−pre) 영상이 재구성 메트릭을 크게 개선**, ③ 합성데이터 증강이 다운스트림 3D 분할을 향상. 모델선택 지표 **SAMe** 제안.

- **Osuala et al., "Towards Learning Contrast Kinetics with Multi-Condition Latent Diffusion Models" (CC-Net)** (MICCAI 2024, arXiv:2403.13890, code: `RichardObi/ccnet`).
  **← 가장 직접적인 diffusion 방법.** 동결된 SD2.1 AE + **ControlNet**(pre-contrast 주입) + 시간(acquisition time) 다중조건화로 **DCE 시퀀스(조영동역학)** 생성. 20GB 학습에 중요한 실전 팁: latent 공간으로 메모리 절감, **AE latent scale s≈0.1**(기본 0.18215 아님)이 품질↑, **gradient value clipping**으로 폭주 방지, DDPM 1000 step, AdamW, batch 8–32.

- **Lang, Osuala et al., "Temporal Neural Cellular Automata (TeNCA)"** (2025, arXiv:2506.18720).
  경량 NCA로 조영증강을 물리적으로 그럴듯한 시간진행으로 모델링. **CC-Net 대비 image-level 메트릭(LPIPS·SSIM·MS-SSIM·PSNR)에서 우세, 파라미터 훨씬 적음**. 반면 CC-Net은 분포메트릭(FID/FRD) 우세하나 "hallucination 경향". → **fidelity vs realism 분열을 명시**. 20GB에 trivially 적합.

- **Ibarra, Osuala et al., "Comparing Conditional Diffusion Models for Synthesizing CE Breast MRI from Pre-Contrast"** (Deep-Breath @ MICCAI 2025, arXiv:2508.13776).
  **← 설계선택 결정에 가장 유용(MAMA-MIA 기반).** DDPM 변형 체계적 비교 결과:
  - **SUB(subtraction) 타깃이 직접 PC 합성을 일관되게 능가** (image-level + ROI/FRD).
  - **Tumor-aware loss(SUB-ROI)가 ROI 메트릭·FRD/FID 추가 개선.**
  - **Mask-conditioning(PC-ROI(M100))이 종양 조영증강을 눈에 띄게 개선**(종양 위치 근사 필요).
  - **Full-breast 학습이 single-breast 능가**(대칭성 단서).
  - 6인 전문가 리더 스터디로 사실성 검증.

- **Han et al., "Tumor-Attentive Segmentation-Guided GAN (TSGAN)"** (IEEE Access 2022, PMC9721354).
  **← 종양인지 유방 VCE GAN의 정석.** pix2pixHD 위에 **국소 종양 판별자 + 분할 분기(Dice+BCE) + curriculum learning**(전체유방→종양ROI). 종양 ROI에서 SSIM 0.868/PSNR 72.8 (Pix2Pix 0.713/63.9). 박스 약지도(TSGAN-Box)도 가능 → **MAMA-SYNTH의 ROI/분할 메트릭에 직결.**

- **인접 연구**: Müller-Franzes/Truhn et al., *Radiology* 2023 (CE 유방 MRI 시뮬레이션 리더 스터디); Fonnegra et al. 2024 (arXiv:2409.01596, 등록+시간동역학 TI curve 모델링).

### 2.2 타 장기 조영제 저감 (전이 가능한 교훈)
- **Gong et al.** "Deep learning enables reduced gadolinium dose for brain MRI" (*JMRI* 2018) — 2D U-Net+residual로 **10× 조영제 저감**. 시초.
- **Pinetz et al.** "Gadolinium dose reduction … conditional deep learning" (arXiv:2403.03539, 2024) — **조영 신호(residual)만 예측**, dose/noise/scanner 조건화로 정확한 증강. → "전체 영상이 아니라 증강 잔차를 예측하라"(§2.1 SUB와 동일 교훈).

### 2.3 일반 의료영상 I2I 아키텍처
**GAN(빠름·선명·mode collapse 위험)**
- **pix2pix**(CVPR'17), **pix2pixHD**(CVPR'18) — paired cGAN + L1 + adversarial + **feature-matching loss**(블러 완화). **← 챌린지 baseline.**
- **SPADE**(2019) — mask-conditioning. **MedGAN**(2018) — perceptual+style+content loss.
- CycleGAN(unpaired) — MAMA-MIA는 paired라 적합성 낮음.

**Diffusion(고충실도·추론 느림 — 단, 추론속도는 채점 안 됨)**
- **Palette**(SIGGRAPH'22) — 조건부 I2I diffusion 표준 레시피.
- **BBDM: Brownian Bridge Diffusion**(CVPR'23, arXiv:2205.07680) — 소스↔타깃 직접 stochastic bridge. 의료 결정론적 변형(arXiv:2503.22531, 2025).
- **SynDiff**(IEEE TMI 2023, arXiv:2207.08208) — **adversarial diffusion**(큰 reverse step) + cycle-consistency, **빠르고 unpaired** 다중대비 MRI.
- **Latent Diffusion(LDM)**(CVPR'22) — CC-Net 백본, **20GB의 핵심 enabler**(압축 latent). **MedLoRD**(2025)는 24GB에서 조건부 LDM 학습 확인.

**판정**: paired·픽셀충실도 채점 환경에선 잘 튜닝된 GAN/회귀가 여전히 경쟁력. MAMA-MIA에서는 주최자 비교 결과 **subtraction-타깃·tumor-aware/mask-conditioned DDPM**이 우세, TeNCA는 경량으로 image-level 우세.

### 2.4 FRD — 직접 최적화 대상
- **Konz, Osuala et al., "Fréchet Radiomic Distance (FRD)"** (arXiv:2412.01496, code `RichardObi/frd-score`). FID의 ImageNet feature를 **표준화된 해석가능 radiomic feature**로 대체. 의료 I2I에서 FID/KID/CMMD/RadFID 능가. **결정적 경고**: FID/KID/CMMD가 골구조를 파괴한 MUNIT을 "최고"로 오인 → **MAMA-SYNTH가 종양패치 FRD를 쓰는 이유.** → 픽셀 loss뿐 아니라 **종양 ROI의 radiomic feature 분포를 맞춰라.**

### 2.5 유사 챌린지: SynthRAD2023 (가장 정보가치 높은 유사 사례)
- Huijben et al., *Medical Image Analysis* 2024 (arXiv:2403.08447). MRI→CT / CBCT→CT, MeanThenRank.
  - **Transformer 백본이 CNN U-Net 능가**(상위권).
  - **영상유사도 메트릭과 다운스트림(dose) 정확도 간 유의 상관 없음** → MAMA-SYNTH 다중그룹 랭킹의 실증 근거이자 "MSE 과적합 금지" 경고.
  - 우승 다수가 **조건부 GAN + (점증하는) diffusion**, 전처리/정규화·2.5D 공간배치가 결정적.

### 2.6 선행연구 종합 — "무엇이 통하고 왜인가"
| 교훈 | 근거 | 챌린지 적용 |
|---|---|---|
| **Subtraction(잔차) 타깃** | Osuala'24, Ibarra'25, Pinetz'24 | post 직접합성 대신 `post−pre` 예측, 추론 시 pre 더해 복원 |
| **Tumor-aware loss / mask-conditioning** | TSGAN'22, Ibarra'25 | ROI 가중 + (가능시) 종양마스크 조건화 → ②③④ 향상 |
| **Full-breast 학습** | Ibarra'25 | 단측 크롭 금지, 양측 함께 |
| **FRD로 검증, FID 불신** | Konz'24 | 로컬에 `frd-score` 설치, 종양패치 radiomics 점검 |
| **Perception–distortion 균형** | Blau&Michaeli'18, YODA arXiv:2505.02048 | regression-style/few-step 샘플링으로 곡선상 유리점 선택 |
| **정규화/도메인 강건성** | SynthRAD'23 | train/inference z-score 정확히 일치, 테스트 분포(3T/1.5T) 강건화 |

---

## 3. 전처리 & 평가 방법 (주최측 코드 분석: `mama-research/mama-synth`)

> 저장소 구조: `src/preprocessing/`, `src/evaluation/{evaluators,models,ground_truth,tests}`, `src/submission/{identity-baseline, submission-gan}`.

### 3.1 전처리 파이프라인 (`src/preprocessing/preprocess.py`)
1. **Peak phase 선택** (`find_peak_phase`): 전체 3D 볼륨에서 각 phase별 **종양마스크 내부 평균강도**(`volume[seg>0]`) 계산 → 최대 phase가 peak. pre-contrast = phase index 0(최저).
2. **Slice 선택** (`find_largest_label_slice`): through-plane 축에서 **종양 라벨 voxel 수가 최대**인 슬라이스(`np.argmax`). 축 결정(`determine_slice_axis`)은 크기·spacing 휴리스틱(애매하면 `--skip_ambiguous_shapes`로 스킵).
3. **z-score 정규화** (`zscore_normalise`): `(img − mean)/std` (float32, std=0이면 0). **pre와 peak 모두 동일한 pre-contrast 전역 통계 사용.** `--global_stats` 필수.
   - **`training_pre_stats.json` 실제 값**: `mean = 107.4119`, `std = 219.9618`, `n_voxels ≈ 2.136e10`, `n_patients = 1506`. (Welford 온라인 알고리즘, 최저 phase 볼륨 기준)
4. **출력**: SimpleITK `.mha`, **float32**(`nan_to_num`→`astype float32`), 마스크는 int16. **리샘플/리사이즈 없음**(native 슬라이스 크기 유지). 저장 전 **90° CCW 회전**(`np.rot90(k=1)`)을 pre/peak/mask에 적용. PNG는 시각화용(정규화 스펙 아님).
5. **지방억제·유방크롭·bias 보정 없음** (전처리 단계엔 종양마스크 외 영역 처리 없음). 대측유방 처리는 평가단계에만 존재.

> **함의**: 입력은 z-score(평균0·표준편차1 근방, 음수 포함) float32. 모델은 이 스케일에서 동작하거나, baseline GAN처럼 `raw = z*std+mean`로 역정규화→처리→재정규화해야 함. 출력도 **동일 z-score 스케일 float32**여야 평가가 정상.

### 3.2 평가 파이프라인 (`src/evaluation/evaluators/`)
`evaluate.py::run_evaluation()`가 4개 evaluator 순차 실행, 실패해도 나머지 진행, `metrics.json` 출력. **모든 메트릭은 z-score 정규화 영상에서 직접 계산**(per-image 추가 정규화 없음 — MSE/LPIPS/SSIM 편향 방지). 예측은 사전 정규화 가정.

- **MSE** (`image_metrics.py`): `np.mean((pred−gt)**2)` (float64, per-case).
- **LPIPS**: **torchmetrics** `LearnedPerceptualImagePatchSimilarity(net_type="alex")` — **AlexNet 백본**(레거시 `lpips` 패키지 아님). 영상 **±5σ 클립** 후 동일 결정적 변환으로 [-1,1] 매핑(per-image min-max 아님).
- **SSIM(tumor)** (`roi_metrics.py`): `skimage structural_similarity(data_range=10.0, full=True)`로 **전체영상 SSIM map** 계산 후 **종양마스크 내부만 평균**(`ssim_map[mask].mean()`), win_size=7. `ssim_tumor`로 보고.
- **FRD**: **`frd-score`** 라이브러리, `compute_frd([gt,pred], paths_masks=[mask,mask], frd_version="v1")`. v1 = z-score/D1 정규화, **~464 radiomic feature**(Original+LoG+Wavelet), 종양마스크 조건. **aggregate scalar**(≥2 케이스 필요).
- **분류 AUROC 2종** (`classification.py`, aggregate):
  - **contrast**: 합성-post(라벨1) vs real pre(라벨0), **종양 ROI radiomic feature**.
  - **tumor_roi**: 종양 ROI(1) vs **대측 미러링 ROI**(0). 미러는 `mirror_utils.create_mirrored_mask()`(중앙선 검출 후 좌우 미러).
  - 분류기: `RadiomicsClassifier`(기본 `XGBClassifier(n_estimators=100, max_depth=5)`, pyradiomics IBSI feature) 또는 `CNNClassifier`(timm `efficientnet_b0`, 224). `EnsembleClassifier`로 `{task}_classifier*.pkl/.pt` 자동탐색.
- **분할 Dice/HD95** (`segmentation.py`): **nnU-Net v2**(`nnUNetPredictor`, tile_step 0.5, gaussian+mirroring TTA, fold 0, `checkpoint_final.pth`)로 합성영상에 추론→GT마스크 비교. Dice=`2|∩|/(|p|+|g|)`(둘 다 비면 1.0), HD95=거리변환 기반 95퍼센타일. 빈 마스크 페널티 = Dice 0, HD95 = 영상 대각선.
- **랭킹 코드는 저장소에 없음**(문서상 프로즈만): 4그룹 각각 그룹랭킹 → **4그룹 평균 = 최종**. 정확한 동점처리/정규화 규칙은 "추후 공개".

### 3.3 제출 인터페이스 (I/O contract)
- 입력 `/input/images/pre-contrast-dce-mri-slice-breast/<uuid>.mha` → 출력 `/output/images/synthetic-contrast-dce-mri-slice-breast/output.mha`.
- **float32 z-score `.mha`**, `output.CopyInformation(input)`로 spacing/origin/direction 보존 필수.
- 입력은 **단일 2D 슬라이스** → 3D 모델 가정 제거. Docker `linux/amd64`, non-root, `/input` read-only, `/output`·`/tmp` 쓰기가능, GPU 사용 가능(`CUDA_VISIBLE_DEVICES`/`MAMA_GPU_ID`).
- GC 런타임은 **케이스 1개씩 실행**되고 **네트워크 접근 없음**. 모델 코드·가중치·통계파일·런타임 리소스는 빌드 시 이미지 안(`/opt/...`)에 넣거나 GC model upload 기능으로 제공해야 한다. Dockerfile에서 `/tmp`에 넣은 파일은 런타임에 남지 않는다고 가정.
- Algorithm 생성 시 GPU/memory를 명시한다. GC 런타임 문서 기준 GPU 인스턴스는 T4 16GB(`ml.g4dn.*`) 또는 A10G 24GB(`ml.g5.*`) 계열이며, 조직/챌린지에 활성화된 타입만 요청 가능하다. 현재 런타임은 NVIDIA driver 535 / CUDA 12.0, `/dev/shm`은 시스템 메모리의 50%, 시스템용 1GiB RAM 예약, phase별 runtime limit 적용.
- **baseline 2종**: `identity-baseline`(pass-through, 인프라 점검용), `submission-gan`(medigan `00023` pix2pixHD; z-score↔uint8 PNG 브리징 포함, 가중치는 빌드시 외부 staging).
- 제출 템플릿 선택: 경량/무가중치 모델은 `identity-baseline` 복사, GPU+외부 가중치 모델은 `submission-gan` 복사가 더 안전하다(`do_build.sh`의 `MODEL_WEIGHTS_DIR` staging과 GPU Docker 설정 재사용).
- 커스텀 모델 `inference.py` 필수 흐름: 입력 `.mha` 탐색 → SimpleITK 로드 → 학습 스케일에 맞게 전처리 → 모델 추론 → `float32` 배열 저장 → `CopyInformation(input)` → `output.mha` 기록.
- 가중치 배포 선택지: ① 컨테이너 내부 `resources/` 또는 `models/`로 COPY, ② GC *Models* 페이지에 tarball 업로드 후 런타임 `/opt/ml/model/`에서 로드. 큰 가중치는 ②가 업데이트/용량 관리에 유리하다. 두 방식을 섞지 말고, `MODEL_WEIGHTS_DIR` staging 모델인지 `/opt/ml/model/` 로딩 모델인지 `inference.py`와 테스트에서 명확히 고정한다.
- 로컬 제출 검증 순서: `./do_build.sh` → `./do_test_run.sh`(필요시 `USE_GPU=0`) → `pytest test_algorithm.py -v` → `./do_save.sh` → GC Algorithm page의 *Containers → Upload a Container*. 컨테이너 활성화는 보통 수십 분 걸릴 수 있으며, 이후 새 컨테이너 업로드로 교체 가능.
- GC 제출 운영: challenge *Submit* 페이지에서 phase를 선택하고 editor 권한이 있는 Algorithm을 고른다. Challenge용 Algorithm 생성 시 인터페이스는 자동 구성되며 title·GPU·memory만 설정한다. 새 컨테이너 업로드는 제출을 자동 생성하지 않으므로, 활성화 후 challenge phase에 다시 수동 제출해야 한다. Validation 제출을 쓰기 전에 **Try-out Algorithm**으로 known `.mha` 1건을 실행하고 Results/Logs에서 출력·GPU·memory를 확인한 뒤, 가능하면 Debug phase를 먼저 사용한다.
- 컨테이너는 가능하면 10GB 미만으로 유지하고, 큰 가중치는 별도 model upload를 선호한다. `do_save.sh`의 `VERSION`을 제출마다 올려 컨테이너를 구분한다. 컨테이너 활성화는 보통 ~20분이나 최대 24시간까지 잡고, phase별 최대 runtime 안에 추론이 끝나는지 GC logs에서 확인한다.
- 관련 `docs/` 참조: `gc_mamasynth_submissions.md`, `gc_mamasynth_debug_leaderboard.md`, `mama_synth_custom_model_submission_guide.md`, `mama_synth_identity_baseline_readme.md`, `mama_synth_gan_submission_readme.md`, `gc_doc_create_your_own_algorithm.md`, `gc_doc_download_example_code.md`, `gc_doc_add_the_algorithm.md`, `gc_doc_making_a_challenge_submission.md`, `gc_doc_create_an_algorithm_page.md`, `gc_doc_choose_input_and_output_interfaces.md`, `gc_doc_building_and_testing_the_container.md`, `gc_doc_runtime_environment.md`, `gc_doc_exporting_the_container.md`, `gc_doc_upload_the_model_weights_separately.md`, `gc_doc_try_out_your_algorithm.md`, `gc_doc_try_out_your_algorithm_and_publish_a_test_case.md`, `gc_doc_linking_a_github_repository_to_your_algorithm.md`.

### 3.4 의존성 (`requirements.txt` 요지)
`SimpleITK>=2.2`, `scikit-learn>=1.2`, `scipy>=1.10`, `scikit-image>=0.20`, `pyradiomics`(AIM-Harvard git master — PyPI는 py≥3.10 깨짐), `frd-score>=1.0`, `torchmetrics>=1.0`, `torch<2.10`, `nnunetv2>=2.4`, `xgboost<2.0`. **`lpips` 패키지·monai 없음.**

### 3.5 로컬 평가 셋업 — 반드시 인지할 제약
- **학습된 가중치 일체 미포함**: 분류기 `.pkl/.pt`, nnU-Net `checkpoint_final.pth`, pix2pixHD 가중치 모두 저장소엔 `.gitkeep`만. → **공식 ③④ 메트릭을 로컬에서 그대로 재현 불가.**
- **ground_truth 데이터도 미포함.** → 로컬 검증은 **자체 hold-out + 자체 proxy 분할/분류기**로 구성해야 함(아래 §4.6).
- **GC 환경에서만** 공식 분류기/nnU-Net으로 ③④가 채점됨.

### 3.6 로컬 데이터셋 경로 운영
원본 MRI 데이터셋은 저장소 안에 두지 않는다. 실제 데이터 루트는 사용자가 로컬 디스크/외장 SSD/서버 마운트 상황에 맞춰 나중에 결정하고, 이 저장소에는 `datasets` 심볼릭 링크만 둔다.

권장 개념 구조:
```bash
# 실제 원본/가공 데이터 루트: 사용자가 이후 결정
<USER_DECIDED_DATA_ROOT>/mama-synth/
  raw/
    mama-mia/
      images/
      segmentations/
  processed/
    mama-mia-2d/
      mha/
        input/
        ground_truth/
        mask/
      png/
      intensity_plots/
      report.csv
  eval/
    predictions/
    metrics_out/
    models/
  weights/
    pix2pixhd-00023/
    custom/

# repo 내부 편의 경로
datasets -> <USER_DECIDED_DATA_ROOT>/mama-synth
```

심볼릭 링크 생성 예시:
```bash
# <USER_DECIDED_DATA_ROOT>는 실제 저장 위치가 정해진 뒤 치환한다.
ln -s <USER_DECIDED_DATA_ROOT>/mama-synth datasets
```

이후 명령은 repo 기준 상대경로로 짧게 유지한다.
```bash
python src/preprocessing/preprocess.py \
  --image_dir datasets/raw/mama-mia/images \
  --seg_dir datasets/raw/mama-mia/segmentations \
  --output_dir datasets/processed/mama-mia-2d \
  --global_stats src/preprocessing/training_pre_stats.json
```

운영 규칙:
- `datasets` symlink 자체는 개인 머신 의존 경로이므로 커밋하지 않는다.
- 원본 MRI, mask, processed `.mha`, predictions, model weights, evaluation model은 모두 `datasets/` 아래 또는 repo 밖에 둔다.
- Docker build context에 `datasets`가 포함되지 않게 `.dockerignore`가 생기면 반드시 `datasets`를 추가한다.
- 코드에서 경로를 기록할 때는 가능하면 `Path(...).resolve()`로 실제 데이터 루트를 함께 로그에 남긴다.

### 3.7 실행 명령 치트시트
```bash
# 의존성 설치
pip install -r requirements.txt

# 공개 테스트 실행
PYTHONPATH=src/evaluation pytest src/evaluation/tests src/preprocessing/test_preprocess.py -v

# 로컬 공식 평가 엔트리포인트(데이터/모델 경로 필요)
export MAMA_PREDICTIONS_DIR=/path/to/predictions
export MAMA_GT_DIR=/path/to/ground_truth
export MAMA_MASKS_DIR=/path/to/masks
export MAMA_MODELS_DIR=/path/to/evaluation_models
export MAMA_OUTPUT_DIR=/path/to/metrics_out
python src/evaluation/evaluate.py

# identity baseline 컨테이너
cd src/submission/identity-baseline
./do_build.sh && ./do_test_run.sh && pytest test_algorithm.py -v && ./do_save.sh

# pix2pixHD GAN baseline 컨테이너
cd ../submission-gan
export MODEL_WEIGHTS_DIR=/path/to/00023
./do_build.sh && ./do_test_run.sh && pytest test_algorithm.py -v && ./do_save.sh

# 커스텀 모델 템플릿 시작점
cd ..
cp -r submission-gan submission-my-model
```

---

## 4. 접근법 제안 (로컬 RTX A4500 20GB 한도)

아래 설계는 로컬 학습/실험을 RTX A4500 20GB 1장에 맞춘 것이다. 최종 제출 컨테이너는 GC에서 활성화된 T4 16GB 또는 A10G 24GB 추론 환경에서도 별도 검증해야 한다.

### 4.1 설계 원칙 (문헌·평가구조에서 도출)
1. **Subtraction 타깃**: 모델은 `Δ = post − pre`를 예측, 추론 시 `post_hat = pre + Δ_hat`. 정적 해부 제거 → ②③④ 동시 이득(가장 재현성 높은 "공짜 점심").
2. **Tumor-aware 지도**: ROI 가중 L1/perceptual + (가능 시) 종양마스크 조건화(SPADE/ControlNet). 학습엔 MAMA-MIA 종양 분할이 있으므로 활용. *단, 테스트 입력엔 마스크가 없음* → mask-conditioning은 "마스크 없이도 동작"하도록 설계하거나, 자체 coarse localizer로 생성.
3. **Full-breast 학습**: 양측 함께(대칭성).
4. **Perception–distortion 균형**: MSE만 좇지 말 것. 적대/지각 loss를 섞되, diffusion이면 few-step/regression-style 샘플링으로 균형.
5. **도메인 강건성**: 학습셋(미국 다기관)과 테스트(3T Siemens / 1.5T GE) 분포차 → 강한 intensity/contrast augmentation, 정규화 정합.
6. **FRD로 모델선택**: 로컬에 `frd-score` 설치, 종양패치 FRD + LPIPS + ROI-SSIM으로 체크포인트 선택(MSE 단독 금지).

### 4.2 단계적 로드맵
**Phase 0 — 인프라 검증 (1~2일)**
- `identity-baseline`로 GC 제출 end-to-end 확인 → 리더보드 하한 확보.
- `submission-gan`(pix2pixHD `00023`) 빌드/로컬 추론 성공 → 정규화 브리징·가중치 staging 이해.
- 커스텀 모델은 먼저 `submission-gan` 템플릿 복사 후 `inference.py`, `requirements.txt`, `Dockerfile`, `do_build.sh`만 교체한다. `MODEL_WEIGHTS_DIR` 기반 staging 또는 GC `/opt/ml/model/` 로딩 중 하나를 명시적으로 선택한다(§3.7 명령으로 검증).
- 검증: Docker 빌드 성공 + `do_test_run.sh` 성공 + `pytest test_algorithm.py -v` 성공 + `output.mha` float32·동일 dims·메타데이터 보존.
- GC 활성화 후 `Try-out Algorithm`으로 known `.mha`를 실행하고 Results/Logs에서 stdout/stderr, GPU, memory, runtime을 확인한다. Validation 제출 전 Debug phase로 한 번 더 확인한다.

**Phase 1 — pix2pixHD baseline 개선 (저위험 메인, 1~2주)**
- baseline에 ① **subtraction 타깃** ② **ROI 가중 + feature-matching + LPIPS-style perceptual loss** ③ **TSGAN식 종양 판별자/분할 분기**(curriculum) 추가.
- MAMA-MIA로 자체 재학습(Duke 대신/추가). 512² 또는 416²(테스트 해상도 정합 고려).
- 검증: 자체 hold-out에서 LPIPS↓·ROI-SSIM↑·FRD↓ 동시 개선 → validation 1회 제출.

**Phase 2 — Latent Diffusion (고성능 도전, 2~3주, 시간 허용 시)**
- **CC-Net 방식**: SD2.1 AE 동결 + ControlNet(pre-contrast 조건) + (subtraction 타깃). latent scale s≈0.1, grad value clip, batch≤8.
- few-step/regression-style 샘플링(YODA/ExpA)으로 MSE 회복.
- 검증: Phase1 대비 FRD/AUROC proxy 향상하면서 MSE 큰 손실 없는지.

**Phase 3 — 앙상블/선택 (선택)**
- 메트릭 그룹별 강점이 다르면(예: TeNCA=image-level, diffusion=FRD) **그룹별 최적 모델 분석 후 단일 제출 모델 선정**. 추론속도 무관하므로 무거운 모델도 OK.

### 4.3 아키텍처 옵션 비교 (20GB 관점)
| 옵션 | 메모리 | 추론속도 | 강점 메트릭 | 위험 | 권고 |
|---|---|---|---|---|---|
| **pix2pixHD+ROI+SUB** | 여유(512² 가능) | 빠름 | MSE·LPIPS, ROI↑ | mode collapse | **1순위(메인)** |
| **Latent Diffusion(SD AE+ControlNet)** | 적합(latent, batch≤8) | 느림(무관) | FRD·AUROC·realism | 학습 까다로움, hallucination | **2순위(상향)** |
| **TeNCA(temporal NCA)** | 매우 여유 | 빠름 | image-level(LPIPS/SSIM/PSNR) | 분포메트릭 약함 | 보조/실험 |
| 픽셀공간 full-res DDPM | **20GB 초과 위험** | 매우 느림 | - | 메모리/시간 | **회피** |
| SynDiff(adversarial diffusion) | 중간 | 중간 | 다중대비 | 구현복잡 | 여력 시 |

### 4.4 20GB 실현가능성 메모
- **pix2pixHD 512²**: 단일 A4500에서 batch 1~4로 학습 가능(generator+multi-scale D). 충분.
- **Latent Diffusion**: AE 동결 시 학습 대상은 UNet+ControlNet. latent(예: 64²×4)에서 batch 8까지 가능. **이것이 20GB에서 diffusion을 쓰는 유일하게 현실적인 길.**
- **혼합정밀(AMP)·gradient checkpointing·grad accumulation** 적극 사용.
- 입력이 2D 단일슬라이스라 3D 부담 없음 → 메모리 매우 유리.

### 4.5 Loss 설계 (Phase 1 기준 예시)
```
L = λ_pix · L1(Δ_hat, Δ_gt)                      # 픽셀 충실도(MSE 그룹)
  + λ_roi · L1_in_tumorROI(Δ_hat, Δ_gt)          # ROI 가중(②④ 강화)
  + λ_perc · LPIPS(post_hat, post_gt)             # 지각(LPIPS 그룹)
  + λ_fm  · FeatureMatching(D)                    # 블러 완화(pix2pixHD)
  + λ_adv · Adversarial(global D + tumor D)       # 선명/사실성(TSGAN)
  + λ_seg · Dice/BCE(분할분기, post_hat)          # ④ 다운스트림 정렬
```
- λ는 **로컬 proxy 메트릭(특히 FRD·ROI-SSIM)** 기준으로 튜닝. MSE만 보고 키우지 말 것.

### 4.6 로컬 검증 전략 (공식 가중치 부재 대응)
- **자체 hold-out**: MAMA-MIA를 train/val로 분할(센터 단위 분할로 도메인시프트 모사 권장).
- **메트릭**: MSE·LPIPS(torchmetrics alex, ±5σ 클립)·SSIM-tumor(skimage, data_range=10, win7)·**FRD(frd-score v1, 종양마스크)**를 **공식 구현 그대로** 재현한다. 엔트리포인트는 `src/evaluation/evaluate.py`, 구현은 `src/evaluation/evaluators/{image_metrics,roi_metrics,classification,segmentation}.py`, 경로 설정은 `MAMA_PREDICTIONS_DIR`, `MAMA_GT_DIR`, `MAMA_MASKS_DIR`, `MAMA_MODELS_DIR`, `MAMA_OUTPUT_DIR`를 사용한다.
- **③④ proxy**: 종양 ROI radiomics + XGBoost로 pre-vs-post / tumor-vs-미러ROI AUROC 자체 학습; 자체 nnU-Net(또는 MAMA-MIA 학습 분할기)으로 Dice/HD95 proxy. **절대값은 GC와 다르지만 상대비교/체크포인트 선택엔 충분.**
- **모델선택**: 4그룹 proxy를 **랭크-평균**으로 합쳐(공식 랭킹 모사) 단일 점수로 체크포인트 선택.

### 4.7 실험 진행 모니터링 (Experiment Tracking)
**기본 원칙**: 실험 추적은 **로컬 우선 MLflow + TensorBoard** 조합을 기본으로 한다. MRI 데이터·마스크·합성 출력·가중치는 보호/대용량 산출물이므로 외부 SaaS에 올리지 않는다. W&B 같은 외부 도구는 scalar-only/offline/private 모드 보조 옵션으로만 둔다. GC 제출 컨테이너는 런타임 네트워크가 없으므로 monitoring service에 의존하면 안 된다.

**권장 디렉터리**
```
experiments/
  mlruns/                 # MLflow local file store
  tensorboard/            # TensorBoard event files
  configs/                # 실행 config snapshot
  reports/                # metric summary csv/json, plots
  runs/<run_id>/           # checkpoints, predictions, debug figures
```
`experiments/`, `checkpoints/`, `predictions/`, `outputs/`, Docker tarball, model weights는 git에 커밋하지 않는다. 최종 논문/PR에는 원본 산출물 대신 aggregate metric table, sanitized plot, 실행 config checksum만 남긴다.

**run_id 규칙**
`YYYYMMDD-HHMM_<model>_<target>_<split>_<shortgit>` 형식을 쓴다.
예: `20260528-2130_pix2pixhd-sub_roi_split-center_a1b2c3d`.

**반드시 기록할 metadata**
- 코드 상태: git commit, dirty 여부, 실행 명령, config 파일 경로와 resolved config.
- 데이터 상태: train/val split ID, 제외 케이스 목록 checksum, `training_pre_stats.json` mean/std, resize/crop/rot90/augmentation 설정.
- 모델 상태: architecture variant, target(`post` vs `subtraction`), loss weights, pretrained weight 출처, seed.
- 런타임 상태: GPU 모델/VRAM, CUDA/PyTorch 버전, batch size, AMP/checkpointing/grad accumulation, epoch time, peak memory.
- 제출 상태: submission template(`identity-baseline`, `submission-gan`, custom), Docker tag/version, `MODEL_WEIGHTS_DIR` 또는 `/opt/ml/model/` 사용 여부.

**metric logging schema**
step 단위 train/val loss와 epoch 단위 challenge proxy를 분리한다.

| group | metric key | 방향 | 기록 주기 |
|---|---|---|---|
| image fidelity | `val/mse`, `val/lpips` | ↓ | epoch/checkpoint |
| tumor ROI realism | `val/ssim_tumor`, `val/frd` | ↑/↓ | epoch/checkpoint |
| classification proxy | `val/auroc_contrast_proxy`, `val/auroc_tumor_roi_proxy` | ↑ | selected checkpoints |
| segmentation proxy | `val/dice_proxy`, `val/hd95_proxy` | ↑/↓ | selected checkpoints |
| selection | `val/proxy_rank_mean`, `val/selection_score` | ↓ 또는 ↑ 명시 | selected checkpoints |
| operations | `sys/gpu_mem_gb`, `sys/epoch_sec`, `sys/infer_sec_case` | 참고 | epoch |

MLflow에는 scalar metric, config, metric summary JSON/CSV, sanitized plots, checkpoint path만 기록한다. TensorBoard에는 loss curve, learning rate, ROI crop debug image, prediction-vs-target montage를 기록하되, 외부 공유 금지 산출물로 취급한다.

**실행 예시**
```bash
# 로컬 MLflow UI
mlflow ui \
  --backend-store-uri file:./experiments/mlruns \
  --host 127.0.0.1 \
  --port 5000

# TensorBoard UI
tensorboard \
  --logdir ./experiments/tensorboard \
  --host 127.0.0.1 \
  --port 6006
```

**체크포인트 승격 게이트**
1. `val/mse`, `val/lpips`, `val/ssim_tumor`, `val/frd`가 baseline 대비 동시에 악화되지 않을 것.
2. proxy ③④는 절대값보다 baseline 대비 상대 순위와 `proxy_rank_mean` 개선을 우선한다.
3. top-k checkpoint는 같은 hold-out split에서 inference output을 저장하고 `metrics.json`, config, model hash를 함께 묶는다.
4. Validation 제출은 MLflow run에 `gc_validation_submission=true`, submission date, container version, leaderboard result를 태그로 남긴다.
5. 동일 validation 결과를 재현할 수 있는 training config와 inference config가 남아 있지 않으면 Test phase 후보로 승격하지 않는다.

### 4.8 리스크 & 함정 체크리스트
**모델/평가 게이트**
- [ ] 출력 스케일을 **z-score float32**로 정확히 맞춤(역정규화 누락 시 MSE 폭망).
- [ ] `CopyInformation` 호출(메타데이터) — 누락 시 평가 오류.
- [ ] 90° 회전 규약 일치(전처리가 rot90 적용 → 학습/추론 일관).
- [ ] mask-conditioning 모델은 **테스트엔 마스크 없음** → 마스크-free 추론경로 필수.
- [ ] FID 대신 **FRD**로 검증(FID 신뢰 금지).
- [ ] MLflow/TensorBoard run에 config·split·checkpoint·metric summary가 남아 있는지 확인.
- [ ] 보호 MRI 데이터·마스크·가중치·합성 출력은 cloud tracker에 업로드하지 않음.
- [ ] validation 제출 **5회 제한** → 로컬에서 충분히 검증 후 제출.

**제출/GC 게이트**
- [ ] Docker `linux/amd64`·non-root·`/input` read-only 가정·`/output` 쓰기권한.
- [ ] GC 런타임 **네트워크 없음** → 가중치/통계/코드/리소스 이미지 포함 또는 `/opt/ml/model/` 업로드.
- [ ] GPU/memory 설정은 GC Algorithm form에서 명시하고, T4 16GB/A10G 24GB 중 활성화된 타입과 phase runtime limit에 맞춘다.
- [ ] 별도 model upload 사용 시 tarball을 Algorithm *Models* page에 업로드하고, `inference.py`는 `/opt/ml/model/`만 바라보게 한다.
- [ ] `./do_build.sh` → `./do_test_run.sh` → `pytest test_algorithm.py -v` → `./do_save.sh` 순서로 제출 전 검증.
- [ ] GC `Try-out Algorithm` + Results/Logs 확인 + Debug phase를 거친 뒤 Validation 제출을 사용.
- [ ] 새 컨테이너 활성화 후 **challenge phase에 다시 수동 제출**(업로드만으로 제출 완료 아님).
- [ ] 컨테이너 10GB 미만 권장, 큰 모델은 GC model upload로 분리.

**데이터/규정 게이트**
- [ ] 외부 데이터·pretrained model은 **공개+문서화**만(private/NIH CADR 금지), 2026-05-07 23:59 CET 이전 공개 리소스인지 확인.
- [ ] metric gaming 금지, final evaluation model이 validation/released checkpoint와 다를 수 있음을 가정.
- [ ] top-3 진입 시 training code·inference script·외부 리소스 문서 제출 가능성을 준비.
- [ ] 도메인시프트(3T Siemens / 1.5T GE) 대비 augmentation/정규화 강건화.

---

## 5. 권장 실행 계획 (현 일정 기준)

| 시점 | 작업 | 검증 게이트 |
|---|---|---|
| 즉시(~6/1) | identity-baseline GC 제출, Debug phase/Try-out 확인, pix2pixHD baseline 로컬 재현, 로컬 평가 파이프라인(공식 메트릭 import + proxy ③④) 구축 | 리더보드 하한 확보 + 로컬 메트릭 재현 |
| ~6/15 | **Phase 1**: SUB 타깃 + ROI/FM/perceptual + 종양 D 개선 pix2pixHD 재학습(MAMA-MIA, full-breast) | hold-out에서 LPIPS↓·ROI-SSIM↑·FRD↓ → validation 1회 |
| ~6/25 | (여력 시) **Phase 2**: latent diffusion(SD AE+ControlNet, SUB), few-step 샘플링 | proxy FRD/AUROC↑, MSE 손실 제한 |
| 6/25~7/10 | Test phase: 최적 단일모델 선정·제출, 도메인 강건성 점검 | 4그룹 proxy 랭크-평균 최상 모델, 컨테이너 활성화 24h 버퍼 고려해 7/9 이전 업로드 권장 |
| ~9/27 | Deep-Breath 워크숍 논문(Best Paper €300 대상) | - |

---

## 참고문헌

- **MAMA-SYNTH Challenge** — https://www.ub.edu/mama-synth/mama-synth · https://mamasynth.grand-challenge.org/ · proposal Zenodo:19852228 · code https://github.com/mama-research/mama-synth
- **MAMA-MIA dataset** — Garrucho et al., *Scientific Data* 12:453 (2025); arXiv:2406.13844
- **pix2pixHD pre→post (baseline)** — Osuala et al., SPIE MI 2024; arXiv:2311.10879; code https://github.com/RichardObi/pre_post_synthesis
- **CC-Net (multi-condition LDM)** — Osuala et al., MICCAI 2024; arXiv:2403.13890; code https://github.com/RichardObi/ccnet
- **Comparing conditional diffusion (MAMA-MIA)** — Ibarra/Osuala et al., Deep-Breath 2025; arXiv:2508.13776
- **TeNCA (temporal NCA)** — Lang/Osuala et al., 2025; arXiv:2506.18720
- **TSGAN (tumor-attentive)** — Han et al., IEEE Access 2022; PMC9721354
- **Müller-Franzes/Truhn, simulate CE breast MRI** — *Radiology* 2023; doi radiol.213199
- **Fonnegra late-stage CE** — 2024; arXiv:2409.01596
- **Gong reduced gadolinium dose** — *JMRI* 48(2):330 (2018)
- **Pinetz conditional dose reduction** — 2024; arXiv:2403.03539
- **pix2pix / pix2pixHD** — Isola CVPR'17 / Wang CVPR'18 · **SPADE** Park'19 · **MedGAN** 2018 arXiv:1806.06397
- **Palette** SIGGRAPH'22 · **BBDM** CVPR'23 arXiv:2205.07680 (의료 결정론 arXiv:2503.22531) · **SynDiff** TMI'23 arXiv:2207.08208 · **LDM** Rombach CVPR'22 · **MedLoRD** 2025 arXiv:2503.13211
- **FRD metric** — Konz/Osuala et al., 2024; arXiv:2412.01496; code https://github.com/RichardObi/frd-score
- **Perception–distortion** — Blau & Michaeli, CVPR 2018 · **YODA "Regression is all you need"** — 2025 arXiv:2505.02048
- **SynthRAD2023** — Huijben et al., *Medical Image Analysis* 97:103276 (2024); arXiv:2403.08447
- **medigan** — Osuala et al., *J. Medical Imaging* 2023; arXiv:2209.14472
