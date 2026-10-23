import argparse

from .runner import build_report, write_report


def main():
    parser = argparse.ArgumentParser(description="Offline synthetic security-lab prototype; no model calls")
    parser.add_argument("--output", required=True, help="New output directory; existing evidence is never overwritten")
    args = parser.parse_args()
    report = build_report()
    write_report(report, args.output)
    print("Synthetic prototype report written. No real-model or deployment claim.")
    print("Quality:", report["quality_summary"])
    print("Security contracts:", report["security_summary"])
    return 0 if report["demonstration_intact"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
