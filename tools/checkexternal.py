#!/usr/bin/env python3
"""Are the sources this archive cites still there?

databases.tanap.net stopped resolving between one search and the next on 15
September. It holds the full transcriptions of the inventory that names eleven
enslaved people, and this site had gone on citing it as though it were live.

links.py checks internal links. Nothing checked the outside world, and the
outside world is where the documents are.

THIS IS NOT IN build.sh AND SHOULD NOT BE. A network check inside a build makes
the build fail for reasons that have nothing to do with the change, and a check
that fails for the wrong reason is a check people learn to ignore. It is run on
demand, and it writes what it finds to site/src/data/sources-state.json so the
site can SAY a source is dark rather than quietly linking into nothing.

  python3 tools/checkexternal.py            # check and write
  python3 tools/checkexternal.py --dry      # check and print only
"""
import os, re, sys, json, glob, socket, argparse, datetime, subprocess
import urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "src", "data", "sources-state.json")
UA = {"User-Agent": "TheBooyzenArchive/1.0 (family history; contact via the site)"}
SKIP = re.compile(r"^https?://(localhost|127\.|daviddef\.github\.io)", re.I)


# A host written in prose is still a citation. The case this tool exists for -
# databases.tanap.net going dark - was never an <a href> anywhere on the site:
# it was a sentence saying where the full transcriptions are. Checking only
# hyperlinks would have missed the one thing that actually happened.
BARE = re.compile(r"\b((?:[a-z0-9][a-z0-9-]*\.)+(?:org|net|com|gov|ac|edu|uk|za|nl|ie)"
                  r"(?:\.[a-z]{2})?)\b", re.I)
NOT_A_HOST = re.compile(r"^(e\.g|i\.e|vs|no|op|dr|mrs|ms|st)\.", re.I)


def hosts_cited():
    """every external host this archive points at - linked OR named in prose"""
    seen = {}
    def note(host, url, n=1):
        host = host.lower().rstrip(".")
        if SKIP.match("http://" + host) or NOT_A_HOST.match(host):
            return
        seen.setdefault(host, {"n": 0, "one": url, "where": set()})
        seen[host]["n"] += n
        if seen[host]["one"].count("/") < 3 and url.count("/") >= 3:
            seen[host]["one"] = url  # prefer a real path over a bare root

    for f in glob.glob(os.path.join(ROOT, "site", "dist", "**", "*.html"), recursive=True):
        html = open(f, encoding="utf-8", errors="ignore").read()
        for url in re.findall(r'href="(https?://[^"#\s]+)"', html):
            h = re.sub(r"^https?://", "", url).split("/")[0]
            note(h, url)
            if h.lower() in seen:
                rel = os.path.relpath(os.path.dirname(f), os.path.join(ROOT, "site", "dist"))
                seen[h.lower()]["where"].add("/" if rel == "." else "/" + rel.replace(os.sep, "/") + "/")

    # A host named in a sentence is still a citation, and the file it is named in
    # is where somebody has to go to fix it. Reporting a dark source without
    # saying where it is cited is half a check.
    for f in glob.glob(os.path.join(ROOT, "site", "src", "data", "*.json")) + \
             glob.glob(os.path.join(ROOT, "site", "src", "pages", "*.astro")):
        if f.endswith("sources-state.json"):
            continue
        for host in set(BARE.findall(open(f, encoding="utf-8", errors="ignore").read())):
            note(host, "https://" + host + "/")
            if host.lower() in seen:
                seen[host.lower()]["where"].add(os.path.relpath(f, ROOT))
    return seen


