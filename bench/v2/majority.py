"""The majority rule of the benchmark's correctness checks (tripletrail-bench#96), for answers
that compare as equal or not (a row count, a one-row value): the answer a strict majority of the
engines gave, and at least two of them, is taken as right. One engine alone is never right by
default, TripleTrail included. compare.py applies the same rule to spatial answers, with
tolerances.
"""


def wrong(answers):
    """answers: {engine: hashable answer} -> the engines whose answer differs from the majority
    answer; empty when all agree or when there is no majority (nothing says who is right)."""
    vals = list(answers.values())
    if len(set(vals)) <= 1:
        return set()
    top = max(sorted(set(vals), key=repr), key=vals.count)
    if vals.count(top) < 2 or vals.count(top) * 2 <= len(vals):
        return set()
    return {e for e, v in answers.items() if v != top}


def sparqloscope_failed(r):
    """A Sparqloscope query record whose run failed or timed out."""
    return isinstance(r.get("results"), str) and r["results"].startswith("Exception")


def sparqloscope_answer(r):
    """What Sparqloscope's answers are compared on: the row count, and for a one-row answer
    (COUNT, SUM, MIN, ...) its values, numbers rounded to 10 significant digits (engines print
    decimals with different precision). The first row of a longer answer is not compared: the
    order of a LIMIT without ORDER BY is up to the engine."""
    n = r.get("result_size")
    if n != 1:
        return n, ""
    rows = r.get("results", [])
    out = []
    for v in (rows[0] if rows else []):
        try:
            out.append(f"{float(v):.10g}")
        except (TypeError, ValueError):
            out.append(str(v))
    return n, str(out)
