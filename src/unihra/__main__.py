import argparse
import sys
import json
import os
from unihra import UnihraClient, UnihraError

def main():
    parser = argparse.ArgumentParser(description="Unihra CLI: SEO Analysis Tool")
    
    # Required args
    parser.add_argument("--key", help="API Key (or set UNIHRA_API_KEY env var)")
    parser.add_argument("--own", required=True, help="Your page URL")
    parser.add_argument("--comp", required=True, action="append", help="Competitor URL (repeatable)")
    
    # Options
    parser.add_argument("--lang", default="ru", choices=["ru", "en"], help="Language")
    parser.add_argument("--save", help="Filename to save report (e.g. analysis.xlsx or .csv)")
    parser.add_argument("--retries", type=int, default=0, help="Max retries for connection stability")
    parser.add_argument("--verbose", action="store_true", help="Show real-time progress")
    parser.add_argument("--no-style", action="store_true", help="Disable Excel styling (colors, auto-width)")

    args = parser.parse_args()
    
    # Get Key
    api_key = args.key or os.getenv("UNIHRA_API_KEY")
    if not api_key:
        print("Error: API Key required. Pass --key or set UNIHRA_API_KEY env var.", file=sys.stderr)
        sys.exit(1)

    client = UnihraClient(api_key=api_key, max_retries=args.retries)

    try:
        if args.verbose:
            print(f"🚀 Starting analysis for {args.own}...")
        
        result = client.analyze(args.own, args.comp, args.lang, verbose=args.verbose)
        
        if args.verbose:
            print("\n✅ Done!")

        # Output logic
        if args.save:
            apply_styling = not args.no_style
            print(f"💾 Saving report to {args.save} (Styling: {apply_styling})...")
            client.save_report(result, args.save, style_output=apply_styling)
            
        elif not args.verbose:
            # If not saving and not verbose, dump JSON to stdout
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except UnihraError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Aborted by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()