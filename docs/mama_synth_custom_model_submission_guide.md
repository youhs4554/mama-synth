# MAMA-SYNTH — Custom Model (U-Net, Diffusion, etc.) Submission Guide

이 가이드는 Pix2PixHD GAN이 아닌 **임의의 사용자 정의 딥러닝 모델(예: PyTorch U-Net, Diffusion, TensorFlow, ONNX 등)**을 MAMA-SYNTH Challenge에 제출하기 위해 제출 템플릿을 수정하고 패키징하는 방법에 대한 실전 개발자 가이드입니다.

---

## 1. 어떤 템플릿으로 시작할 것인가?

제출할 커스텀 모델의 특징에 따라 적절한 시작 템플릿을 선택합니다.

* **경량 모델 또는 가중치 파일이 없는 경우 (또는 코드 내에 포함):**
  - [identity-baseline](https://github.com/youhs4554/mama-synth/tree/master/src/submission/identity-baseline) 템플릿을 복사하여 시작합니다.
* **별도의 가중치 파일(예: `.pth`, `.ckpt`, `.onnx`, `.h5`)이 있고 GPU 가속이 필요한 경우 (권장):**
  - [submission-gan](https://github.com/youhs4554/mama-synth/tree/master/src/submission/submission-gan) 템플릿을 복사하여 시작합니다. (가중치 스테이징 및 GPU 컨테이너 설정이 이미 포함되어 있어 수정하기 편리합니다.)

---

## 2. 뼈대 파일 복사 및 환경 준비

터미널에서 템플릿 폴더를 복사하여 새로운 제출 프로젝트를 생성합니다.
```bash
cp -r src/submission/submission-gan src/submission/submission-my-model
cd src/submission/submission-my-model
```

---

## 3. 모델 가중치(Weights) 스테이징 및 빌드 설정

도커 이미지를 빌드할 때 가중치 파일을 안전하게 포함시키기 위해 빌드 스크립트를 수정합니다.

### 1단계: `do_build.sh` 수정
`do_build.sh` 파일은 로컬 디렉터리에 있는 가중치를 빌드 컨텍스트 안으로 복사하는 역할을 합니다.
```bash
# do_build.sh 파일 내부 수정
export MODEL_WEIGHTS_DIR="~/Desktop/my_model_weights" # 가중치 파일이 있는 로컬 경로
MODEL_STAGE_DIR="./models/my_model"

mkdir -p "$MODEL_STAGE_DIR"
# 자신의 모델 가중치 파일 복사 (예: best_model.pth)
cp "$MODEL_WEIGHTS_DIR/best_model.pth" "$MODEL_STAGE_DIR/"
```

### 2단계: `Dockerfile` 수정
가중치 파일을 컨테이너 내부로 올바르게 복사하고 복사된 폴더에 권한을 부여합니다.
```dockerfile
# Dockerfile 내부 수정
# 1. 딥러닝 프레임워크에 맞는 베이스 이미지 선택 (PyTorch 예시)
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# 2. 작업 디렉토리 설정 및 라이브러리 설치
WORKDIR /opt/algorithm
COPY requirements.txt /opt/algorithm/
RUN pip install --no-cache-dir -r requirements.txt

# 3. 모델 가중치 폴더 복사 및 비루트(non-root) 권한 부여
COPY --chown=algorithm:algorithm models/my_model /opt/algorithm/models/my_model
COPY --chown=algorithm:algorithm inference.py /opt/algorithm/
```

---

## 4. 추론 코드 (`inference.py`) 개발

자신의 커스텀 모델을 로드하고 SimpleITK 이미지(`.mha`)를 받아 추론을 수행한 뒤 다시 SimpleITK 이미지로 내보내는 핵심 로직을 구성합니다.

```python
import os
import SimpleITK as sitk
import numpy as np
import torch
import torch.nn as nn

# [필수] 자신의 커스텀 모델 클래스 정의 또는 임포트
class MyUNet(nn.Module):
    def __init__(self):
        super().__init__()
        # ... 모델 레이어 정의 ...
    def forward(self, x):
        # ... 순전파 ...
        return x

def load_model(weights_path, device):
    model = MyUNet()
    # 컨테이너 환경의 가중치 로드
    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model

def run():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 1. 경로 설정 (MAMA-SYNTH 규격 고정)
    input_dir = "/input/images/pre-contrast-dce-mri-slice-breast/"
    output_dir = "/output/images/synthetic-contrast-dce-mri-slice-breast/"
    os.makedirs(output_dir, exist_ok=True)
    
    input_files = [f for f in os.listdir(input_dir) if f.endswith(".mha")]
    if not input_files:
        raise RuntimeError("No input .mha file found")
        
    input_path = os.path.join(input_dir, input_files[0])
    output_path = os.path.join(output_dir, "output.mha")
    
    # 2. SimpleITK 이미지 로드 및 Numpy 변환
    input_image = sitk.ReadImage(input_path)
    input_array = sitk.GetArrayFromImage(input_image) # Shape: (H, W) 또는 (1, H, W)
    
    # [정규화 주의 사항]
    # 입력 mha는 평균 0, 표준편차 1로 z-score 정규화되어 들어옵니다.
    # 만약 모델이 [0, 1] 또는 [0, 255] 데이터를 기대한다면 역정규화를 먼저 수행해야 합니다.
    # 예: raw = input_array * std + mean
    
    # 3. 텐서 변환 및 배치 차원 추가
    # Shape: (1, 1, H, W)
    input_tensor = torch.from_numpy(input_array).float().unsqueeze(0).unsqueeze(0).to(device)
    
    # 4. 모델 추론
    weights_file = "/opt/algorithm/models/my_model/best_model.pth"
    model = load_model(weights_file, device)
    
    with torch.no_grad():
        output_tensor = model(input_tensor)
        
    # 5. Numpy 변환 및 SimpleITK 복원
    output_array = output_tensor.squeeze().cpu().numpy().astype(np.float32)
    output_image = sitk.GetImageFromArray(output_array)
    
    # [중요] 공간 메타데이터(Spacing, Origin, Direction) 복사
    # 이를 빠뜨릴 경우 평가 서버에서 매칭 오류로 실패합니다.
    output_image.CopyInformation(input_image)
    
    # 6. 결과 저장
    sitk.WriteImage(output_image, output_path)
    print("Inference completed successfully!")

if __name__ == "__main__":
    run()
```

---

## 5. 정규화(Normalisation) 설계 팁

딥러닝 모델의 학습 환경에 맞게 입력/출력 픽셀 값을 올바르게 정규화해야 모델의 합성 성능이 보장됩니다.

1. **z-score 학습 모델:**
   - 만약 모델이 z-score 정규화된 이미지로 학습되었다면, 입력 이미지(`.mha`)를 별도의 역정규화 없이 그대로 모델에 입력합니다.
2. **Min-Max 정규화 학습 모델 (예: [0, 1] 또는 [-1, 1]):**
   - **입력 시:** MAMA-SYNTH reference statistics를 사용해 원본 스케일로 돌려놓은 뒤, 학습에 썼던 방식대로 Min-Max Scaling을 수행합니다.
     - `raw = z_score * std + mean` (클리핑 및 스케일링)
   - **출력 시:** 모델 출력을 다시 z-score 스케일로 역변환하여 저장합니다.
     - `z_output = (raw_output - mean) / std`

---

## 6. 의존성 정의 및 로컬 검증

### 1단계: `requirements.txt` 작성
모델 작동에 필요한 파이썬 라이브러리를 기재합니다.
```text
numpy
SimpleITK
torch
torchvision
```

### 2단계: 로컬 테스트 실행
```bash
# 1. 로컬 테스트를 위한 MHA 입력 이미지 배치
cp /path/to/test_image.mha test/input/images/pre-contrast-dce-mri-slice-breast/

# 2. 로컬 빌드 및 GPU 실행 테스트
./do_build.sh
./do_test_run.sh

# 3. CPU 모드로 빌드/디버그 테스트 수행 시
USE_GPU=0 ./do_test_run.sh
```

---

## 7. 패키징 및 제출

모든 로컬 테스트가 통과되면 패키징을 수행합니다.
```bash
./do_save.sh
# -> mama-synth-my-model-v1.0.0.tar.gz 파일 생성 완료
```
생성된 `.tar.gz` 파일을 **Grand Challenge 알고리즘 컨테이너 관리(Container Management)** 페이지에 업로드하여 제출을 완료합니다.
