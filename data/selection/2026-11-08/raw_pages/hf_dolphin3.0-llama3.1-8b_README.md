---
license: llama3.1
datasets:
- OpenCoder-LLM/opc-sft-stage1
- OpenCoder-LLM/opc-sft-stage2
- microsoft/orca-agentinstruct-1M-v1
- microsoft/orca-math-word-problems-200k
- NousResearch/hermes-function-calling-v1
- AI-MO/NuminaMath-CoT
- AI-MO/NuminaMath-TIR
- allenai/tulu-3-sft-mixture
- cognitivecomputations/dolphin-coder
- HuggingFaceTB/smoltalk
- cognitivecomputations/samantha-data
- m-a-p/CodeFeedback-Filtered-Instruction
- m-a-p/Code-Feedback
language:
- en
base_model:
- meta-llama/Llama-3.1-8B
model-index:
- name: Dolphin3.0-Llama3.1-8B
  results:
  - task:
      type: text-generation
      name: Text Generation
    dataset:
      name: IFEval (0-Shot)
      type: wis-k/instruction-following-eval
      split: train
      args:
        num_few_shot: 0
    metrics:
    - type: inst_level_strict_acc and prompt_level_strict_acc
      value: 76.21
      name: averaged accuracy
    source:
      url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard#/?search=cognitivecomputations%2FDolphin3.0-Llama3.1-8B
      name: Open LLM Leaderboard
  - task:
      type: text-generation
      name: Text Generation
    dataset:
      name: BBH (3-Shot)
      type: SaylorTwift/bbh
      split: test
      args:
        num_few_shot: 3
    metrics:
    - type: acc_norm
      value: 27.63
      name: normalized accuracy
    source:
      url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard#/?search=cognitivecomputations%2FDolphin3.0-Llama3.1-8B
      name: Open LLM Leaderboard
  - task:
      type: text-generation
      name: Text Generation
    dataset:
      name: MATH Lvl 5 (4-Shot)
      type: lighteval/MATH-Hard
      split: test
      args:
        num_few_shot: 4
    metrics:
    - type: exact_match
      value: 10.5
      name: exact match
    source:
      url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard#/?search=cognitivecomputations%2FDolphin3.0-Llama3.1-8B
      name: Open LLM Leaderboard
  - task:
      type: text-generation
      name: Text Generation
    dataset:
      name: GPQA (0-shot)
      type: Idavidrein/gpqa
      split: train
      args:
        num_few_shot: 0
    metrics:
    - type: acc_norm
      value: 4.36
      name: acc_norm
    source:
      url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard#/?search=cognitivecomputations%2FDolphin3.0-Llama3.1-8B
      name: Open LLM Leaderboard
  - task:
      type: text-generation
      name: Text Generation
    dataset:
      name: MuSR (0-shot)
      type: TAUR-Lab/MuSR
      args:
        num_few_shot: 0
    metrics:
    - type: acc_norm
      value: 8.97
      name: acc_norm
    source:
      url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard#/?search=cognitivecomputations%2FDolphin3.0-Llama3.1-8B
      name: Open LLM Leaderboard
  - task:
      type: text-generation
      name: Text Generation
    dataset:
      name: MMLU-PRO (5-shot)
      type: TIGER-Lab/MMLU-Pro
      config: main
      split: test
      args:
        num_few_shot: 5
    metrics:
    - type: acc
      value: 22.13
      name: accuracy
    source:
      url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard#/?search=cognitivecomputations%2FDolphin3.0-Llama3.1-8B
      name: Open LLM Leaderboard
---