def probe(host, one):
    """Resolve, then ask. A name that will not resolve is the thing that happened.

    BUT: the first version of this tool called three live government domains
    dark, because getaddrinfo asks for A records and a domain can be perfectly
    alive with nothing but MX. kzndac.gov.za has no website and takes mail; on
    the strength of that this archive was one edit away from publishing that
    the Pietermaritzburg email addresses were both dead. THEY ACCEPT MAIL.
    So: no A record is not dark until the MX has been asked for too.
    """
    try:
        socket.getaddrinfo(host, None)
    except socket.gaierror:
        try:
            mx = subprocess.run(["host", "-t", "MX", host], capture_output=True,
                                text=True, timeout=15).stdout
        except Exception:
            mx = ""
        if "handled by" in mx:
            return "mail only", "no website, but takes mail"
        return "dark", "does not resolve"
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(one, headers=UA, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return "up", str(r.status)
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501, 503):
                continue  # plenty of servers simply refuse HEAD
            break
        except Exception as e:
            if method == "HEAD":
                continue
            return "down", type(e).__name__
    err = locals().get("e")
    if isinstance(err, urllib.error.HTTPError):
        e = err
    else:
        return "down", type(err).__name__ if err else "no response"
    try:
        raise e
    except urllib.error.HTTPError as e:
        # 403 is very often a bot check rather than a dead page, and this
        # archive does not go around bot checks - so it is recorded as guarded,
        # which is true, rather than as broken, which would not be.
        return ("guarded" if e.code in (401, 403, 429) else "up" if e.code < 500 else "down"), str(e.code)
    except Exception as e:
        return "down", type(e).__name__


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any host is dark - off by default, see above")
    a = ap.parse_args()

    rows, cited = [], hosts_cited()
    for host, info in sorted(cited.items(), key=lambda kv: -kv[1]["n"]):
        state, why = probe(host, info["one"])
        rows.append({"host": host, "cited": info["n"], "state": state, "why": why,
                     "where": sorted(info.get("where", []))[:8]})
        mark = {"up": "  ok  ", "guarded": "  warn", "dark": "  dark",
                "down": "  warn", "mail only": "  ok  "}[state]
        print(f"{mark}  external   {host:<34} {state:<8} {why:<18} cited {info['n']}x")

    # A dark host is NOT a failure, and working the tool taught that.
    #
    # All four dark hosts on the first full run are cited only from the registers
    # that exist to record failure - corrections, searched, the work list - and
    # from the passages on /sources/ that say those hosts are gone. A page whose
    # subject is "this source died" will always cite the source that died, and a
    # check that fails the build for it would be punishing the archive for saying
    # so out loud.
    #
    # So this reports and does not refuse. What it is actually for is the WHERE
    # and the HISTORY: which files depend on a host, and whether the ground is
    # moving. Exit non-zero only when asked.
    dark = [r for r in rows if r["state"] == "dark"] if a.strict else []
    darknames = [r["host"] for r in rows if r["state"] == "dark"]
    prev = {}
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding="utf-8"))
            prev = {r["host"]: r["state"] for r in old.get("rows", [])}
            history = old.get("history", [])
            if old.get("checked") and old.get("checked") != datetime.date.today().isoformat():
                history = ([{"checked": old["checked"],
                             "dark": sorted(r["host"] for r in old["rows"] if r["state"] == "dark"),
                             "hosts": len(old["rows"])}] + history)[:12]
        except Exception:
            history = []
    else:
        history = []

    for r in rows:
        was = prev.get(r["host"])
        if was and was != r["state"]:
            r["changed_from"] = was
            print(f"  note  external   {r['host']} was {was}, is now {r['state']}")

    if not a.dry:
        json.dump({"history": history, "note": "Written by tools/checkexternal.py. Not part of the build: a network "
                           "check inside a build fails for reasons that have nothing to do with "
                           "the change, and a check that fails for the wrong reason is a check "
                           "people learn to ignore.",
                   "checked": datetime.date.today().isoformat(), "rows": rows},
                  open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  {'FAIL' if dark else 'ok  '}  external   {len(rows)} hosts, "
          f"{len(darknames)} dark ({', '.join(darknames) if darknames else 'none'})")
    return 1 if dark else 0


if __name__ == "__main__":
    sys.exit(main())
