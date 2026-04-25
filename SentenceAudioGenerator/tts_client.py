from __future__ import annotations

import json
import mimetypes
import uuid
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import AddonConfig


class TTSClientError(Exception):
    pass


@dataclass
class TTSRequest:
    text: str
    reference_audio_name: str
    reference_audio_bytes: bytes
    transcript_text: str | None


def synthesize(config: AddonConfig, request_data: TTSRequest) -> bytes:
    boundary = uuid.uuid4().hex
    body = bytearray()

    append_text_part(
        body,
        boundary,
        config.endpoint.text_field_name,
        request_data.text,
    )
    append_file_part(
        body,
        boundary,
        config.endpoint.reference_audio_field_name,
        request_data.reference_audio_name,
        request_data.reference_audio_bytes,
    )
    transcript_field = config.endpoint.transcript_text_field_name.strip()
    if transcript_field and request_data.transcript_text:
        append_text_part(body, boundary, transcript_field, request_data.transcript_text)
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "audio/wav",
    }
    for header in config.headers:
        if header.name:
            headers[header.name] = header.value

    request = Request(
        config.endpoint.url(),
        data=bytes(body),
        method="POST",
        headers=headers,
    )

    try:
        with urlopen(request, timeout=config.endpoint.timeout_seconds) as response:
            payload = response.read()
            content_type = response.headers.get("Content-Type", "")
            if not payload:
                raise TTSClientError("The TTS server returned an empty response.")
            if "audio/wav" not in content_type:
                raise TTSClientError(
                    f"Unexpected response content type: {content_type or 'unknown'}"
                )
            return payload
    except HTTPError as exc:
        raise TTSClientError(format_http_error(exc)) from exc
    except URLError as exc:
        raise TTSClientError(f"Could not reach the TTS server: {exc.reason}") from exc


def append_text_part(body: bytearray, boundary: str, name: str, value: str) -> None:
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8")
    )
    body.extend(value.encode("utf-8"))
    body.extend(b"\r\n")


def append_file_part(
    body: bytearray,
    boundary: str,
    name: str,
    filename: str,
    data: bytes,
) -> None:
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        (
            f'Content-Disposition: form-data; name="{name}"; '
            f'filename="{filename}"\r\n'
        ).encode("utf-8")
    )
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    body.extend(data)
    body.extend(b"\r\n")


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
        return f"TTS request failed with HTTP {exc.code}: {detail}"
    return f"TTS request failed with HTTP {exc.code}."
