"""Reproduce today's news-poster entry: verify entry.png and emit it for the grader."""
import hashlib
import json
import os
import struct
import sys

ENTRY_NAME = "entry.png"
LIMIT_BYTES = 1 << 20
LIMIT_SIDE = 1024
SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print(json.dumps({"ok": False, "error": message}))
    return 1


def image_geometry(blob):
    if blob[:8] != SIGNATURE or len(blob) < 33 or blob[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", blob[16:24])
    return width, height


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def run():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, ENTRY_NAME)

    try:
        with open(source, "rb") as fh:
            blob = fh.read()
    except FileNotFoundError:
        return fail(f"missing {ENTRY_NAME} next to main.py")
    except OSError as exc:
        return fail(f"cannot read {ENTRY_NAME}: {exc}")

    if len(blob) > LIMIT_BYTES:
        return fail(f"{len(blob)} bytes exceeds the {LIMIT_BYTES}-byte cap")

    geometry = image_geometry(blob)
    if geometry is None:
        return fail("file is not a PNG (bad signature or no IHDR)")
    width, height = geometry
    if width > LIMIT_SIDE or height > LIMIT_SIDE:
        return fail(f"{width}x{height} exceeds the {LIMIT_SIDE}px cap")

    out_root = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(here, "out")
    try:
        os.makedirs(out_root, exist_ok=True)
    except OSError as exc:
        return fail(f"output directory unusable: {exc}")

    final = os.path.join(out_root, ENTRY_NAME)
    staging = final + ".part"
    try:
        with open(staging, "wb") as fh:
            fh.write(blob)
            fh.flush()
            os.fsync(fh.fileno())
        with open(staging, "rb") as fh:
            if fh.read() != blob:
                return fail("verification readback differs")
        os.replace(staging, final)
    except OSError as exc:
        return fail(f"write failed: {exc}")

    print(json.dumps({
        "ok": True,
        "entry": os.path.abspath(final),
        "pixels": f"{width}x{height}",
        "bytes": len(blob),
        "sha256": digest(blob),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(run())
