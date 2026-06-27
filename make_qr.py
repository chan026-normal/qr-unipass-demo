"""
make_qr.py — turn the deployed app URL into a scannable QR image (navy on white).

Usage:
    python make_qr.py https://your-app.streamlit.app
    python make_qr.py https://your-app.streamlit.app --out slide_qr.png

Put the resulting PNG onto slides 5 and 12.
"""
import sys

import qrcode

NAVY = (20, 41, 76)     # #14294C
WHITE = (255, 255, 255)


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: python make_qr.py <URL> [--out qr.png]")
        sys.exit(0 if args else 1)

    url = args[0]
    out = "qr.png"
    if "--out" in args:
        out = args[args.index("--out") + 1]

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=NAVY, back_color=WHITE)
    img.save(out)
    print(f"Saved {out}  ->  {url}")


if __name__ == "__main__":
    main()
