# Crawled Page: 
            
    Metrics & Ranking - The MAMA-SYNTH Challenge - Grand Challenge

            
                
            
        
- **Source URL:** [https://mamasynth.grand-challenge.org/evaluation/](https://mamasynth.grand-challenge.org/evaluation/)

---

### **Evaluation**[¶](#evaluation "Permanent link")

#### **Overview**[¶](#overview "Permanent link")

Submissions in MAMA-SYNTH are evaluated using a **multi-dimensional framework** designed to assess not only visual similarity to real post-contrast MRI, but also the preservation of clinically meaningful tumor information.

The evaluation combines four complementary components:

1. **Image-to-image fidelity**
2. **ROI-to-ROI tumor realism**
3. **Downstream classification utility**
4. **Downstream segmentation utility**

This design is intended to reward methods that are not only visually plausible, but also useful for clinically relevant downstream tasks.

#### **Evaluation rationale**[¶](#evaluation-rationale "Permanent link")

Virtual contrast-enhancement cannot be assessed adequately using a single image similarity metric alone. A synthetic post-contrast image may appear visually convincing while still failing to preserve diagnostically meaningful enhancement patterns or tumor characteristics.

For this reason, MAMA-SYNTH evaluates methods from multiple perspectives:

* **global image fidelity**, to measure similarity to the reference post-contrast image;
* **tumor-region realism**, to assess whether local enhancement patterns are preserved;
* **classification performance**, to determine whether the synthesized images retain contrast and tumor relevant information;
* **segmentation performance**, to assess whether the synthesized images remain useful for lesion delineation.

Together, these components provide a more clinically grounded assessment of virtual post-contrast image synthesis.

#### **Image-to-image comparison**[¶](#image-to-image-comparison "Permanent link")

The first metric group evaluates the similarity between the synthesized image and the reference post-contrast MRI at the whole-image level.

**Mean Squared Error (MSE)**  
MSE measures the average squared difference between the synthesized image and the ground-truth post-contrast image at the pixel level.

* **Interpretation:** lower is better
* **Purpose:** pixel-level fidelity

**Learned Perceptual Image Patch Similarity (LPIPS)**  
LPIPS measures perceptual distance using deep feature activations and is intended to better reflect human-perceived image similarity than simple pixel-wise comparisons.

* **Interpretation:** lower is better
* **Purpose:** perceptual realism

This metric group is intended to measure whether synthesized images are globally similar to the target post-contrast acquisition, both numerically and perceptually.

#### **ROI-to-ROI tumor realism**[¶](#roi-to-roi-tumor-realism "Permanent link")

The second metric group focuses specifically on the tumor region of interest, where contrast enhancement is most clinically relevant.

**Structural Similarity Index (SSIM)**  
SSIM is computed on the tumor ROI and measures structural similarity between synthesized and reference images in terms of luminance, contrast, and local structure.

* **Interpretation:** higher is better
* **Range:** 0 to 1
* **Purpose:** tumor texture and structural similarity

**Fréchet Radiomics Distance (FRD)**  
FRD measures the Fréchet distance between radiomic feature distributions extracted from synthesized and real post-contrast tumor patches.

* **Interpretation:** lower is better
* **Purpose:** radiomic and statistical realism of tumor enhancement

This ROI-based evaluation is intended to determine whether the synthesized images preserve clinically meaningful local tumor characteristics rather than only global appearance.

#### **Downstream classification evaluation**[¶](#downstream-classification-evaluation "Permanent link")

The third metric group evaluates whether synthesized images retain biologically relevant information using two classification tasks.

**AUROC: Pre Vs. Post**  
This metric measures the classifier's ability to distinguish between pre and post-contrast on synthesized images.

* **Interpretation:** higher is better
* **Reference values:** 1.0 indicates perfect discrimination; 0.5 indicates chance-level performance

**AUROC: Tumor vs. Non-Tumor**  
This metric measures the classifier's ability to distinguish between tumor and non-tumor tissue on synthesized images.

* **Interpretation:** higher is better
* **Reference values:** 1.0 indicates perfect discrimination; 0.5 indicates chance-level performance

This evaluation component is intended to quantify whether virtual contrast enhancement preserves information that is relevant beyond visual appearance alone.

#### **Downstream segmentation evaluation**[¶](#downstream-segmentation-evaluation "Permanent link")

The fourth metric group evaluates whether synthesized post-contrast images remain useful for lesion delineation.

**Dice coefficient**  
The Dice score measures overlap between the predicted tumor segmentation on synthesized post-contrast images and the corresponding ground-truth reference mask.

* **Interpretation:** higher is better
* **Range:** 0 to 1
* **Purpose:** segmentation overlap accuracy

**95th percentile Hausdorff distance (HD95)**  
HD95 measures the distance between predicted and reference segmentation boundaries while reducing sensitivity to extreme outliers.

* **Interpretation:** lower is better
* **Purpose:** segmentation boundary accuracy

This component is intended to assess the practical utility of synthesized images for tumor localization and delineation tasks.

#### **Ranking**[¶](#ranking "Permanent link")

Each submission is assessed within each of the four metric groups:

* **Image-to-image comparison:** MSE, LPIPS
* **ROI-to-ROI tumor realism:** SSIM, FRD
* **Downstream classification:** AUROC (Pre Vs. Post), AUROC (Tumor vs. Non-Tumor)
* **Downstream segmentation:** Dice, HD95

For each group, the relevant metrics are combined into a group-level ranking. The **final challenge ranking** is then obtained by averaging performance across all four evaluation groups.

This ranking strategy is designed to avoid over-optimizing a single narrow aspect of the task. A competitive method should perform consistently across image fidelity, tumor realism, and downstream clinical utility.

#### **Validation and test evaluation**[¶](#validation-and-test-evaluation "Permanent link")

**Validation phase**  
During the validation phase, submissions are evaluated under the official challenge framework to allow participants to test and refine their methods.

**Test phase**  
During the test phase, final submissions are evaluated on the hidden test cohorts and used to determine the official challenge ranking.

Further details regarding leaderboard behavior, score aggregation, and tie-breaking policies will be released together with the final challenge documentation.

#### **Evaluation philosophy**[¶](#evaluation-philosophy "Permanent link")

The goal of MAMA-SYNTH is not merely to identify methods that generate visually appealing synthetic images, but to benchmark methods that preserve clinically relevant information in a robust and useful way.

Competitive methods should therefore balance:

* **fidelity**
* **perceptual realism**
* **tumor-region realism**
* **classification utility**
* **segmentation usefulness**

This evaluation framework reflects the broader goal of supporting clinically meaningful virtual contrast-enhancement methods for breast MRI.