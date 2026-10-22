# AICTE BluePill — Local Model Vault (`/models`)

This directory houses the localized Large Language Model weights used for assistive statutory scrutiny and conversational analysis.

## Model Details
- **Model**: Qwen 2.5 3B Instruct (`qwen2.5-3b-instruct.gguf`)
- **Format**: GGUF (Quantized Q4_K_M)
- **Size**: ~1.93 GB (1,929,903,008 bytes)
- **Context Length**: 4,096 tokens
- **Architecture**: Transformer Decoder-only with RoPE and SwiGLU activations
- **Target Hardware**: Runs with 100% GPU acceleration (CUDA) or fast CPU inference

## Files in `/models`
1. **`qwen2.5-3b-instruct.gguf`**: The complete quantized weights binary.
2. **`Modelfile`**: Ready-to-use Ollama configuration specifying system prompts and AICTE scrutiny temperature/top_p hyperparameters.

## Serving Locally
### Option 1: Via Ollama (Currently Active)
```powershell
ollama create qwen2.5:3b -f models/Modelfile
```
The FastAPI backend connects to `http://localhost:11434` to invoke this model.

### Option 2: Direct Llama.cpp / Python Llama-CPP
```powershell
.\venv\Scripts\python.exe -m pip install llama-cpp-python
```
```python
from llama_cpp import Llama
llm = Llama(model_path="models/qwen2.5-3b-instruct.gguf", n_ctx=4096)
```