# Dolphin 3.0 Llama 3.1 8B 🐬
Part of the [Dolphin 3.0 Collection](https://huggingface.co/collections/cognitivecomputations/dolphin-30-677ab47f73d7ff66743979a3)

Curated and trained by [Eric Hartford](https://huggingface.co/ehartford), [Ben Gitter](https://huggingface.co/bigstorm), [BlouseJury](https://huggingface.co/BlouseJury) and [Cognitive Computations](https://huggingface.co/cognitivecomputations)

[![Discord](https://img.shields.io/discord/1156064224225808488?logo=Discord&logoColor=%23ffffff&label=Discord&link=https%3A%2F%2Fdiscord.gg%2FtCMkMDDHwm)](https://discord.gg/cognitivecomputations)
Discord: https://discord.gg/cognitivecomputations

<img src="https://cdn-uploads.huggingface.co/production/uploads/63111b2d88942700629f5771/cNCs1TBD3FelWCJGkZ3cd.png" width="600" />

## Sponsors
Our appreciation for the generous sponsors of Dolphin 3.0:
- [Crusoe Cloud](https://crusoe.ai/) - provided 16x L40s for training and evals
- [Akash](https://akash.network/) - provided on-demand 8x H100 for training
- [Lazarus](https://www.lazarusai.com/) - provided 16x H100 for training
- [Cerebras](https://cerebras.ai/) - provided excellent and fast inference services for data labeling
- [Andreessen Horowitz](https://a16z.com/) - provided a [grant](https://a16z.com/supporting-the-open-source-ai-community/) that make Dolphin 1.0 possible and enabled me to bootstrap my homelab

## What is Dolphin?

Dolphin 3.0 is the next generation of the Dolphin series of instruct-tuned models.  Designed to be the ultimate general purpose local model, enabling coding, math, agentic, function calling, and general use cases.

Dolphin aims to be a general purpose model, similar to the models behind ChatGPT, Claude, Gemini.  But these models present problems for businesses seeking to include AI in their products.
1) They maintain control of the system prompt, deprecating and changing things as they wish, often causing software to break.
2) They maintain control of the model versions, sometimes changing things silently, or deprecating older models that your business relies on.
3) They maintain control of the alignment, and in particular the alignment is one-size-fits all, not tailored to the application.
4) They can see all your queries and they can potentially use that data in ways you wouldn't want.
Dolphin, in contrast, is steerable and gives control to the system owner. You set the system prompt.  You decide the alignment.  You have control of your data.  Dolphin does not impose its ethics or guidelines on you.  You are the one who decides the guidelines.

Dolphin belongs to YOU, it is your tool, an extension of your will.
Just as you are personally responsible for what you do with a knife, gun, fire, car, or the internet, you are the creator and originator of any content you generate with Dolphin.

https://erichartford.com/uncensored-models

## Chat Template

We use ChatML for the chat template.

```
<|im_start|>system
You are Dolphin, a helpful AI assistant.<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
```

## System Prompt

In Dolphin, the system prompt is what you use to set the tone and alignment of the responses.  You can set a character, a mood, rules for its behavior, and it will try its best to follow them.

Make sure to set the system prompt in order to set the tone and guidelines for the responses - Otherwise, it will act in a default way that might not be what you want.

Example use of system prompt:

```
<|im_start|>system
You are Dolphin, a golang coding assistant.  you only code in golang.  If the user requests any other programming language, return the solution in golang instead.<|im_end|>
<|im_start|>user
Please implement A* using python<|im_end|>
<|im_start|>assistant
```

## Sample Outputs

<img src="https://cdn-uploads.huggingface.co/production/uploads/63111b2d88942700629f5771/C-r1X13UBjnUUNb0q2JLV.png" width="600" />
<img src="https://cdn-uploads.huggingface.co/production/uploads/63111b2d88942700629f5771/4l3KAZiKej2ON7i35PsOa.png" width="600" />
<img src="https://cdn-uploads.huggingface.co/production/uploads/63111b2d88942700629f5771/1ZalmR66LnwhEQQEFttlu.png" width="600" />

## How to use

There are many ways to use a huggingface model including:
- ollama
- LM Studio
- Huggingface Transformers library
- vllm
- sglang
- tgi

### ollama
- [Install ollama](https://ollama.com/download)
- ```ollama run hf.co/cognitivecomputations/Dolphin3.0-Llama3.1-8B-GGUF:Q4_0```
- ```/set system <your system prompt>```

## Evals

TBD

## Appreciation

Respect and thanks to the creators of the open source datasets that were used:
- [OpenCoder-LLM](https://huggingface.co/OpenCoder-LLM) (opc-sft-stage1, opc-sft-stage2)
- [microsoft](https://huggingface.co/OpenCoder-LLM) (orca-agentinstruct-1M-v1, orca-math-word-problems-200k)
- [NousResearch](https://huggingface.co/NousResearch) (hermes-function-calling-v1)
- [AI-MO](https://huggingface.co/AI-MO) (NuminaMath-CoT, NuminaMath-TIR)
- [allenai](https://huggingface.co/allenai) (tulu-3-sft-mixture)
- [HuggingFaceTB](https://huggingface.co/HuggingFaceTB) (smoltalk)
- [m-a-p](https://huggingface.co/m-a-p) (CodeFeedback-Filtered-Instruction, Code-Feedback)

Special thanks to 
- Meta, Qwen, and OpenCoder, who wrote papers and published models that were instrumental in creating Dolphin 3.0.
- [RLHFlow](https://huggingface.co/RLHFlow) for the excellent reward model used to filter the datasets
- Deepseek, for the ridiculously fast Deepseek-V3 that we used to augment the data.



# [Open LLM Leaderboard Evaluation Results](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard)
Detailed results can be found [here](https://huggingface.co/datasets/open-llm-leaderboard/cognitivecomputations__Dolphin3.0-Llama3.1-8B-details)!
Summarized results can be found [here](https://huggingface.co/datasets/open-llm-leaderboard/contents/viewer/default/train?q=cognitivecomputations%2FDolphin3.0-Llama3.1-8B&sort[column]=Average%20%E2%AC%86%EF%B8%8F&sort[direction]=desc)!

|      Metric       |Value (%)|
|-------------------|--------:|
|**Average**        |    24.97|
|IFEval (0-Shot)    |    76.21|
|BBH (3-Shot)       |    27.63|
|MATH Lvl 5 (4-Shot)|    10.50|
|GPQA (0-shot)      |     4.36|
|MuSR (0-shot)      |     8.97|
|MMLU-PRO (5-shot)  |    22.13|

