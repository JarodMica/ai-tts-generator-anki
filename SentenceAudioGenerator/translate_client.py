from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import AddonConfig, TranslationHeaderConfig
from .constants import LANGUAGE_NAMES


class TranslationClientError(Exception):
    pass


def language_name(code: str) -> str:
    normalized = code.replace("_", "-")
    return LANGUAGE_NAMES.get(normalized.lower(), normalized)


def build_prompt(text: str, source_lang: str, target_lang: str) -> str:
    source_lang = source_lang.replace("_", "-")
    target_lang = target_lang.replace("_", "-")
    source_name = language_name(source_lang)
    target_name = language_name(target_lang)
    return (
        "<bos><start_of_turn>user\n"
        f"You are a professional {source_name} ({source_lang}) to "
        f"{target_name} ({target_lang}) translator. Your goal is to accurately "
        f"convey the meaning and nuances of the original {source_name} text "
        f"while adhering to {target_name} grammar, vocabulary, and cultural "
        "sensitivities.\n"
        f"Produce only the {target_name} translation, without any additional "
        f"explanations or commentary. Please translate the following "
        f"{source_name} text into {target_name}:\n\n\n"
        f"{text.strip()}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )


def translate(
    config: AddonConfig,
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    endpoint = config.translation_endpoint
    prompt = build_prompt(text, source_lang, target_lang)
    payload = {
        "model": endpoint.model,
        "prompt": prompt,
        "max_tokens": endpoint.max_tokens,
        "temperature": 0,
        "stop": ["<end_of_turn>"],
    }

    headers = {"Content-Type": "application/json"}
    for header in config.translation_headers:
        if header.name:
            headers[header.name] = header.value

    request = Request(
        endpoint.url(),
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers=headers,
    )

    try:
        with urlopen(request, timeout=endpoint.timeout_seconds) as response:
            raw = response.read()
            if not raw:
                raise TranslationClientError("The translation server returned an empty response.")
            data = json.loads(raw.decode("utf-8"))
    except HTTPError as exc:
        raise TranslationClientError(format_http_error(exc)) from exc
    except URLError as exc:
        raise TranslationClientError(f"Could not reach the translation server: {exc.reason}") from exc
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        raise TranslationClientError(f"Malformed response from translation server: {exc}") from exc

    translated = data["choices"][0]["text"].strip()
    if not translated:
        raise TranslationClientError("The translation server returned empty text.")
    return translated


def format_http_error(exc: HTTPError) -> str:
    body = exc.read()
    detail = ""
    if body:
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            detail = body.decode("utf-8", errors="replace").strip()
        else:
            detail = str(payload.get("detail", "")).strip()
    if detail:
        return f"Translation request failed with HTTP {exc.code}: {detail}"
    return f"Translation request failed with HTTP {exc.code}."
