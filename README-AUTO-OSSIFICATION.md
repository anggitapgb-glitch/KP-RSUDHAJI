# OSSIA - Automatic exploratory carpal/ossification candidate pipeline

This adds a no-manual-mask exploratory baseline.

## Install
```bash
pip install opencv-python numpy
```

## Run
From the project root:
```bash
python test_ossification_auto.py "outputs/roi/carpal_roi.png"
```

Optional parameter comparison:
```bash
python test_ossification_auto.py "outputs/roi/carpal_roi.png" --region-percentile 55 --candidate-percentile 70
python test_ossification_auto.py "outputs/roi/carpal_roi.png" --region-percentile 58 --candidate-percentile 75
python test_ossification_auto.py "outputs/roi/carpal_roi.png" --region-percentile 62 --candidate-percentile 80
```

Outputs:
`outputs/auto_ossification/`
- `01_enhanced.png`
- `02_auto_carpal_region_mask.png`
- `03_auto_region_overlay.png`
- `04_ossification_candidate_mask.png`
- `05_ossification_candidate_overlay.png`

## Important limitations
This is an intensity/morphology baseline operating on a pre-cropped carpal ROI.
It is not a trained anatomical segmentation model, may include non-carpal structures,
and does not reliably separate the eight carpal bones. Candidate bright pixels are
not automatically equivalent to ossification centers. Do not interpret the ratio
as a clinical measure until the target definition, expert-reviewed reference masks,
and validation (e.g. Dice/IoU on held-out images) are established.
For deployment, keep a human review/correction step.
