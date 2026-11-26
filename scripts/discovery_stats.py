"""Discovery figures for the Stage 1 workbook, computed from the course datasets.

Run from the project folder:  python -m scripts.discovery_stats
Prints the headline figures and writes every table to docs/discovery/ticket_stats.md.
Each figure in the workbook's data sections should be traceable to this output.

Definitions used throughout (development tickets unless stated):
- first contact resolution = history.first_contact_resolution is true
- escalation rate          = history.escalated is true
- repeat contact           = history.repeat_contact is true
- resolution time          = history.resolution_time_minutes (the pack does not define whether this is
                             elapsed or working time; treat it as a proxy)
- answerable from docs     = labels.answerable_from_docs is true
"""
from __future__ import annotations

import json
import math
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from src import config

OUTPUT = config.ROOT / "docs" / "discovery" / "ticket_stats.md"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ---------- helpers ----------

def load(name: str) -> list[dict]:
    return json.loads((config.DATA_DIR / name).read_text(encoding="utf-8"))


def pct(part: float, whole: float) -> str:
    return f"{100.0 * part / whole:.1f}%" if whole else "n/a"


def received(ticket: dict) -> datetime:
    return datetime.fromisoformat(ticket["received_at"].replace("Z", "+00:00"))


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def outcome_row(label: str, tickets: list[dict]) -> list:
    n = len(tickets)
    history = [t["history"] for t in tickets]
    minutes = [h["resolution_time_minutes"] for h in history]
    return [label, n,
            pct(sum(h["first_contact_resolution"] for h in history), n),
            pct(sum(h["escalated"] for h in history), n),
            pct(sum(h["repeat_contact"] for h in history), n),
            f"{st.mean(h['csat_rating'] for h in history):.2f}",
            f"{st.median(minutes):.0f}", f"{st.mean(minutes):.0f}"]


OUTCOME_HEADERS = ["Group", "Tickets", "First contact resolution", "Escalated", "Repeat contact",
                   "Mean satisfaction", "Median resolution (min)", "Mean resolution (min)"]


def group_by(tickets: list[dict], key) -> dict:
    groups = defaultdict(list)
    for t in tickets:
        groups[key(t)].append(t)
    return dict(sorted(groups.items(), key=lambda item: -len(item[1])))


def mann_whitney_p(a: list[float], b: list[float]) -> float:
    """Two-sided Mann-Whitney U test (normal approximation with tie correction)."""
    pooled = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks = [0.0] * len(pooled)
    i = 0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    n1, n2 = len(a), len(b)
    u = sum(r for r, (_, g) in zip(ranks, pooled) if g == 0) - n1 * (n1 + 1) / 2
    n = n1 + n2
    ties = sum(c ** 3 - c for c in Counter(v for v, _ in pooled).values())
    sigma = math.sqrt(n1 * n2 / 12 * ((n + 1) - ties / (n * (n - 1))))
    z = (u - n1 * n2 / 2) / sigma if sigma else 0.0
    return math.erfc(abs(z) / math.sqrt(2))


# ---------- sections ----------

def headline(dev: list[dict]) -> tuple[str, list[str]]:
    n = len(dev)
    times = sorted(received(t) for t in dev)
    weeks = (times[-1] - times[0]).days / 7
    channels = Counter(t["channel"] for t in dev)
    intents = Counter(t["labels"]["intent"] for t in dev)
    bodies = Counter(norm(t["body"]) for t in dev)
    top_body, top_count = bodies.most_common(1)[0]
    top_intent = next(t["labels"]["intent"] for t in dev if norm(t["body"]) == top_body)
    minutes = [t["history"]["resolution_time_minutes"] for t in dev]
    h = [t["history"] for t in dev]
    src = "development_tickets.json"
    rows = [
        ["Total tickets in sample", f"{n} ({times[0]:%d %b} – {times[-1]:%d %b %Y}, {weeks:.0f} weeks, ~{n / weeks:.0f} a week)", f"{src}, all records"],
        ["Channel split", ", ".join(f"{c} {pct(v, n)}" for c, v in channels.most_common()), f"{src}, channel"],
        ["Top five intents and share", ", ".join(f"{i} {pct(v, n)}" for i, v in intents.most_common(5)), f"{src}, labels.intent"],
        ["Most frequent single question", f"\"{top_body[:90]}…\" ({top_count} tickets, {top_intent})", f"{src}, body (exact repeats)"],
        ["Proportion answerable from existing docs", pct(sum(t["labels"]["answerable_from_docs"] for t in dev), n), f"{src}, labels.answerable_from_docs"],
        ["Proportion from non-fluent writers", pct(sum(t["language_fluency"] == "non_fluent" for t in dev), n), f"{src}, language_fluency"],
        ["Historical first contact resolution", pct(sum(x["first_contact_resolution"] for x in h), n), f"{src}, history.first_contact_resolution"],
        ["Average resolution time", f"mean {st.mean(minutes):.0f} min ({st.mean(minutes) / 60:.1f} h), median {st.median(minutes):.0f} min", f"{src}, history.resolution_time_minutes"],
        ["Average satisfaction", f"{st.mean(x['csat_rating'] for x in h):.2f} out of 5", f"{src}, history.csat_rating"],
        ["Escalation rate", pct(sum(x["escalated"] for x in h), n), f"{src}, history.escalated"],
        ["Repeat contacts", pct(sum(x["repeat_contact"] for x in h), n), f"{src}, history.repeat_contact"],
    ]
    summary = [f"{r[0]}: {r[1]}" for r in rows]
    return "## 1. Headline figures (Stage 1, section 2)\n\n" + table(["Measure", "Value", "Source"], rows), summary


