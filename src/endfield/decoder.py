
from __future__ import annotations
from typing import Any

from .errors import DecodeError


class DataDecoder:
    def __init__(self, raw: dict) -> None:
        try:
            self._data: list[Any] = raw["nodes"][1]["data"]
        except (KeyError, IndexError, TypeError) as exc:
            raise DecodeError(
                f"Unexpected API response shape — could not locate nodes[1].data: {exc}"
            ) from exc

    def decode(self) -> dict:
        try:
            return self._resolve(self._data[0])
        except RecursionError as exc:
            raise DecodeError("Circular reference detected in data array") from exc
        except (IndexError, KeyError, TypeError) as exc:
            raise DecodeError(f"Failed to resolve data array: {exc}") from exc

    def _resolve(self, node: Any) -> Any:
        if isinstance(node, dict):
            return {key: self._resolve(self._data[idx]) for key, idx in node.items()}

        if isinstance(node, list):
            result = []
            for item in node:
                if isinstance(item, int):
                    result.append(self._resolve(self._data[item]))
                else:
                    # Non-integer list elements are direct values (defensive)
                    result.append(self._resolve(item))
            return result
        return node
