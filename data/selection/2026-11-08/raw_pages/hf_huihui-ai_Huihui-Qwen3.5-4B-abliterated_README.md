---
library_name: transformers
license: apache-2.0
license_link: https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/LICENSE
pipeline_tag: image-text-to-text
base_model:
- Qwen/Qwen3.5-4B
tags:
- abliterated
- uncensored
---

# huihui-ai/Huihui-Qwen3.5-4B-abliterated

This is the uncensored version of [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) after fine-tuning.  It has been trained using [TRL](https://github.com/huggingface/trl).

The fine-tuned dataset is a type of dataset that operates in a non-think mode, and it may actually make thinking simpler.

It was only the text part that was processed, not the image part.

After saving the model, the names of some weights have changed, and it no longer contains MTP weights. However, both ollama and llama.cpp can still be used for conversion.

## ollama

Please use the latest version of [ollama v0.17.7](https://github.com/ollama/ollama/releases/tag/v0.17.7)

You can use [huihui_ai/qwen3.5-abliterated:4b](https://ollama.com/huihui_ai/qwen3.5-abliterated:4b) directly, 
```
ollama run huihui_ai/qwen3.5-abliterated:4b
```


### Usage Warnings


 - **Risk of Sensitive or Controversial Outputs**: This model’s safety filtering has been significantly reduced, potentially generating sensitive, controversial, or inappropriate content. Users should exercise caution and rigorously review generated outputs.

 - **Not Suitable for All Audiences**: Due to limited content filtering, the model’s outputs may be inappropriate for public settings, underage users, or applications requiring high security.

 - **Legal and Ethical Responsibilities**: Users must ensure their usage complies with local laws and ethical standards. Generated content may carry legal or ethical risks, and users are solely responsible for any consequences.

 - **Research and Experimental Use**: It is recommended to use this model for research, testing, or controlled environments, avoiding direct use in production or public-facing commercial applications.

 - **Monitoring and Review Recommendations**: Users are strongly advised to monitor model outputs in real-time and conduct manual reviews when necessary to prevent the dissemination of inappropriate content.

 - **No Default Safety Guarantees**: Unlike standard models, this model has not undergone rigorous safety optimization. huihui.ai bears no responsibility for any consequences arising from its use.


### Donation
##### Your donation helps us continue our further development and improvement, a cup of coffee can do it.
- bitcoin:
```
  bc1qqnkhuchxw0zqjh2ku3lu4hq45hc6gy84uk70ge
```
- Support our work on [Ko-fi](https://ko-fi.com/huihuiai)!

