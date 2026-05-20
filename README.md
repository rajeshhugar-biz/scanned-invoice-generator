# Azure Image Pipeline

A pipeline for generating synthetic, multilingual GST invoice images using Azure's GPT-Image-2 API, with realistic scan/photo augmentation effects applied post-generation. Designed for building OCR and document AI training datasets.

## What It Does

1. **Generates** invoice images via Azure OpenAI's `gpt-image-2` model using dynamically composed prompts (language + document type + scan style)
2. **Augments** each image with realistic scanning or photography effects (perspective warp, noise, blur, stains, etc.)
3. **Saves** output images and JSON metadata organized by language

## Supported Languages

| Single | Bilingual |
|--------|-----------|
| English |  |
| Hindi | English–Hindi |
| Marathi | English–Marathi |
| Tamil | English–Tamil |
| Telugu | English–Telugu  |
| Kannada | English–Kannada  |
| Bengali |English–Bengali |

## Document Types (15 Variations)

Retail/FMCG, Restaurant, Electronics/IT, Pharma, Logistics, Grocery/Kirana, Hotel, Manufacturing, SaaS/IT Services, Construction, Textile, Automotive, Agricultural, Educational, Healthcare

## Scan Profiles (6 Augmentation Modes)

| Profile | Weight | Description |
|---------|--------|-------------|
| `mobile_camera` | 30% | Perspective warp, shadows, rotation, JPEG compression |
| `photocopy` | 25% | Paper texture, bleed-through, reduced contrast |
| `clean_laser` | 20% | Minimal effects, high contrast |
| `thermal_faded` | 10% | Faded gray tones, uneven ink density |
| `dot_matrix` | 10% | Horizontal banding, perforation marks |
| `hand_annotated` | 5% | Fold lines, coffee stains, wear |

## Setup

### Prerequisites

- Python 3.8+
- Azure OpenAI resource with `gpt-image-2` deployment

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
AZURE_API_KEY=your_azure_api_key
AZURE_IMAGE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/openai/deployments/gpt-image-2/images/generations
```

## Usage

```bash
python main.py [OPTIONS]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--count N` | `1` | Number of invoices to generate |
| `--language LANG` | `random` | Target language (see list above, or `random`) |
| `--profile NAME` | weighted random | Scan augmentation profile |
| `--size SIZE` | `1024x1792` | Image dimensions (`1024x1024` or `1024x1792`) |
| `--quality LEVEL` | `low` | Azure quality setting (`low`, `medium`, `high`) |
| `--format FMT` | `PNG` | Output format (`PNG`, `JPEG`, `TIFF`) |
| `--output DIR` | `./output` | Output directory |
| `--api-key KEY` | from `.env` | Azure API key override |
| `--endpoint URL` | from `.env` | Azure endpoint override |

### Examples

```bash
# Generate 5 Hindi invoices with default settings
python main.py --count 5 --language Hindi

# Generate 3 Marathi invoices using mobile camera profile
python main.py --count 3 --language Marathi --profile mobile_camera --quality medium

# Generate 10 bilingual invoices at square resolution
python main.py --count 10 --language "English-Hindi bilingual" --size 1024x1024 --quality high
```

## Output Structure

```
output/
└── {language}/
    ├── images/     # PNG image files
    └── metadata/   # JSON metadata per image
```

### Metadata Example

```json
{
  "id": "invoice_azimg_20260519_122631_271_0001",
  "language": "Hindi",
  "scan_profile": "weighted_random",
  "image_path": "output/hindi/images/invoice_azimg_20260519_122631_271_0001.png",
  "generation_time_seconds": 98.22,
  "timestamp": "20260519_122631_271"
}
```

## Rate Limiting & Performance

- Azure API limit: ~2 requests/minute; the pipeline enforces 30-second intervals automatically
- Typical generation time: ~98 seconds per image
- Retry logic: 3 attempts with exponential backoff on timeout or rate-limit errors
- Logs written to `logs/pipeline.log` (rotating, DEBUG level)

## Project Structure

```
azure_image_pipeline/
├── main.py             # Entry point, CLI, pipeline orchestration
├── generator.py        # Azure API image generation
├── scan_augmentor.py   # Image augmentation effects
├── prompts.py          # Prompt templates and style configurations
├── requirements.txt    # Python dependencies
└── .env                # Azure credentials (not committed)
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `python-dotenv` | Load credentials from `.env` |
| `requests` | HTTP calls to Azure API |
| `Pillow` | Image I/O and basic effects |
| `opencv-python-headless` | Perspective transforms, advanced processing |
| `numpy` | Pixel-level array operations |
