<div align="center">

# 🎯 UI-UG: A Unified MLLM for UI Understanding and Generation


[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Paper](https://img.shields.io/badge/paper-arxiv-red.svg)](https://arxiv.org/abs/2509.24361)
[![Hugging Face Model](https://img.shields.io/badge/🤗%20Hugging%20Face-UI--UG--7B-yellow.svg)](https://huggingface.co/neovateai/UI-UG-7B)
[![Hugging Face Model](https://img.shields.io/badge/🤗%20Hugging%20Face-UI--UG--7B--2601-orange.svg)](https://huggingface.co/neovateai/UI-UG-7B-2601)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717.svg?logo=github)](https://github.com/neovateai/UI-UG)

[**📖 Paper**](https://arxiv.org/abs/2509.24361) | [**🤗 Model**](https://huggingface.co/neovateai/UI-UG-7B) | [**🚀 Quick Start**](#-quick-start) | [**📊 Evaluation**](#-evaluation) | [**📄 License**](#-license)

</div>

## 🌟 Overview

UI-UG (A Unified MLLM for UI Understanding and Generation) is a multimodal large model that simultaneously supports both UI understanding and UI generation. It supports various tasks including referring, grounding, captioning and generation.

> **🚀 New Release: UI-UG-7B-2601 🔥🔥🔥 ** - This latest version delivers significant improvements in aesthetic quality while maintaining enhanced UI understanding performance. The new model achieves visual appeal comparable to closed-source alternatives, making it ideal for production applications requiring both accuracy and beautiful UI generation.

<div align="center">
  <img src="https://mdn.alipayobjects.com/huamei_v87pyo/afts/img/A*7ZqrR6mlQ2gAAAAAVxAAAAgAepd5AQ/original" alt="UI-UG Model Demo Overview" width="900px">
  <p><em>Figure 1: Overview of UI-UG. The workflow includes 1) Data preparation (UI image collection + element detection + DSL generation); 2) Two-stage training: SFT with VQA dataset, then RL optimization using GRPO and DPO for each task. The model supports UI understanding tasks (referring and grounding) and enables both offline and real-time UI generation.</em></p>
</div>

## 🚀 Core Features

### 🔍 1. UI Description Generation (Referring)
- **Element Description**: Automatically generate element descriptions based on coordinate regions
- **Semantic Understanding**: Understand the function, style, and interaction meaning of UI elements
- **Multi-dimensional Analysis**: Include text, color, clickability, and other attributes

### 📍 2. UI Element Detection (Grounding)
- **Object Detection**: Automatically identify and locate various UI elements in interfaces
- **Classification**: Support for 20+ categories including text, button, icon, image, etc.
- **Coordinate Annotation**: Precisely generate bounding box coordinates for elements

### 🎨 3. UI Code Generation (Generation)
- **DSL Generation**: Generate structured DSL code from requirement descriptions
- **Mock Data**: Automatically generate accompanying mock data
- **Multi-language Support**: Support for generating UI code from Chinese and English descriptions

## 🛠️ Quick Start

### 📋 Environment Setup

```bash
# Create virtual environment
python -m venv uiug-env
source uiug-env/bin/activate  # Windows: uiug-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install render dependencies (optional)
pip install playwright && playwright install
```

### 🔧 Basic Usage

```python
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import smart_resize, process_vision_info
import torch
from PIL import Image
import re

# Configuration
IMAGE_FACTOR = 28
MIN_PIXELS = 64 * 28 * 28
MAX_PIXELS = 1280 * 28 * 28
MAX_TOKENS = 8192

# Load model
model_path = "neovateai/UI-UG-7B"
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_path, torch_dtype=torch.float16, device_map="auto"
)
processor = AutoProcessor.from_pretrained(
    model_path, 
    min_pixels=MIN_PIXELS, 
    max_pixels=MAX_PIXELS
)

def llm_inference(messages):
    """Unified inference function"""
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)
    
    generated_ids = model.generate(
        **inputs, 
        max_new_tokens=MAX_TOKENS, 
        do_sample=False
    )
    
    generated_ids_trimmed = [
        out_ids[len(in_ids):] 
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    
    output_text = processor.batch_decode(
        generated_ids_trimmed, 
        skip_special_tokens=True, 
        clean_up_tokenization_spaces=False
    )
    return output_text[0]

# Load image
image_path = "figures/alipay_demo.png"
original_image = Image.open(image_path)
original_width, original_height = original_image.size

# Calculate resize dimensions
resized_height, resized_width = smart_resize(
    original_height, original_width, IMAGE_FACTOR, MIN_PIXELS, MAX_PIXELS
)
```

### 📊 Task Examples

#### 1️⃣ Referring Task: Describe element by coordinates
```python
# Scale coordinates from original to resized dimensions
def scale_coordinates(original_coords, original_size, resized_size):
    orig_x1, orig_y1, orig_x2, orig_y2 = original_coords
    orig_w, orig_h = original_size
    new_w, new_h = resized_size
    
    scaled_x1 = int(orig_x1 * new_w / orig_w)
    scaled_y1 = int(orig_y1 * new_h / orig_h)
    scaled_x2 = int(orig_x2 * new_w / orig_w)
    scaled_y2 = int(orig_y2 * new_h / orig_h)
    
    return f"({scaled_x1}, {scaled_y1}),({scaled_x2}, {scaled_y2})"

# Example usage
original_coords_str = "(600, 623),(907, 634)"
# Parse original coordinates
coord_match = re.findall(r'\((\d+),\s*(\d+)\)', original_coords_str)
original_coords = [int(coord_match[0][0]), int(coord_match[0][1]), int(coord_match[1][0]), int(coord_match[1][1])]
scaled_coords_str = scale_coordinates(original_coords, (original_width, original_height), (resized_width, resized_height))

referring_messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": image_path},
            {"type": "text", "text": f"Describe the region {scaled_coords_str}"}
        ]
    }
]

referring_result = llm_inference(referring_messages)
print("Referring Result:", referring_result)
```

#### 2️⃣ Grounding Task: Detect element by description
```python
grounding_messages = [
    {
        "role": "user", 
        "content": [
            {"type": "image", "image": image_path},
            {"type": "text", "text": "List all the ui items."}
        ]
    }
]

grounding_result = llm_inference(grounding_messages)

# Extract coordinates from grounding result and rescale them
coord_pattern = r'\((\d+),\s*(\d+)\),\((\d+),\s*(\d+)\)'
matches = re.findall(coord_pattern, grounding_result)
for match in matches:
    scaled_coords = [int(match[0]), int(match[1]), int(match[2]), int(match[3])]
    original_coords_str = scale_coordinates(scaled_coords, (resized_width, resized_height), (original_width, original_height))
    grounding_result = grounding_result.replace(f"({match[0]}, {match[1]}),({match[2]}, {match[3]})", original_coords_str)

print("Grounding Result:", grounding_result)
```

#### 3️⃣ Generation Task: Generate UI from description
```python
generation_messages = [
    {
        "role": "user",
        "content": [
            # {"type": "image", "image": image_path}, # your optional referring image
            {"type": "text", "text": "Generate a login form with email field, password field, and submit button"}
        ]
    }
]

generation_result = llm_inference(generation_messages)
print("Generation Result:", generation_result)
```

## 🚀 vLLM Deployment

### 🎯 Start Model Service

#### Option 1: Quick Start with Script
```bash
bash scripts/vllm_deploy.sh
```

#### Option 2: Manual Command Line
```bash
vllm serve $MODEL_PATH \
  --port 8000 \
  --served-model-name ui_ug \
  --dtype bfloat16 \
  --tensor-parallel-size 1 \
  --max-model-len 8192 \
  --mm_processor_kwargs '{"max_pixels":1003520}' \
  --trust-remote-code
```

### 🎮 Run Demo Tasks

```bash
# Run individual tasks
python -m demo.run_demo --task referring      # UI element referring
python -m demo.run_demo --task grounding      # UI element grounding
python -m demo.run_demo --task generation     # UI code generation

# Run all demo tasks
python -m demo.run_demo --all-tasks

# Custom image testing
python -m demo.run_demo --single \
  --image-url YOUR_URL \
  --prompt "Describe this UI."

# Enable streaming output
python -m demo.run_demo --task generation --stream
```

## 📊 Evaluation

### 🎯 Run Evaluation Tasks

```bash
# UI element referring evaluation
python -m eval.referring_evaluator 

# UI element grounding evaluation
python -m eval.grounding_evaluator 

# UI code generation evaluation
python -m eval.generation_evaluator
```

### 🎨 Render UI DSL

```bash
python -m utils/render_utils
```

## ⚙️ Configuration

### 🔧 Environment Variables

```bash
export MODEL_PATH="/path/to/model"      # Model path
export CUDA_DEVICES="0"                 # GPU device
export API_BASE="http://localhost:8000" # API address
```

### 🎛️ Model Parameters

```python
# Configuration in eval/config.py or demo/config.py
DEFAULT_BATCH_SIZE = 1
MIN_PIXELS = 4 * 28 * 28
MAX_PIXELS = 1280 * 28 * 28

SAMPLING_CONFIG = {
    'temperature': 0.0,
    'repetition_penalty': 1.2,
    'max_tokens': 8192
}
```

## � Performance

### 🎯 Task Specifications

| Task Type | Description | Evaluation Metrics |
|-----------|-------------|-------------------|
| **Referring** | UI element referring generation | JSON format accuracy, Classification accuracy, text similarity, color similarity |
| **Grounding** | UI element detection and localization | JSON format accuracy, mAP, AP50, AP75 |
| **Generation** | UI code generation | JSON format accuracy, LLM-based judgement (following Web2Code) |

<div align="center">
  <img src="https://mdn.alipayobjects.com/huamei_v87pyo/afts/img/A*uqydRLNHAvwAAAAAT2AAAAgAepd5AQ/original" alt="UI-UG Understanding Evaluation" width="900px">
  <p><em>Table 1: Performance comparison of different models on referring and grounding tasks.(UI-UG-7B-2601)</em></p>
</div>

<div align="center">
  <img src="https://mdn.alipayobjects.com/huamei_v87pyo/afts/img/A*eYvnRrt3l2YAAAAASFAAAAgAepd5AQ/original" alt="UI-UG Generation Evaluation" width="500px">
  <p><em>Table 2: Performance comparison of different models on generation tasks.(UI-UG-7B-2601)</em></p>
</div>

<div align="center">
  <img src="https://mdn.alipayobjects.com/huamei_v87pyo/afts/img/A*BDYJRpBDMpQAAAAAgBAAAAgAepd5AQ/original" alt="UI-UG Grounding Vis1" width="900px">
  <img src="https://mdn.alipayobjects.com/huamei_v87pyo/afts/img/A*u6jvT7B63CYAAAAAdkAAAAgAepd5AQ/original" alt="UI-UG Grounding Vis2" width="900px">
  <p><em>Figure 2: Visual comparison of different models for grounding task for complex UIs.(UI-UG-7B-2601)</em></p>
</div>

## 📄 License

This project is licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0) - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

- [**Qwen2.5-VL**](https://github.com/QwenLM/Qwen2.5-VL) - Multimodal foundation model
- [**VLLM**](https://github.com/vllm-project/vllm) - High-performance inference framework
- [**Ant Group**](https://www.antgroup.com) & [**AFX Team**](https://afx-team.github.io) - Technical support and scenario applications

## 📖 Citation

If you find this work useful, please consider citing:

```bibtex
@misc{yang2025uiugunifiedmllmui,
      title={UI-UG: A Unified MLLM for UI Understanding and Generation}, 
      author={Hao Yang and Weijie Qiu and Ru Zhang and Zhou Fang and Ruichao Mao and Xiaoyu Lin and Maji Huang and Zhaosong Huang and Teng Guo and Shuoyang Liu and Hai Rao},
      year={2025},
      eprint={2509.24361},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2509.24361}, 
}
```

---

<div align="center">
  <p><i>Built with ❤️ by <a href="https://afx-team.github.io/">Alipay AFX</a></i></p>
</div>