def segments(dev: list[dict]) -> str:
    parts = ["## 2. Outcomes by customer group\n"]
    for title, key in [("Language fluency", lambda t: t["language_fluency"]),
                       ("Customer tier", lambda t: t["customer_tier"]),
                       ("Region", lambda t: t["customer_region"]),
                       ("Channel", lambda t: t["channel"]),
                       ("Urgency (label)", lambda t: t["labels"]["urgency"])]:
        rows = [outcome_row(g, ts) for g, ts in group_by(dev, key).items()]
        parts.append(f"### {title}\n\n" + table(OUTCOME_HEADERS, rows) + "\n")
    rows = []
    for ch, ts in group_by(dev, lambda t: t["channel"]).items():
        lengths = [len(t["body"]) for t in ts]
        rows.append([ch, len(ts), f"{st.median(lengths):.0f}", max(lengths),
                     pct(sum(t["labels"]["answerable_from_docs"] for t in ts), len(ts)),
                     pct(sum(t["labels"]["expected_route"] == "auto_respond" for t in ts), len(ts))])
    parts.append("### Channel detail\n\n" + table(
        ["Channel", "Tickets", "Median length (chars)", "Longest (chars)", "Answerable from docs", "Labelled auto-respond"], rows))
    return "\n".join(parts)


def effort(dev: list[dict]) -> str:
    n = len(dev)
    total = sum(t["history"]["resolution_time_minutes"] for t in dev)
    rows = []
    for intent, ts in group_by(dev, lambda t: t["labels"]["intent"]).items():
        minutes = sum(t["history"]["resolution_time_minutes"] for t in ts)
        rows.append([intent, len(ts), pct(len(ts), n), pct(minutes, total), f"{minutes / len(ts):.0f}",
                     pct(sum(t["history"]["first_contact_resolution"] for t in ts), len(ts)),
                     pct(sum(t["labels"]["answerable_from_docs"] for t in ts), len(ts)),
                     pct(sum(t["labels"]["expected_route"] == "auto_respond" for t in ts), len(ts)),
                     sum(t["labels"]["must_not_auto_respond"] for t in ts)])
    rows.sort(key=lambda r: -float(r[3].rstrip("%")))
    shares = []
    for label, test in [
        ("Labelled auto-respond", lambda t: t["labels"]["expected_route"] == "auto_respond"),
        ("Labelled escalate", lambda t: t["labels"]["expected_route"] == "escalate"),
        ("Must not auto-respond", lambda t: t["labels"]["must_not_auto_respond"]),
        ("Answerable from docs but escalated", lambda t: t["labels"]["answerable_from_docs"] and t["history"]["escalated"]),
    ]:
        ts = [t for t in dev if test(t)]
        shares.append([label, pct(len(ts), n), pct(sum(t["history"]["resolution_time_minutes"] for t in ts), total)])
    return ("## 3. Where the time goes (Stage 1, section 3)\n\nResolution minutes are the only time field, "
            "so they stand in for effort.\n\n"
            + table(["Intent", "Tickets", "% of volume", "% of resolution minutes", "Mean minutes",
                     "First contact resolution", "Answerable from docs", "Labelled auto-respond",
                     "Must not auto-respond"], rows)
            + "\n\n### Volume against time for groups of tickets\n\n"
            + table(["Group", "% of volume", "% of resolution minutes"], shares))


