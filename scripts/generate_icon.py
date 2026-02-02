import argparse
import os
import struct
import zlib


def make_png_rgba(width, height):
    background = (31, 90, 166, 255)
    check = (255, 255, 255, 255)
    pixels = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append(background)
        pixels.append(row)

    # Simple checkmark
    for i in range(12):
        x = 16 + i
        y = 36 + i // 2
        if 0 <= x < width and 0 <= y < height:
            pixels[y][x] = check
    for i in range(20):
        x = 24 + i
        y = 44 - i // 2
        if 0 <= x < width and 0 <= y < height:
            pixels[y][x] = check

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # no filter
        for x in range(width):
            raw.extend(pixels[y][x])

    compressed = zlib.compress(bytes(raw))
    return build_png_bytes(width, height, compressed)


def build_png_bytes(width, height, compressed):
    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = compressed
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def build_ico(png_bytes, width, height):
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack(
        "<BBBBHHII",
        width if width < 256 else 0,
        height if height < 256 else 0,
        0,
        0,
        1,
        32,
        len(png_bytes),
        6 + 16,
    )
    return header + entry + png_bytes


def read_png_dimensions(png_bytes):
    signature = b"\x89PNG\r\n\x1a\n"
    if not png_bytes.startswith(signature):
        raise ValueError("Not a PNG file.")
    offset = 8
    length = struct.unpack(">I", png_bytes[offset : offset + 4])[0]
    chunk_type = png_bytes[offset + 4 : offset + 8]
    if chunk_type != b"IHDR":
        raise ValueError("Invalid PNG: missing IHDR.")
    ihdr = png_bytes[offset + 8 : offset + 8 + length]
    width = struct.unpack(">I", ihdr[0:4])[0]
    height = struct.unpack(">I", ihdr[4:8])[0]
    return width, height


def load_png_bytes(source_path):
    with open(source_path, "rb") as handle:
        return handle.read()


def main():
    parser = argparse.ArgumentParser(description="Generate app icon assets.")
    parser.add_argument(
        "--source",
        help="Path to a PNG file to use as the app icon.",
    )
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    assets_dir = os.path.join(project_root, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    png_path = os.path.join(assets_dir, "app.png")
    ico_path = os.path.join(assets_dir, "app.ico")

    if args.source:
        source_path = os.path.abspath(args.source)
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source PNG not found: {source_path}")
        png_bytes = load_png_bytes(source_path)
        with open(png_path, "wb") as handle:
            handle.write(png_bytes)
    elif os.path.exists(png_path):
        png_bytes = load_png_bytes(png_path)
    else:
        width = 64
        height = 64
        png_bytes = make_png_rgba(width, height)
        with open(png_path, "wb") as handle:
            handle.write(png_bytes)

    width, height = read_png_dimensions(png_bytes)
    ico_bytes = build_ico(png_bytes, width, height)
    with open(ico_path, "wb") as handle:
        handle.write(ico_bytes)

    print(f"Generated {png_path} and {ico_path}")


if __name__ == "__main__":
    main()
