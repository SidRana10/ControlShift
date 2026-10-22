"""Standard ranked-retrieval metrics over parent chunk IDs.

`relevance` maps chunk_id -> grade (>=1 relevant; 2 = highly relevant). A ranking is a list of
chunk IDs, best first; repeated IDs (e.g. several passages of one chunk) count once, at their
first position. Metrics that need a rank cut-off ignore anything after rank k.
"""
from __future__ import annotations

import math
import random
from collections.abc import Sequence


def dedupe(ranking: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for x in ranking:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _relevant(relevance: dict[str, int]) -> set[str]:
    return {c for c, g in relevance.items() if g >= 1}


def recall_at_k(ranking: Sequence[str], relevance: dict[str, int], k: int) -> float:
    """|relevant retrieved in top-k| / |relevant|."""
    rel = _relevant(relevance)
    if not rel:
        raise ValueError("a query needs at least one relevant chunk")
    return len(rel & set(dedupe(ranking)[:k])) / len(rel)


def hit_rate_at_k(ranking: Sequence[str], relevance: dict[str, int], k: int) -> float:
    return 1.0 if _relevant(relevance) & set(dedupe(ranking)[:k]) else 0.0


def reciprocal_rank_at_k(ranking: Sequence[str], relevance: dict[str, int], k: int) -> float:
    rel = _relevant(relevance)
    for i, c in enumerate(dedupe(ranking)[:k], start=1):
        if c in rel:
            return 1.0 / i
    return 0.0


def ndcg_at_k(ranking: Sequence[str], relevance: dict[str, int], k: int) -> float:
    """DCG@k / ideal DCG@k with gain 2^grade - 1 and discount 1/log2(rank + 1)."""
    if not _relevant(relevance):
        raise ValueError("a query needs at least one relevant chunk")

    def dcg(grades: Sequence[int]) -> float:
        return sum((2 ** g - 1) / math.log2(i + 1) for i, g in enumerate(grades, start=1))

    got = [relevance.get(c, 0) for c in dedupe(ranking)[:k]]
    ideal = sorted((g for g in relevance.values() if g >= 1), reverse=True)[:k]
    return dcg(got) / dcg(ideal)


def version_isolation(versions: Sequence[str], expected: str | None) -> float | None:
    """Fraction of returned results from the requested version (None if no filter was requested).
    An empty result list has nothing out of version and scores 1.0."""
    if expected is None:
        return None
    return 1.0 if not versions else sum(v == expected for v in versions) / len(versions)


def query_metrics(ranking: Sequence[str], relevance: dict[str, int]) -> dict[str, float]:
    return {
        "recall@1": recall_at_k(ranking, relevance, 1),
        "recall@5": recall_at_k(ranking, relevance, 5),
        "recall@10": recall_at_k(ranking, relevance, 10),
        "mrr@10": reciprocal_rank_at_k(ranking, relevance, 10),
        "ndcg@5": ndcg_at_k(ranking, relevance, 5),
        "hit@5": hit_rate_at_k(ranking, relevance, 5),
    }


METRIC_NAMES = ["recall@1", "recall@5", "recall@10", "mrr@10", "ndcg@5", "hit@5"]


def mean(xs: Sequence[float]) -> float:
    if not xs:
        raise ValueError("cannot average an empty list")
    return sum(xs) / len(xs)


def bootstrap_ci(values: Sequence[float], n_boot: int = 2000, seed: int = 0,
                 alpha: float = 0.05) -> tuple[float, float]:
    """Seeded percentile bootstrap CI of the mean over queries."""
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
    return means[int(alpha / 2 * n_boot)], means[int((1 - alpha / 2) * n_boot) - 1]


def paired_bootstrap_ci(a: Sequence[float], b: Sequence[float], n_boot: int = 2000, seed: int = 0,
                        alpha: float = 0.05) -> tuple[float, float]:
    """Seeded percentile CI of mean(a - b) over paired queries."""
    return bootstrap_ci([x - y for x, y in zip(a, b, strict=True)], n_boot, seed, alpha)


def percentile(values: Sequence[float], q: float) -> float:
    """Linear-interpolation percentile (q in [0, 100])."""
    if not values:
        raise ValueError("no values")
    s = sorted(values)
    pos = (len(s) - 1) * q / 100
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)