def findability(dev: list[dict]) -> str:
    escalated = [t for t in dev if t["history"]["escalated"]]
    answerable = [t for t in escalated if t["labels"]["answerable_from_docs"]]
    auto = [t for t in escalated if t["labels"]["expected_route"] == "auto_respond"]
    ans_all = [t for t in dev if t["labels"]["answerable_from_docs"]]
    rows = [
        ["Escalated tickets", len(escalated), pct(len(escalated), len(dev))],
        ["…of which answerable from docs", len(answerable), pct(len(answerable), len(escalated))],
        ["…of which labelled auto-respond", len(auto), pct(len(auto), len(escalated))],
        ["Answerable tickets resolved on first contact", sum(t["history"]["first_contact_resolution"] for t in ans_all),
         pct(sum(t["history"]["first_contact_resolution"] for t in ans_all), len(ans_all))],
        ["Answerable tickets that were escalated", sum(t["history"]["escalated"] for t in ans_all),
         pct(sum(t["history"]["escalated"] for t in ans_all), len(ans_all))],
    ]
    return "## 4. Answers that exist but were not delivered\n\n" + table(["Measure", "Tickets", "Share"], rows)


def checks(dev: list[dict]) -> str:
    parts = ["## 5. Checks for claims made in the interviews\n",
             "Neutral figures only: which person they support is a judgement for the workbook.\n"]

    esc = [t for t in dev if t["history"]["escalated"]]
    not_esc = [t for t in dev if not t["history"]["escalated"]]
    rows = [["Not escalated", len(not_esc), f"{st.mean(t['history']['csat_rating'] for t in not_esc):.2f}"],
            ["Escalated", len(esc), f"{st.mean(t['history']['csat_rating'] for t in esc):.2f}"]]
    for lo, hi in [(60, 240), (240, 600), (600, 10 ** 9)]:
        g = [t for t in esc if lo <= t["history"]["resolution_time_minutes"] < hi]
        label = f"Escalated, resolved in {lo}–{hi} min" if hi < 10 ** 9 else f"Escalated, resolved in {lo}+ min"
        rows.append([label, len(g), f"{st.mean(t['history']['csat_rating'] for t in g):.2f}" if g else "n/a"])
    fcr_minutes = [t["history"]["resolution_time_minutes"] for t in not_esc]
    esc_minutes = [t["history"]["resolution_time_minutes"] for t in esc]
    parts.append("### Satisfaction against escalation and waiting\n\n" + table(["Group", "Tickets", "Mean satisfaction"], rows)
                 + f"\n\nNon-escalated tickets took {min(fcr_minutes)}–{max(fcr_minutes)} min; "
                   f"escalated tickets took {min(esc_minutes)}–{max(esc_minutes)} min.\n")

    rows = []
    for route in ["auto_respond", "escalate"]:
        for urgency in ["high", "medium", "low"]:
            g = [t["history"]["resolution_time_minutes"] for t in dev
                 if t["labels"]["expected_route"] == route and t["labels"]["urgency"] == urgency]
            rows.append([route, urgency, len(g), f"{st.median(g):.0f}"])
    parts.append("### Waiting time by urgency, within each labelled route\n\n"
                 + table(["Labelled route", "Urgency", "Tickets", "Median resolution (min)"], rows) + "\n")

    days = Counter(received(t).strftime("%a") for t in dev)
    hours = Counter(received(t).hour for t in dev)
    parts.append("### When tickets arrive\n\n"
                 + table(["Weekday"] + WEEKDAYS, [["Tickets"] + [days[d] for d in WEEKDAYS]])
                 + f"\n\nBy hour (UTC): every hour has between {min(hours.values())} and {max(hours.values())} tickets.\n")

    rows = []
    for tier, ts in group_by(dev, lambda t: t["customer_tier"]).items():
        rows.append([tier, len(ts), pct(sum(t["history"]["escalated"] for t in ts), len(ts)),
                     pct(sum(t["labels"]["expected_route"] == "escalate" for t in ts), len(ts)),
                     f"{st.median(t['history']['resolution_time_minutes'] for t in ts):.0f}"])
    ent = [t["history"]["resolution_time_minutes"] for t in dev if t["customer_tier"] == "enterprise"]
    bus = [t["history"]["resolution_time_minutes"] for t in dev if t["customer_tier"] == "business"]
    parts.append("### Escalation and waiting by tier\n\n"
                 + table(["Tier", "Tickets", "Historically escalated", "Labelled escalate", "Median resolution (min)"], rows)
                 + f"\n\nEnterprise vs business resolution time: Mann-Whitney p = {mann_whitney_p(ent, bus):.3f}.\n")

    rows = []
    for metric in ["csat_rating", "resolution_time_minutes"]:
        nf = [t["history"][metric] for t in dev if t["language_fluency"] == "non_fluent"]
        fl = [t["history"][metric] for t in dev if t["language_fluency"] == "fluent"]
        rows.append([metric, f"{st.mean(nf):.2f}", f"{st.mean(fl):.2f}", f"{st.median(nf):.0f}", f"{st.median(fl):.0f}",
                     f"{mann_whitney_p(nf, fl):.3f}"])
    parts.append("### Fluent vs non-fluent writers\n\n"
                 + table(["Measure", "Non-fluent mean", "Fluent mean", "Non-fluent median", "Fluent median",
                          "Mann-Whitney p"], rows))
    return "\n".join(parts)


