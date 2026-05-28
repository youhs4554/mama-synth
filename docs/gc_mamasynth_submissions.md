# Crawled Page: 
            
    Submissions - The MAMA-SYNTH Challenge - Grand Challenge

            
                
            
        
- **Source URL:** [https://mamasynth.grand-challenge.org/submissions/](https://mamasynth.grand-challenge.org/submissions/)

---

# How to Submit to MAMA-SYNTH[¶](#how-to-submit-to-mama-synth "Permanent link")

Welcome to the MAMA-SYNTH submission guide! This page walks you through everything you need to package your synthesis model and submit it to the challenge — from a working local test all the way to an uploaded algorithm on Grand Challenge.

---

## Overview[¶](#overview "Permanent link")

MAMA-SYNTH submissions run as **Docker containers** on the Grand Challenge (GC) platform. Each container receives a single pre-contrast breast MRI slice, runs your synthesis model, and writes the predicted post-contrast slice to a fixed output path. The evaluation pipeline then scores your output automatically.

No special GC SDK is required — only Docker and a working model.

---

## Step 0: Prerequisites[¶](#step-0-prerequisites "Permanent link")

Before you start, make sure you have:

* **Docker** installed and running (`docker --version`)
* A trained synthesis model (weights + inference code)
* A pre-contrast `.mha` slice for local testing
* A [Grand Challenge account](https://grand-challenge.org/accounts/signup/) and team registration for MAMA-SYNTH

---

## Step 1: Understand the I/O Contract[¶](#step-1-understand-the-io-contract "Permanent link")

The GC platform calls your container once per image. The paths are fixed:

| Direction | Container path | Interface slug |
| --- | --- | --- |
| **Input** | `/input/images/pre-contrast-dce-mri-slice-breast/<uuid>.mha` | `pre-contrast-dce-mri-slice-breast` |
| **Output** | `/output/images/synthetic-contrast-dce-mri-slice-breast/output.mha` | `synthetic-contrast-dce-mri-slice-breast` |

**Image format:** 2-D `float32` `.mha` files, z-score normalised using the MAMA-SYNTH pre-contrast reference statistics (`training_pre_stats.json`, provided in the [challenge repository](https://github.com/mama-research/mama-synth/blob/master/src/preprocessing/training_pre_stats.json).

Your container must:
1. Read the single input `.mha` file from `/input/images/pre-contrast-dce-mri-slice-breast/`.
2. Write a single output file to `/output/images/synthetic-contrast-dce-mri-slice-breast/output.mha`.
3. Exit with code `0` on success.

---

## Step 2: Start from a Baseline[¶](#step-2-start-from-a-baseline "Permanent link")

We provide a ready-to-use [baseline](https://github.com/mama-research/mama-synth/tree/gc_upload/src/submission/identity-baseline) in the challenge repository:

| Baseline | Description | When to use |
| --- | --- | --- |
| `identity-baseline` | Copies input → output (no synthesis) | Start here to verify your Docker setup end-to-end before touching model code |

Clone the repository and copy the baseline that best fits your starting point:

```
git clone https://github.com/mama-research/mama-synth.git
cd mama-synth/src/submission/identity-baseline
```

---

## Step 3: Adapt `inference.py`[¶](#step-3-adapt-inferencepy "Permanent link")

Open `inference.py` and replace the synthesis logic with your own model. The key section to modify is clearly marked:

```
# identity-baseline — replace this block:
output_image = image   # identity copy

# with your model inference, for example:
import your_model
arr = sitk.GetArrayFromImage(image)
arr_out = your_model.predict(arr).astype("float32")
output_image = sitk.GetImageFromArray(arr_out)
output_image.CopyInformation(image)   # ← preserve spacing / origin / direction
```

**Important reminders:**

* The **output must be `float32`** and z-score normalised on the same scale as the input (see `training_pre_stats.json`).
* **Always call `CopyInformation(input_image)`** on your output so that spatial metadata is preserved for the evaluation pipeline.
* The input image is a single 2-D slice, remove any 3-D model assumptions.

---

## Step 4: Update the Dockerfile[¶](#step-4-update-the-dockerfile "Permanent link")

Add your dependencies to `requirements.txt` and place model weights in a `models/` subfolder (or any directory you prefer), then `COPY` them into the image:

Here you can find an example of the [dockerfile](https://github.com/mama-research/mama-synth/blob/gc_upload/src/submission/identity-baseline/Dockerfile).

Key requirements for Grand Challenge compatibility:

* **Platform must be `linux/amd64`** (even when building on Apple Silicon or ARM).
* The container must **run as a non-root user**.
* The `/output` directory must be **writable by that user**.
* GPU access is available during evaluation; use `CUDA_VISIBLE_DEVICES` or set `MAMA_GPU_ID` as needed.

---

## Step 5: Build the Image Locally[¶](#step-5-build-the-image-locally "Permanent link")

```
chmod +x do_build.sh do_test_run.sh do_save.sh
./do_build.sh
```

This runs `docker build --no-cache` and tags the image. The `--no-cache` flag ensures your latest code changes are always picked up.

---

## Step 6: Test Locally[¶](#step-6-test-locally "Permanent link")

Place a pre-contrast `.mha` slice in the expected input folder:

```
cp /path/to/your/DUKE_001.mha \
   test/input/images/pre-contrast-dce-mri-slice-breast/
```

Then run the container against it:

```
./do_test_run.sh
```

On success, your synthesised output will be at:

```
test/output/images/synthetic-contrast-dce-mri-slice-breast/output.mha
```

You can also run the automated validation tests:

```
pip install pytest SimpleITK numpy
pytest test_algorithm.py -v
```

These checks verify that the output file exists, has the correct path, is a valid float32 `.mha`, and has the same spatial dimensions as the input.

---

## Step 7: Export the Container[¶](#step-7-export-the-container "Permanent link")

When your local tests pass, export the Docker image for upload:

```
./do_save.sh
# → mama-synth-<your-algorithm>-v1.0.0.tar.gz
```

Bump the `VERSION` variable in `do_save.sh` before each new upload so that different iterations remain distinguishable.

---

## Step 8: Create an Algorithm on Grand Challenge[¶](#step-8-create-an-algorithm-on-grand-challenge "Permanent link")

1. Go to [grand-challenge.org/algorithms/](https://grand-challenge.org/algorithms/) and click **Create a new algorithm**.
2. Fill in a name (e.g. `MAMA-SYNTH My Method`) and a short description.
3. Set the **inputs** interface to `pre-contrast-dce-mri-slice-breast` and **outputs** to `synthetic-contrast-dce-mri-slice-breast`.
4. Under **Container Management**, click **Upload a new container** and upload your `.tar.gz`.
5. Wait for GC to validate and activate the image (typically within a few hours, up to 24 h).

---

## Step 9: Submit to the Challenge Phase[¶](#step-9-submit-to-the-challenge-phase "Permanent link")

Once your algorithm is active:

1. Navigate to the [MAMA-SYNTH challenge page](https://mamasynth.grand-challenge.org/).
2. Go to **Submit** and select the desired phase (**Validation** or **Test**).
3. Choose your algorithm from the dropdown and confirm the submission.
4. Results will appear on the leaderboard once evaluation completes.

> **Tip:** Use the **Debug phase** to test the upload. For tuning your model, you can submit to **Validation Phase** upto five times. The **Test phase** uses the hidden test cohorts and determines the official ranking.

---

## Common Pitfalls[¶](#common-pitfalls "Permanent link")

| Issue | Fix |
| --- | --- |
| Container exits with a non-zero code | Check GC logs; the most common cause is a wrong input path or a missing output file |
| Output `.mha` not found | Ensure you write to `/output/images/synthetic-contrast-dce-mri-slice-breast/output.mha` exactly |
| Wrong image dtype | Cast your output array to `float32` before creating the SimpleITK image |
| Spatial metadata mismatch | Call `output_image.CopyInformation(input_image)` to preserve spacing and origin |
| Image built for wrong platform | Add `--platform linux/amd64` to your `docker build` command |
| Permission denied on `/output` | Confirm your Dockerfile creates `/output` and assigns it to the non-root user |

---

## Resources[¶](#resources "Permanent link")

* **Challenge repository** (baselines, preprocessing, evaluation): [github.com/mama-research/mama-synth](https://github.com/mama-research/mama-synth/)
* **Grand Challenge documentation**: [grand-challenge.org/support/](https://grand-challenge.org/support/)
* **Algorithm creation guide**: [grand-challenge.org/algorithms/](https://grand-challenge.org/algorithms/)
* **Evaluation details**: [mamasynth.grand-challenge.org/evaluation/](https://mamasynth.grand-challenge.org/evaluation/)

---

## Questions?[¶](#questions "Permanent link")

If you run into issues not covered here, please reach out:

* Smriti Joshi — [smriti.joshi@ub.edu](mailto:smriti.joshi@ub.edu)
* Richard Osuala — [richard.osuala@gmail.com](mailto:richard.osuala@gmail.com)
* Jarek van Dijk — [jarek.vandijk@radboudumc.nl](mailto:jarek.vandijk@radboudumc.nl)

Good luck, and we look forward to seeing your submissions! 🎯