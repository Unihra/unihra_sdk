import argparse
import sys
import json
import os
from unihra import UnihraClient, UnihraError

def main():
    parser = argparse.ArgumentParser(description="Unihra CLI: SEO Analysis Tool")

    # Required args
    parser.add_argument("--key", help="API Key (or set UNIHRA_API_KEY env var)")
    parser.add_argument("--own", help="Your page URL")
    parser.add_argument("--comp", required=True, action="append", help="Competitor URL (repeatable)")

    # Optional Context Query
    parser.add_argument("--query", action="append", help="Target search query for Context Analysis (repeatable)")

    # New Options
    parser.add_argument("--cookies", help="Auth cookies for Own Page (e.g. 'session=123; auth=abc')")
    parser.add_argument("--lang", default="ru", choices=["ru", "en"], help="Language")
    parser.add_argument("--save", help="Filename to save report (e.g. analysis.xlsx or .csv)")
    parser.add_argument("--retries", type=int, default=0, help="Max retries for connection stability")
    parser.add_argument("--verbose", action="store_true", help="Show real-time progress")
    parser.add_argument("--no-style", action="store_true", help="Disable Excel styling (colors, auto-width)")
    parser.add_argument(
        "--triplets",
        action="store_true",
        help="Enable extended Knowledge Graph analysis (5 credits instead of 1)"
    )
    parser.add_argument(
        "--limits",
        action="store_true",
        help="Show current API key usage limits and balance, then exit"
    )

    args = parser.parse_args()

    # Get Key
    api_key = args.key or os.getenv("UNIHRA_API_KEY")
    if not api_key:
        print("Error: API Key required. Pass --key or set UNIHRA_API_KEY env var.", file=sys.stderr)
        sys.exit(1)

    client = UnihraClient(api_key=api_key, max_retries=args.retries)

    # --limits: show balance and exit
    if args.limits:
        try:
            limits = client.get_limits()
            print(json.dumps(limits, indent=2, ensure_ascii=False))
        except UnihraError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    if not args.own:
        print("Error: --own is required for analysis.", file=sys.stderr)
        sys.exit(1)

    # Construct url_cookies if provided via CLI
    url_cookies = {}
    if args.cookies:
        url_cookies[args.own] = args.cookies

    try:
        if args.verbose:
            print(f"🚀 Starting analysis for {args.own}...")
            if args.query:
                print(f"🔎 Context Queries: {args.query}")
            if url_cookies:
                print(f"🍪 Auth Cookies applied to Own Page.")
            if args.triplets:
                print(f"🧠 Triplets (Knowledge Graph) enabled — cost: 5 credits.")
            else:
                print(f"💳 Standard analysis — cost: 1 credit.")

        # Analyze will now automatically fetch Page Structure upon success
        result = client.analyze(
            own_page=args.own,
            competitors=args.comp,
            queries=args.query,
            lang=args.lang,
            url_cookies=url_cookies, # Passing cookies
            triplet_analysis=args.triplets,
            verbose=args.verbose
        )

        if args.verbose:
            print("\n✅ Analysis complete!")
            if 'page_structure' in result:
                print("📋 Page Structure data extracted successfully.")
            if args.triplets and 'triplets_analysis' in result:
                stats = (result.get("triplets_analysis") or {}).get("stats") or {}
                if stats:
                    print(
                        "🧠 Knowledge Graph: "
                        f"{stats.get('total_triplets', 0)} triplets, "
                        f"{stats.get('gaps_total', 0)} gaps "
                        f"(critical={stats.get('gaps_critical', 0)}, "
                        f"important={stats.get('gaps_important', 0)}, "
                        f"unique={stats.get('gaps_unique', 0)})."
                    )

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
