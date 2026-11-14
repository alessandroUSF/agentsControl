"""One call = one request to one model, returned as a plain dict.

Every adapter returns the same fields, so the runner, the judges and the statistics never care
which provider answered:
  text            the visible answer (reasoning/thinking blocks are not kept; for Ollama, a reasoning block written at
                  the start of the output is split off by split_inband_reasoning, decision D22)
  inband_reasoning, inband_reasoning_chars
                  Ollama only: that block (private records only) and its length, 0 when there was none
  stop_reason     provider stop reason, normalized to a string
  provider_block  True when the provider itself blocked the answer (Anthropic stop_reason
                  "refusal", OpenAI refusal content, content-filter finish reasons). Counted
                  separately from refusals the model writes in plain text.
  block_category  provider category for that block, when given
  served_provider the host that actually served the call (OpenRouter), else the provider name
  input_tokens, output_tokens, reasoning_tokens, request_id

A request is either a prompt string (one user turn) or a list of {"role", "content"} messages
(used for the in-context judge presentation, protocol v2.2 Section 8.3). A "system" message is sent
as Anthropic's top-level system parameter, as a system item on the OpenAI Responses API, and as a
system message elsewhere. The Gemini API (decision D2) takes it as systemInstruction and the assistant turn as
role "model".

Keys (protocol v2.2, Section 10): every remote call uses a dedicated project key whose
environment variable starts with "AC_". A remote model without such a key fails before any
request is made; there is no fallback to any other key. OpenAI calls set store=False.

Blocks (Section 5.2): a moderation rejection is returned as provider_block (never retried). Any other
400/403 without a parameter-error signature raises SuspectedBlock, which the runner records as
provider_block_suspected on refuse-expected prompts (classified by hand after the pilot). Raw 4xx
bodies are kept in the raw record only (error_body, at most 2,000 characters; they can quote the
input); the published call log keeps their SHA-256. A response that comes back but cannot be parsed
raises ResponseParseError (the call may have been billed).

Respondent settings (Section 6.3): provider defaults, no system prompt. Judge settings (Section 8.3)
come from the judge config: temperature, seed, reasoning effort, explicit sampling options.
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

RESEARCH_KEYS = {"anthropic": "AC_ANTHROPIC_API_KEY", "openai": "AC_OPENAI_API_KEY", "google": "AC_GOOGLE_API_KEY"}
LOCAL_HOSTS = ("http://localhost", "http://127.0.0.1", "http://[::1]")     # kept for reference; see is_local_url
LOCAL_HOSTNAMES = ("localhost", "127.0.0.1", "::1")


class ProjectKeyError(RuntimeError):
    pass


def key_from_env(name):
    if not name or not name.startswith("AC_"):
        raise ProjectKeyError(f"remote calls need a dedicated project key named AC_*; got {name!r}")
    key = os.environ.get(name, "").strip()
    if not key:
        raise ProjectKeyError(f"{name} is empty in .env")
    return key


# ---- reasoning written into the output (decision D22, 13 November 2026) ---------------------------------------------
# Some local models write their reasoning into the output itself, even with thinking switched off: model 17 always,
# model 16 now and then (its template opens the block, so only the closing tag appears). Reasoning is not part of the
# answer or of the verdict (Section 2.2), as for the API models whose reasoning comes back apart. The block is split
# off before the screen, the judges and the verdict parser; the raw block is kept in the private record.
THINK_OPEN, THINK_CLOSE = "<think>", "</think>"
INBAND_REASONING_RULE_VERSION = "2026-11-13"


def split_inband_reasoning(text):
    """(visible, block) of an output. The block is what precedes the first closing tag when the output opens with
    the opening tag, or when no opening tag comes before that closing tag (the template opened the block); the visible
    part is what follows it, without leading whitespace. An output that opens with the opening tag and never closes
    it was cut off inside its reasoning: its visible part is empty. Any other output is returned unchanged, with no
    block."""
    if not text:
        return text, None
    s = text.lstrip()
    close = s.find(THINK_CLOSE)
    if s.startswith(THINK_OPEN):
        if close < 0:
            return "", s
    elif close < 0 or THINK_OPEN in s[:close]:
        return text, None
    end = close + len(THINK_CLOSE)
    return s[end:].lstrip(), s[:end]


def is_local_url(url):
    """True only for plain http on an exact loopback host, with no user information (review round 18, M1: the
    earlier prefix test accepted lookalike hosts such as http://localhost.example.org)."""
    try:
        u = urllib.parse.urlsplit(str(url or ""))
        u.port                                   # raises ValueError on a malformed port
    except ValueError:
        return False
    return u.scheme == "http" and u.hostname in LOCAL_HOSTNAMES and u.username is None and u.password is None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect from the local server is an error: nothing follows it to another host."""

    def redirect_request(self, *args, **kwargs):
        return None


# Calls to the local server use no proxy (environment or system settings) and follow no redirect.
LOCAL_OPEN = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect()).open   # test seam


def local_urlopen(req, timeout):
    """Open a request on the local Ollama server only: exact loopback host, no proxy, no redirect."""
    url = req.full_url if isinstance(req, urllib.request.Request) else req
    if not is_local_url(url):
        raise ProjectKeyError("the local server must be http on localhost, 127.0.0.1 or [::1]")
    return LOCAL_OPEN(req, timeout=timeout)


def is_remote(cfg):
    if cfg["provider"] in ("anthropic", "openai", "google"):
        return True
    if cfg["provider"] == "ollama":
        return not is_local_url(cfg.get("base_url", "http://localhost:11434"))
    return not is_local_url(cfg.get("base_url", ""))


# Strong markers are error codes that only moderation produces; they win over parameter-error markers.
# Weak markers are phrases that also occur in other errors ("invalid value for model: omni-moderation-...",
# "request was flagged by rate limit"); a parameter-error marker beats them (B5-m3).
STRONG_MODERATION_MARKERS = ("flagged_input", "invalid_prompt", "content_policy", "content_filter",
                             "data_inspection_failed", "prohibited_content")
WEAK_MODERATION_MARKERS = ("moderation", "content policy", "content management policy", "safety system",
                           "content exists risk", "inappropriate content", "sensitive content", "blocked by safety")
MODERATION_MARKERS = STRONG_MODERATION_MARKERS + WEAK_MODERATION_MARKERS
# Markers that are too short or too common as bare substrings (B4-m1): matched as fields or whole words only.
STRONG_MODERATION_PATTERNS = (re.compile(r'"code"\s*:\s*"?1301"?(?![0-9])'),   # Zhipu sensitive-content code
                              re.compile(r'"flagged"\s*:\s*true'))
WEAK_MODERATION_PATTERNS = (re.compile(r"\bwas flagged\b"),)
MODERATION_PATTERNS = STRONG_MODERATION_PATTERNS + WEAK_MODERATION_PATTERNS
# The last five occur in the Gemini API's errors for a malformed request or a missing precondition (decision D2).
# Its generateContent method reports blocks inside a normal response, so these name our request or our account,
# never the content of a prompt.
PARAM_ERROR_MARKERS = ("max_tokens", "max_output_tokens", "temperature", "top_p", "parameter", "unsupported",
                       "not supported", "invalid value", "model_not_found", "does not exist", "context length",
                       "context_length", "maximum context", "too long", "rate limit", "quota", "billing",
                       "authentication", "api key", "permission",
                       "invalid json payload", "unknown name", "cannot find field", "invalid_argument",
                       "failed_precondition")
NATIVE_BLOCK_REASONS = {"content_filter", "safety", "prohibited_content", "blocklist", "spii", "refusal",
                        "image_safety", "recitation"}


class PreSendError(RuntimeError):
    """Raised by this module's own checks before any request is sent; settled at zero."""


class HTTPStatusError(RuntimeError):
    """An HTTP error of a plain urllib call (the Ollama adapter), with its status and body."""

    def __init__(self, status, body):
        super().__init__(f"HTTP {status}")
        self.status_code, self.body = status, body


class ResponseParseError(RuntimeError):
    """The request was sent and a response came back, but it could not be parsed (B4-m2).
    The runner settles it at the reserved amount, because the call may have been billed."""


class AccountRestricted(RuntimeError):
    """The provider says that the study's account is limited or disabled (Section 16.5). This is not an outcome of
    the request. It has no HTTP status, so the runners treat it as a failure that does not depend on the request
    (retried, then pending; five pending calls in a row stop the model) and settle it at the reserved amount."""


def moderation_marker(msg, strength="any"):
    """The moderation marker found in a lower-cased error body, or None. strength: 'strong', 'weak' or 'any'."""
    markers = {"strong": STRONG_MODERATION_MARKERS, "weak": WEAK_MODERATION_MARKERS}.get(strength, MODERATION_MARKERS)
    patterns = {"strong": STRONG_MODERATION_PATTERNS, "weak": WEAK_MODERATION_PATTERNS}.get(strength,
                                                                                             MODERATION_PATTERNS)
    for m in markers:
        if m in msg:
            return m
    for p in patterns:
        if p.search(msg):
            return p.pattern
    return None


class SuspectedBlock(RuntimeError):
    """A 400/403 that matches neither a moderation marker nor a parameter-error signature."""

    def __init__(self, status, body):
        super().__init__(f"suspected provider block ({status})")
        self.status, self.body = status, body


def error_text(exc):
    msg = str(getattr(exc, "message", "") or exc)
    body = getattr(exc, "body", None)
    if body:
        msg += " " + json.dumps(body, default=str)
    return msg[:2000]


def classify_rejection(status, raw):
    """Block record, SuspectedBlock, or None for a provider rejection with this status and raw body."""
    msg = (raw or "").lower()
    marker = None
    if status in (400, 403):
        param = any(m in msg for m in PARAM_ERROR_MARKERS)
        marker = moderation_marker(msg, "strong") or (None if param else moderation_marker(msg, "weak"))
    if marker:
        return {"text": "", "stop_reason": f"moderation_block:{status}", "provider_block": True, "block_marker": marker,
                "block_category": "router_or_provider_moderation", "served_provider": None,
                "model_returned": None, "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": None,
                "cost_reported": None, "request_id": None, "error_body": (raw or "")[:2000]}
    if status in (400, 403) and not any(m in msg for m in PARAM_ERROR_MARKERS):
        raise SuspectedBlock(status, (raw or "")[:2000])
    return None


def moderation_block(exc):
    """A provider- or router-side moderation rejection, returned as a block record.

    Router moderation (OpenRouter 403) and provider prompt rejections (OpenAI 400
    invalid_prompt) are outcomes, not transport errors: they are recorded as
    provider_block and never retried automatically (protocol v2.2, Section 5.2).
    Returns None when the exception is not a moderation rejection.
    """
    try:
        return classify_rejection(getattr(exc, "status_code", None), error_text(exc))
    except SuspectedBlock as sb:
        raise sb from exc


def split_system(messages):
    """(system text or None, the other messages) for APIs with a top-level system parameter."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system") or None
    return system, [m for m in messages if m["role"] != "system"]


def as_messages(request):
    if isinstance(request, str):
        return [{"role": "user", "content": request}]
    return list(request)


class Provider:
    def __init__(self, cfg):
        self.cfg = cfg

    def call(self, request):
        raise NotImplementedError


class AnthropicProvider(Provider):
    def __init__(self, cfg):
        super().__init__(cfg)
        import anthropic
        self.client = anthropic.Anthropic(api_key=key_from_env(RESEARCH_KEYS["anthropic"]),
                                          max_retries=0, timeout=900.0)

    def params(self, request):
        system, msgs = split_system(as_messages(request))
        kwargs = dict(model=self.cfg["model"], max_tokens=self.cfg["max_output_tokens"], messages=msgs)
        if system:   # cached prefix: the judge rubric (Section 11 budget assumes it); harmless when too short to cache
            kwargs["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        if self.cfg.get("temperature") is not None:
            kwargs["temperature"] = self.cfg["temperature"]
        if self.cfg.get("effort"):
            kwargs["output_config"] = {"effort": self.cfg["effort"]}
        return kwargs

    def call(self, request):
        kwargs = self.params(request)
        if "output_config" in kwargs:
            kwargs["extra_body"] = {"output_config": kwargs.pop("output_config")}
        try:
            r = self.client.messages.create(**kwargs)
        except Exception as e:
            block = moderation_block(e)
            if block is None:
                raise
            return dict(block, served_provider="anthropic")
        try:
            return self.parse(r)
        except Exception as e:
            raise ResponseParseError(f"{type(e).__name__}: {e}") from e

    # Message Batches (50% price; Section 6.3). Batch results are deleted after retrieval (Section 10).
    def batch_submit(self, items):
        """items: list of (custom_id, request). Returns the batch id."""
        reqs = [{"custom_id": cid, "params": self.params(req)} for cid, req in items]
        return self.client.messages.batches.create(requests=reqs).id

    def batch_status(self, batch_id):
        b = self.client.messages.batches.retrieve(batch_id)
        return b.processing_status == "ended", str(b.processing_status)

    def batch_request_count(self, batch_id):
        rc = self.client.messages.batches.retrieve(batch_id).request_counts
        return sum(getattr(rc, k, 0) or 0 for k in ("processing", "succeeded", "errored", "canceled", "expired"))

    def batch_results(self, batch_id):
        """Yields (custom_id, record or None, error text or None); raises SuspectedBlock per item via the record."""
        for res in self.client.messages.batches.results(batch_id):
            kind = res.result.type
            if kind == "succeeded":
                try:                                # per item (B5-M5): one bad item never stops the collect
                    rec = self.parse(res.result.message)
                except Exception as e:
                    yield res.custom_id, None, ("parse_error", type(e).__name__)
                    continue
                yield res.custom_id, rec, None
            elif kind == "errored":
                err = res.result.error
                raw = json.dumps(err.model_dump() if hasattr(err, "model_dump") else str(err), default=str)
                status = 400 if "invalid_request" in raw else 500
                yield res.custom_id, None, (status, raw)
            else:                                   # canceled, expired: not billed, run again later
                yield res.custom_id, None, (None, f"batch_result:{kind}")

    def batch_delete(self, batch_id):
        try:
            self.client.messages.batches.delete(batch_id)
        except Exception as e:                      # already deleted counts as deleted (idempotent, B6-M4)
            if getattr(e, "status_code", None) != 404:
                raise
        return [batch_id]

    def batch_cancel(self, batch_id):
        self.client.messages.batches.cancel(batch_id)

    def batch_errors(self, batch_id):
        return None

    def parse(self, r):
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        details = getattr(r, "stop_details", None)
        return {
            "text": text,
            "stop_reason": str(r.stop_reason),
            "provider_block": r.stop_reason == "refusal",
            "block_category": getattr(details, "category", None) if details else None,
            "served_provider": "anthropic",
            "model_returned": getattr(r, "model", None),
            "input_tokens": r.usage.input_tokens + (getattr(r.usage, "cache_read_input_tokens", 0) or 0)
            + (getattr(r.usage, "cache_creation_input_tokens", 0) or 0),
            "cache_read_tokens": getattr(r.usage, "cache_read_input_tokens", None),
            "cache_write_tokens": getattr(r.usage, "cache_creation_input_tokens", None),
            "output_tokens": r.usage.output_tokens,
            "reasoning_tokens": None,
            "cost_reported": None,
            "request_id": getattr(r, "_request_id", None),
        }


class OpenAIProvider(Provider):
    """OpenAI Responses API (reasoning tokens are billed as output)."""

    def __init__(self, cfg):
        super().__init__(cfg)
        from openai import OpenAI
        self.client = OpenAI(api_key=key_from_env(RESEARCH_KEYS["openai"]), max_retries=0, timeout=900.0)

    def params(self, request):
        kwargs = dict(model=self.cfg["model"], input=as_messages(request),
                      max_output_tokens=self.cfg["max_output_tokens"], store=False)
        if self.cfg.get("effort"):
            kwargs["reasoning"] = {"effort": self.cfg["effort"]}
        return kwargs

    def call(self, request):
        try:
            r = self.client.responses.create(**self.params(request))
        except Exception as e:
            block = moderation_block(e)
            if block is None:
                raise
            return dict(block, served_provider="openai")
        try:
            return self.parse(r)
        except Exception as e:
            raise ResponseParseError(f"{type(e).__name__}: {e}") from e

    # Batch API (50% price). The input, output and error files are deleted after retrieval (Section 10).
    def batch_submit(self, items):
        import io
        lines = [json.dumps({"custom_id": cid, "method": "POST", "url": "/v1/responses", "body": self.params(req)},
                            ensure_ascii=False) for cid, req in items]
        f = self.client.files.create(file=("batch.jsonl", io.BytesIO(("\n".join(lines) + "\n").encode("utf-8"))),
                                     purpose="batch")
        try:
            b = self.client.batches.create(input_file_id=f.id, endpoint="/v1/responses", completion_window="24h")
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status is not None and 400 <= int(status) < 500:     # rejected: no batch exists, delete the upload
                try:
                    self.client.files.delete(f.id)
                except Exception:
                    pass
            else:                                   # a batch may exist (B6-M4): keep the upload; --release deletes it
                e.uploaded_file_id = f.id
            raise
        return b.id

    def batch_status(self, batch_id):
        b = self.client.batches.retrieve(batch_id)
        return b.status in ("completed", "failed", "expired", "cancelled"), str(b.status)

    def batch_request_count(self, batch_id):
        rc = getattr(self.client.batches.retrieve(batch_id), "request_counts", None)
        return getattr(rc, "total", None) if rc else None

    def batch_results(self, batch_id):
        from openai.types.responses import Response
        b = self.client.batches.retrieve(batch_id)
        for fid in (b.output_file_id, b.error_file_id):
            if not fid:
                continue
            for line in self.client.files.content(fid).text.splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    yield None, None, ("parse_error", "unreadable_line")
                    continue
                resp = row.get("response") or {}
                if resp.get("status_code") == 200:
                    try:                            # per item (B5-M5)
                        rec = self.parse(Response.model_validate(resp["body"]))
                    except Exception as e:
                        yield row.get("custom_id"), None, ("parse_error", type(e).__name__)
                        continue
                    yield row.get("custom_id"), rec, None
                else:                               # error-file lines may lack a custom_id (C7-M3)
                    raw = json.dumps(resp.get("body") or row.get("error"), default=str)
                    yield row.get("custom_id"), None, (resp.get("status_code"), raw)

    def batch_cancel(self, batch_id):
        self.client.batches.cancel(batch_id)

    def batch_errors(self, batch_id):
        """Batch-level errors (for example a failed validation), as JSON text, or None."""
        errs = getattr(self.client.batches.retrieve(batch_id), "errors", None)
        if not errs:
            return None
        return json.dumps(errs.model_dump() if hasattr(errs, "model_dump") else errs, default=str)[:2000]

    def batch_delete(self, batch_id):
        """Output, error, then input file (the answers first); a file already gone counts as deleted, so a
        retry after a partial failure completes the deletion (idempotent, B6-M4)."""
        b = self.client.batches.retrieve(batch_id)
        deleted = []
        for fid in (b.output_file_id, b.error_file_id, b.input_file_id):
            if fid:
                self.delete_upload(fid)
                deleted.append(fid)
        return deleted

    def delete_upload(self, file_id):
        try:
            self.client.files.delete(file_id)
        except Exception as e:
            if getattr(e, "status_code", None) != 404:
                raise

    def parse(self, r):
        refusal = None
        for item in r.output or []:
            for c in getattr(item, "content", None) or []:
                if getattr(c, "type", "") == "refusal":
                    refusal = getattr(c, "refusal", "") or "refusal"
        stop = r.status
        filtered = False
        if getattr(r, "incomplete_details", None):
            stop = f"{r.status}:{r.incomplete_details.reason}"
            filtered = r.incomplete_details.reason == "content_filter"
        details = getattr(r.usage, "output_tokens_details", None) if r.usage else None
        return {
            "text": r.output_text or (refusal or ""),
            "stop_reason": str(stop),
            "provider_block": refusal is not None or filtered,
            "block_category": "content_filter" if filtered else None,
            "served_provider": "openai",
            "model_returned": getattr(r, "model", None),
            "input_tokens": r.usage.input_tokens if r.usage else 0,
            "cache_read_tokens": getattr(getattr(r.usage, "input_tokens_details", None), "cached_tokens", None)
            if r.usage else None,
            "output_tokens": r.usage.output_tokens if r.usage else 0,
            "reasoning_tokens": getattr(details, "reasoning_tokens", None) if details else None,
            "cost_reported": None,
            "request_id": getattr(r, "_request_id", None) or r.id,
        }


class OpenAICompatibleProvider(Provider):
    """Chat Completions on an OpenAI-compatible server (OpenRouter for all routed API models)."""

    def __init__(self, cfg):
        super().__init__(cfg)
        from openai import OpenAI
        remote = is_remote(cfg)
        key = key_from_env(cfg.get("api_key_env")) if remote else "local"
        self.client = OpenAI(base_url=cfg["base_url"], api_key=key, max_retries=0, timeout=900.0)
        self.openrouter = "openrouter.ai" in cfg["base_url"]

    def extra_body(self):
        extra = {}
        if self.openrouter:
            prov = {"data_collection": "deny", "allow_fallbacks": bool(self.cfg.get("allow_fallbacks", False))}
            if self.cfg.get("provider_order"):
                prov["order"] = self.cfg["provider_order"]
                if not prov["allow_fallbacks"]:          # decision D16: the pinned endpoint is the only one allowed
                    prov["only"] = list(self.cfg["provider_order"][:1])
            if self.cfg.get("zdr", True):
                prov["zdr"] = True
            extra["provider"] = prov
            extra["usage"] = {"include": True}
        if self.cfg.get("effort"):
            extra["reasoning"] = {"effort": self.cfg["effort"]}
        if self.cfg.get("seed") is not None:
            extra["seed"] = self.cfg["seed"]
        return extra

    def call(self, request):
        kwargs = dict(model=self.cfg["model"], max_tokens=self.cfg["max_output_tokens"],
                      messages=as_messages(request), extra_body=self.extra_body())
        if self.cfg.get("temperature") is not None:
            kwargs["temperature"] = self.cfg["temperature"]
        try:
            r = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            block = moderation_block(e)
            if block is None:
                raise
            return dict(block, served_provider=self.cfg["base_url"])
        try:
            return self.parse(r)
        except Exception as e:
            raise ResponseParseError(f"{type(e).__name__}: {e}") from e

    def parse(self, r):
        ch = r.choices[0]
        extra = getattr(r, "model_extra", None) or {}
        details = getattr(r.usage, "completion_tokens_details", None) if r.usage else None
        finish = str(ch.finish_reason)
        native = str((getattr(ch, "model_extra", None) or {}).get("native_finish_reason") or "")
        blocked = finish == "content_filter" or native.lower() in NATIVE_BLOCK_REASONS
        return {
            "text": ch.message.content or "",
            "stop_reason": finish,
            "native_finish_reason": native or None,
            "provider_block": blocked,
            "block_category": (native or finish) if blocked else None,
            "served_provider": extra.get("provider") or self.cfg["base_url"],
            "model_returned": getattr(r, "model", None),
            "input_tokens": r.usage.prompt_tokens if r.usage else 0,
            "output_tokens": r.usage.completion_tokens if r.usage else 0,
            "reasoning_tokens": getattr(details, "reasoning_tokens", None) if details else None,
            "cost_reported": (getattr(r.usage, "model_extra", None) or {}).get("cost") if r.usage else None,
            "request_id": r.id,
        }


class GoogleProvider(Provider):
    """Gemini API (generateContent), called directly with the study's own key (decision D2, 11 November 2026).

    Request. No safetySettings are sent: the adjustable filters keep the API's default, which Google documents as
    off for Gemini 2.5 and later models; protections that cannot be adjusted still apply. The reasoning effort is
    sent as thinkingConfig.thinkingLevel; temperature and seed are sent when set (Google documents that its models
    from Gemini 3.6 Flash on ignore the temperature). 'service_tier' is sent only when the config sets it.

    Response (values documented on 11 November 2026). Thought parts are not kept in the text. Thinking tokens are
    billed as output, so output_tokens counts them with the visible answer. A prompt that Google blocks
    (promptFeedback.blockReason) and an answer stopped by a filter (finishReason SAFETY, BLOCKLIST,
    PROHIBITED_CONTENT, SPII, RECITATION, ESCALATION, LANGUAGE) are provider blocks. MAX_TOKENS and CONTINUATION
    stop at a token limit and are recorded as 'max_tokens'. PUP_LIMITED_DISABLED says that the account is limited
    or disabled under Google's Prohibited Use Policy: not an outcome of the request, so AccountRestricted.

    Errors. generateContent reports blocks inside a normal response; its 400s name a malformed request or a missing
    precondition (INVALID_ARGUMENT, FAILED_PRECONDITION: parameter-error signatures). A 400 in the block form of
    Google's Interactions API (error code safety, jailbreak, prohibited_content or blocklist, or a message that
    starts with 'Input blocked:') is still read as a block. Every other HTTP error keeps its status and body, as in
    the other adapters; an unexplained 400/403 is a suspected block."""

    BASE = "https://generativelanguage.googleapis.com/v1beta"
    BLOCK_FINISH = frozenset(NATIVE_BLOCK_REASONS | {"escalation", "language"})
    LIMIT_FINISH = frozenset({"MAX_TOKENS", "CONTINUATION"})
    ACCOUNT_FINISH = frozenset({"PUP_LIMITED_DISABLED"})
    HTTP_BLOCK_CODES = frozenset({"safety", "jailbreak", "prohibited_content", "blocklist"})

    def __init__(self, cfg):
        super().__init__(cfg)
        self.key = key_from_env(RESEARCH_KEYS["google"])
        self.base = (cfg.get("base_url") or self.BASE).rstrip("/")

    def body(self, request):
        system, msgs = split_system(as_messages(request))
        contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                    for m in msgs]
        gen = {"maxOutputTokens": self.cfg["max_output_tokens"]}
        if self.cfg.get("temperature") is not None:
            gen["temperature"] = self.cfg["temperature"]
        if self.cfg.get("seed") is not None:
            gen["seed"] = self.cfg["seed"]
        if self.cfg.get("effort"):
            gen["thinkingConfig"] = {"thinkingLevel": str(self.cfg["effort"]).upper()}
        body = {"contents": contents, "generationConfig": gen}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if self.cfg.get("service_tier"):
            body["service_tier"] = self.cfg["service_tier"]
        return body

    def http_block(self, status, body):
        """A 400 in the block form of Google's Interactions API, as a block record; else None."""
        if status != 400:
            return None
        try:
            err = json.loads(body).get("error")
        except Exception:
            return None
        if not isinstance(err, dict):
            return None
        code, msg = str(err.get("code") or "").lower(), str(err.get("message") or "")
        if code not in self.HTTP_BLOCK_CODES and not msg.startswith("Input blocked:"):
            return None
        category = code if code in self.HTTP_BLOCK_CODES else "input_blocked"
        return {"text": "", "stop_reason": f"provider_block:{status}", "provider_block": True,
                "block_marker": category, "block_category": category, "served_provider": "google",
                "model_returned": None, "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": None,
                "cost_reported": None, "request_id": None, "error_body": body[:2000]}

    def call(self, request):
        url = f"{self.base}/models/{self.cfg['model']}:generateContent"
        req = urllib.request.Request(url, data=json.dumps(self.body(request)).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": self.key})
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", "replace")[:2000]
            except Exception:
                body = ""
            # classify_rejection raises SuspectedBlock for an unexplained 400/403
            block = self.http_block(e.code, body) or classify_rejection(e.code, body)
            if block is not None:
                return dict(block, served_provider="google")
            raise HTTPStatusError(e.code, body) from None
        try:
            data = json.loads(raw)
        except Exception as e:
            raise ResponseParseError(f"{type(e).__name__}: {e}") from e
        try:
            return self.parse(data)
        except AccountRestricted:
            raise
        except Exception as e:
            raise ResponseParseError(f"{type(e).__name__}: {e}") from e

    def parse(self, r):
        cands = r.get("candidates") or []
        cand = cands[0] if cands else {}
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        finish = str(cand.get("finishReason") or "")
        if finish in self.ACCOUNT_FINISH:
            raise AccountRestricted(f"Gemini API finishReason {finish}: the account is limited or disabled under "
                                    "Google's Prohibited Use Policy (Section 16.5)")
        prompt_block = str((r.get("promptFeedback") or {}).get("blockReason") or "")
        if prompt_block == "BLOCK_REASON_UNSPECIFIED":
            prompt_block = ""
        blocked = bool(prompt_block) or finish.lower() in self.BLOCK_FINISH
        if finish in self.LIMIT_FINISH:
            stop = "max_tokens"
        elif finish:
            stop = finish.lower()
        else:
            stop = "prompt_blocked" if prompt_block else "none"
        u = r.get("usageMetadata") or {}
        thoughts = u.get("thoughtsTokenCount")
        return {
            "text": text,
            "stop_reason": stop,
            "native_finish_reason": finish or prompt_block or None,
            "provider_block": blocked,
            "block_category": (prompt_block or finish) if blocked else None,
            "served_provider": "google",
            "model_returned": str(r.get("modelVersion") or "").removeprefix("models/") or None,
            "input_tokens": u.get("promptTokenCount") or 0,
            "cache_read_tokens": u.get("cachedContentTokenCount"),
            "cache_write_tokens": None,
            "output_tokens": (u.get("candidatesTokenCount") or 0) + (thoughts or 0),
            "reasoning_tokens": thoughts,
            "cost_reported": None,
            "request_id": r.get("responseId"),
        }


class OllamaProvider(Provider):
    """Native Ollama API on the local GPU (thinking switch, fixed seed, context size)."""

    def __init__(self, cfg):
        super().__init__(cfg)
        if is_remote(cfg):
            raise ProjectKeyError("the Ollama adapter is for the local GPU only")
        self.base = cfg.get("base_url", "http://localhost:11434").rstrip("/")

    def body(self, request):
        opts = {"num_predict": self.cfg["max_output_tokens"], "seed": self.cfg.get("seed", 20261126)}
        if self.cfg.get("temperature") is not None:
            opts["temperature"] = self.cfg["temperature"]
        if self.cfg.get("num_ctx"):
            opts["num_ctx"] = self.cfg["num_ctx"]
        opts.update(self.cfg.get("options") or {})   # explicit sampling options override Modelfile defaults (Section 8.3)
        body = {"model": self.cfg["model"], "stream": False, "messages": as_messages(request), "options": opts}
        if "think" in self.cfg:
            body["think"] = self.cfg["think"]
        for k in ("truncate", "shift"):     # judges (protocol v2.3, Section 11.2): never shorten the conversation
            if k in self.cfg:
                body[k] = self.cfg[k]
        return body

    def call(self, request):
        req = urllib.request.Request(self.base + "/api/chat", data=json.dumps(self.body(request)).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        try:
            with local_urlopen(req, timeout=900) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:      # keep the status and the body (context overflow, Section 10.2)
            try:
                body = e.read().decode("utf-8", "replace")[:2000]
            except Exception:
                body = ""
            raise HTTPStatusError(e.code, body) from None
        try:
            r = json.loads(raw)
        except Exception as e:
            raise ResponseParseError(f"{type(e).__name__}: {e}") from e
        visible, block = split_inband_reasoning(r.get("message", {}).get("content", ""))     # decision D22
        return {
            "text": visible,
            "inband_reasoning": block,
            "inband_reasoning_chars": len(block) if block else 0,
            "stop_reason": str(r.get("done_reason")),
            "provider_block": False,
            "block_category": None,
            "served_provider": "ollama-local",
            "model_returned": r.get("model"),
            "input_tokens": r.get("prompt_eval_count", 0),
            "output_tokens": r.get("eval_count", 0),
            "reasoning_tokens": None,
            "cost_reported": 0.0,
            "request_id": None,
        }


def ollama_identity(model, base="http://localhost:11434"):
    """Digest, quantization and template hash of a local model, for provenance (Section 6.3)."""
    import hashlib
    with local_urlopen(base + "/api/tags", timeout=30) as resp:
        tags = {m["name"]: m for m in json.loads(resp.read().decode("utf-8"))["models"]}
    req = urllib.request.Request(base + "/api/show", data=json.dumps({"model": model}).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with local_urlopen(req, timeout=60) as resp:
        show = json.loads(resp.read().decode("utf-8"))
    with local_urlopen(base + "/api/version", timeout=30) as resp:
        version = json.loads(resp.read().decode("utf-8")).get("version")
    tag = tags.get(model) or tags.get(model + ":latest") or {}
    return {
        "digest": tag.get("digest"),
        "quantization": (show.get("details") or {}).get("quantization_level"),
        "parameter_size": (show.get("details") or {}).get("parameter_size"),
        "template_sha256": hashlib.sha256((show.get("template") or "").encode("utf-8")).hexdigest(),
        "ollama_version": version,
    }


def ollama_vram(model, base="http://localhost:11434"):
    """GPU memory of a loaded local model (bytes), for the 6 GB fit check (Section 6.3)."""
    with local_urlopen(base + "/api/ps", timeout=30) as resp:
        for m in json.loads(resp.read().decode("utf-8")).get("models", []):
            if m.get("name") == model or m.get("model") == model:
                return {"size_vram": m.get("size_vram"), "size": m.get("size")}
    return {"size_vram": None, "size": None}


PROVIDERS = {"anthropic": AnthropicProvider, "openai": OpenAIProvider, "google": GoogleProvider,
             "openai_compatible": OpenAICompatibleProvider, "ollama": OllamaProvider}


def allowed(cfg, row):
    """True when this prompt may be sent to this model (protocol v2.1, Section 5.2).

    Local models receive every prompt. A remote model receives prompts expected to be refused
    only when its config sets receives_harmful=true; the key check in the adapter applies to
    every remote call. Which prompts each model actually runs is set by its prompt subset.
    """
    if not is_remote(cfg):
        return True
    if row["expected"] == "comply":
        return True
    return cfg.get("receives_harmful") is True


def make(cfg):
    return PROVIDERS[cfg["provider"]](cfg)


def timed_call(provider, request):
    t0 = time.perf_counter()
    out = provider.call(request)
    out["latency_s"] = round(time.perf_counter() - t0, 2)
    return out