def data_quality(dev: list[dict], val: list[dict], docs: list[dict]) -> str:
    parts = ["## 6. Data quality and constraints (Stage 1, section 5)\n"]
    bodies = group_by(dev, lambda t: norm(t["body"]))
    differing = Counter()
    for ts in bodies.values():
        if len(ts) > 1:
            for key in ["intent", "urgency", "expected_route", "answerable_from_docs", "expected_doc_ids"]:
                if len({json.dumps(t["labels"][key], sort_keys=True) for t in ts}) > 1:
                    differing[key] += 1
    names, tiers = defaultdict(set), defaultdict(set)
    for t in dev:
        names[t["customer_id"]].add(t["customer_name"])
        tiers[t["customer_id"]].add(t["customer_tier"])
    dev_bodies = set(bodies)
    novel = [t for t in val if norm(t["body"]) not in dev_bodies]
    must_not_intents = sorted({t["labels"]["intent"] for t in dev if t["labels"]["must_not_auto_respond"]})
    # applies_to mixes plan limits ("Business and Enterprise plans") with product names ("Managed Database")
    restricted = [d["doc_id"] for d in docs if "Business and Enterprise" in d["applies_to"]]
    std_restricted = sum(1 for t in dev if t["customer_tier"] == "standard"
                         and set(t["labels"]["expected_doc_ids"]) & set(restricted))
    pii = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+|\+?\d[\d\s().-]{8,}\d")
    injection = re.compile(r"ignore (all |the |your )?(previous|prior|above)|system prompt|disregard", re.I)
    rows = [
        ["Distinct ticket texts", f"{len(bodies)} across {len(dev)} tickets"],
        ["Identical texts with differing labels", ", ".join(f"{k}: {v}" for k, v in differing.items()) or "none"],
        ["Customer IDs with more than one name", f"{sum(len(v) > 1 for v in names.values())} of {len(names)}"],
        ["Customer IDs with more than one tier", f"{sum(len(v) > 1 for v in tiers.values())} of {len(tiers)}"],
        ["Intents always marked must-not-auto-respond", ", ".join(must_not_intents)],
        ["Validation tickets whose text appears word for word in development", f"{len(val) - len(novel)} of {len(val)}"],
        ["New validation texts by fluency", ", ".join(f"{k} {v}" for k, v in Counter(t['language_fluency'] for t in novel).items())],
        ["Knowledge-base articles", f"{len(docs)} in {len({d['category'] for d in docs})} categories; last reviewed "
                                    f"{min(d['last_reviewed_days_ago'] for d in docs)}–{max(d['last_reviewed_days_ago'] for d in docs)} days ago"],
        ["Article length (chars)", f"{min(len(d['content']) for d in docs)}–{max(len(d['content']) for d in docs)}"],
        ["Articles for Business and Enterprise plans only", f"{', '.join(restricted)} ({std_restricted} standard-tier tickets rely on one)"],
        ["Tickets containing email addresses or phone numbers", sum(bool(pii.search(t['body'])) for t in dev + val)],
        ["Tickets with prompt-injection wording", sum(bool(injection.search(t['body'])) for t in dev + val)],
        ["Empty ticket bodies", sum(not t['body'].strip() for t in dev + val)],
    ]
    parts.append(table(["Check", "Result"], rows))
    return "\n".join(parts)


def targets(dev: list[dict], val: list[dict]) -> str:
    rows = []
    for name, ts in [("development", dev), ("validation", val)]:
        auto = sum(t["labels"]["expected_route"] == "auto_respond" for t in ts)
        rows.append([name, len(ts), auto, pct(auto, len(ts)), pct(len(ts) - auto, len(ts))])
    return ("## 7. What the labels allow\n\nIf only tickets labelled auto-respond are answered automatically:\n\n"
            + table(["Set", "Tickets", "Labelled auto-respond", "Highest possible first contact resolution",
                     "Lowest possible escalation rate"], rows))


def main(output: Path | None = None) -> int:
    output = output or OUTPUT
    dev, val = load("development_tickets.json"), load("validation_tickets.json")
    docs = load("documentation.json")
    headline_md, summary = headline(dev)
    report = "\n\n".join([
        "# Ticket statistics for discovery",
        f"Generated by `scripts/discovery_stats.py` on {datetime.now():%d %b %Y %H:%M} from the files in `data/`.",
        headline_md, segments(dev), effort(dev), findability(dev), checks(dev), data_quality(dev, val, docs),
        targets(dev, val),
    ]) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print("\n".join(summary))
    try:
        shown = output.relative_to(config.ROOT)
    except ValueError:
        shown = output
    print(f"\nAll tables written to {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
