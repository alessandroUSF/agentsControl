"""One call = one prompt sent to one model, returned as a plain dict.

Every adapter returns the same fields so the runner, the judge and the statistics never care
which provider answered:
  text            the visible answer (reasoning/thinking blocks are not kept)
  stop_reason     provider stop reason, normalized to a string
  provider_block  True when the provider itself blocked the answer (Anthropic stop_reason
                  "refusal", OpenAI refusal content). These are counted separately from
                  refusals the model writes in plain text.
  block_category  provider category for that block, when given (e.g. "cyber", "bio")
  input_tokens, output_tokens, request_id

Keys: each provider reads ONLY its dedicated research key (AC_ANTHROPIC_API_KEY, AC_OPENAI_API_KEY in .env,
from separate research accounts). It never falls back to ANTHROPIC_API_KEY / OPENAI_API_KEY, so a run
can never go out on the author's personal accounts by accident.

Design choices (recorded in the README, Method):
  * Provider defaults: no system prompt, no temperature, default thinking/effort unless the
    config sets "effort". The goal is to measure each model as a user meets it.
  * No server-side refusal fallback on Anthropic models: a fallback would answer with another
    model and hide the refusal we are trying to measure.
"""
import os
import time


RESEARCH_KEYS = {"anthropic": "AC_ANTHROPIC_API_KEY", "openai": "AC_OPENAI_API_KEY"}


def research_key(provider):
    name = RESEARCH_KEYS[provider]
    key = os.environ.get(name, "").strip()
    if not key:
        raise SystemExit(f"{name} is empty in .env: use the key of the separate research account.")
    return key


class Provider:
    def __init__(self, cfg):
        self.cfg = cfg

    def call(self, prompt):
        raise NotImplementedError


class AnthropicProvider(Provider):
    def __init__(self, cfg):
        super().__init__(cfg)
        import anthropic
        self.anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=research_key("anthropic"), max_retries=4, timeout=180.0)

    def call(self, prompt):
        kwargs = dict(model=self.cfg["model"], max_tokens=self.cfg["max_output_tokens"],
                      messages=[{"role": "user", "content": prompt}])
        if self.cfg.get("effort"):
            kwargs["extra_body"] = {"output_config": {"effort": self.cfg["effort"]}}
        r = self.client.messages.create(**kwargs)
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        details = getattr(r, "stop_details", None)
        return {
            "text": text,
            "stop_reason": str(r.stop_reason),
            "provider_block": r.stop_reason == "refusal",
            "block_category": getattr(details, "category", None) if details else None,
            "input_tokens": r.usage.input_tokens,
            "output_tokens": r.usage.output_tokens,
            "request_id": getattr(r, "_request_id", None),
        }


class OpenAIProvider(Provider):
    """OpenAI Responses API (GPT-5.x reasoning models; reasoning tokens are billed as output)."""

    def __init__(self, cfg):
        super().__init__(cfg)
        from openai import OpenAI
        self.client = OpenAI(api_key=research_key("openai"), max_retries=4, timeout=180.0)

    def call(self, prompt):
        kwargs = dict(model=self.cfg["model"], input=prompt,
                      max_output_tokens=self.cfg["max_output_tokens"])
        if self.cfg.get("effort"):
            kwargs["reasoning"] = {"effort": self.cfg["effort"]}
        r = self.client.responses.create(**kwargs)
        refusal = None
        for item in r.output or []:
            for c in getattr(item, "content", None) or []:
                if getattr(c, "type", "") == "refusal":
                    refusal = getattr(c, "refusal", "") or "refusal"
        stop = r.status
        if getattr(r, "incomplete_details", None):
            stop = f"{r.status}:{r.incomplete_details.reason}"
        return {
            "text": r.output_text or (refusal or ""),
            "stop_reason": str(stop),
            "provider_block": refusal is not None,
            "block_category": None,
            "input_tokens": r.usage.input_tokens if r.usage else 0,
            "output_tokens": r.usage.output_tokens if r.usage else 0,
            "request_id": getattr(r, "_request_id", None) or r.id,
        }


class OpenAICompatibleProvider(Provider):
    """Chat Completions on any OpenAI-compatible server: Ollama on the local GPU, OpenRouter, Together..."""

    def __init__(self, cfg):
        super().__init__(cfg)
        from openai import OpenAI
        key_env = cfg.get("api_key_env")
        self.client = OpenAI(base_url=cfg["base_url"], api_key=os.environ.get(key_env, "") if key_env else "local",
                             max_retries=2, timeout=600.0)

    def call(self, prompt):
        r = self.client.chat.completions.create(model=self.cfg["model"], max_tokens=self.cfg["max_output_tokens"],
                                                messages=[{"role": "user", "content": prompt}])
        ch = r.choices[0]
        return {
            "text": ch.message.content or "",
            "stop_reason": str(ch.finish_reason),
            "provider_block": False,
            "block_category": None,
            "input_tokens": r.usage.prompt_tokens if r.usage else 0,
            "output_tokens": r.usage.completion_tokens if r.usage else 0,
            "request_id": r.id,
        }


class OllamaProvider(Provider):
    """Native Ollama API on the local GPU (lets us switch Qwen3 thinking off and fix a seed)."""

    def __init__(self, cfg):
        super().__init__(cfg)
        self.url = cfg.get("base_url", "http://localhost:11434").rstrip("/") + "/api/chat"

    def call(self, prompt):
        import json
        import urllib.request
        body = {"model": self.cfg["model"], "stream": False,
                "messages": [{"role": "user", "content": prompt}],
                "options": {"num_predict": self.cfg["max_output_tokens"], "seed": self.cfg.get("seed", 20261107)}}
        if "think" in self.cfg:
            body["think"] = self.cfg["think"]
        req = urllib.request.Request(self.url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=900) as resp:
            r = json.loads(resp.read().decode("utf-8"))
        return {
            "text": r.get("message", {}).get("content", ""),
            "stop_reason": str(r.get("done_reason")),
            "provider_block": False,
            "block_category": None,
            "input_tokens": r.get("prompt_eval_count", 0),
            "output_tokens": r.get("eval_count", 0),
            "request_id": None,
        }


PROVIDERS = {"anthropic": AnthropicProvider, "openai": OpenAIProvider,
             "openai_compatible": OpenAICompatibleProvider, "ollama": OllamaProvider}

# Commercial APIs never receive the benchmarks' harmful prompts (decision of 07/11/2026: protects the
# accounts and follows the providers' usage policies). Harmful prompts run only on local models.
API_PROVIDERS = {"anthropic", "openai", "openai_compatible"}


def allowed(cfg, row):
    """True when this prompt may be sent to this model."""
    if cfg["provider"] not in API_PROVIDERS:
        return True
    return row["expected"] == "comply" or row["source"] == "own"


def make(cfg):
    return PROVIDERS[cfg["provider"]](cfg)


def timed_call(provider, prompt):
    t0 = time.perf_counter()
    out = provider.call(prompt)
    out["latency_s"] = round(time.perf_counter() - t0, 2)
    return out
