"""Tokenize with the installed GGUF's own vocabulary, merges and special tokens."""

import struct
from pathlib import Path
from typing import Any, BinaryIO

from synthesis_study.io import file_hash, read

TEMPLATE_DIGEST = "ae370d884f108d16e7cc8fd5259ebc5773a0afa6e078b11f4ed7e39a27e0dfc4"
PATTERN = (
    r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}"
    r"| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
)


def unpack(handle: BinaryIO, format_: str) -> Any:
    size = struct.calcsize("<" + format_)
    value = handle.read(size)
    if len(value) != size:
        raise ValueError("Truncated GGUF metadata")
    return struct.unpack("<" + format_, value)[0]


def gguf_value(handle: BinaryIO, kind: int) -> Any:
    formats = {
        0: "B",
        1: "b",
        2: "H",
        3: "h",
        4: "I",
        5: "i",
        6: "f",
        7: "?",
        10: "Q",
        11: "q",
        12: "d",
    }
    if kind in formats:
        return unpack(handle, formats[kind])
    if kind == 8:
        length = unpack(handle, "Q")
        value = handle.read(length)
        if len(value) != length:
            raise ValueError("Truncated GGUF string")
        return value.decode("utf-8")
    if kind == 9:
        element, length = unpack(handle, "I"), unpack(handle, "Q")
        return [gguf_value(handle, element) for _ in range(length)]
    raise ValueError(f"Unknown GGUF metadata kind {kind}")


def metadata(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        if handle.read(4) != b"GGUF" or unpack(handle, "I") != 3:
            raise ValueError("Require GGUF v3")
        unpack(handle, "Q")
        count = unpack(handle, "Q")
        result = {}
        for _ in range(count):
            key = gguf_value(handle, 8)
            result[key] = gguf_value(handle, unpack(handle, "I"))
        return result


class LocalTokenizer:
    def __init__(self, model_root: Path):
        from tokenizers import AddedToken, Regex, Tokenizer, models, pre_tokenizers

        manifest_path = model_root / "manifests/registry.ollama.ai/library/qwen3/14b"
        manifest = read(manifest_path)
        layers = {layer["mediaType"]: layer for layer in manifest["layers"]}
        model_layer = layers["application/vnd.ollama.image.model"]
        template_layer = layers["application/vnd.ollama.image.template"]
        if template_layer["digest"] != "sha256:" + TEMPLATE_DIGEST:
            raise ValueError("Unsupported Ollama template; renderer must be verified first")
        template = model_root / "blobs" / template_layer["digest"].replace(":", "-")
        if file_hash(template) != TEMPLATE_DIGEST:
            raise ValueError("Template content hash mismatch")
        model = model_root / "blobs" / model_layer["digest"].replace(":", "-")
        info = metadata(model)
        if info.get("tokenizer.ggml.model") != "gpt2" or info.get("tokenizer.ggml.pre") != "qwen2":
            raise ValueError("Require installed Qwen2 BPE pretokenizer")
        if info.get("tokenizer.ggml.add_bos_token", False):
            raise ValueError("Unexpected BOS insertion")
        vocab = {token: i for i, token in enumerate(info["tokenizer.ggml.tokens"])}
        merges = [tuple(pair.split(" ")) for pair in info["tokenizer.ggml.merges"]]
        self.tokenizer = Tokenizer(models.BPE(vocab, merges))
        self.tokenizer.pre_tokenizer = pre_tokenizers.Sequence(
            [
                pre_tokenizers.Split(Regex(PATTERN), behavior="isolated"),
                pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False),
            ]
        )
        specials = [
            AddedToken(token, special=True, normalized=False)
            for token, kind in zip(
                info["tokenizer.ggml.tokens"], info["tokenizer.ggml.token_type"], strict=True
            )
            if kind in {3, 4}
        ]
        self.tokenizer.add_special_tokens(specials)
        self.identity = {
            "method": "installed_gguf_vocabulary_and_merges",
            "manifest_sha256": file_hash(manifest_path),
            "model_blob_digest": model_layer["digest"],
            "model_blob_size": model.stat().st_size,
            "template_sha256": file_hash(template),
            "tokenizer_pre": info["tokenizer.ggml.pre"],
            "vocabulary_size": len(vocab),
            "merges": len(merges),
        }

    def count(self, text: str) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=False).ids)

    @staticmethod
    def render(body: dict[str, Any]) -> str:
        messages = body["messages"]
        if [message["role"] for message in messages] != ["system", "user"] or body.get(
            "think"
        ) is not False:
            raise ValueError("Renderer supports exactly system/user with think=false")
        return (
            "<|im_start|>system\n" + messages[0]["content"] + "<|im_end|>\n"
            "<|im_start|>user\n" + messages[1]["content"] + " /no_think<|im_end|>\n"
            "<|im_start|>assistant\n<think>\n\n</think>\n\n"
        )

    def prompt_count(self, body: dict[str, Any]) -> int:
        return self.count(self.render(body))

    def exported(self) -> dict[str, Any]:
        import tokenizers

        return {
            **self.identity,
            "library_version": tokenizers.__version__,
            "tokenizer_sha256": __import__("hashlib")
            .sha256(self.tokenizer.to_str().encode())
            .hexdigest(),
        }
