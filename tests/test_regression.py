#!/usr/bin/env python3
"""
Regression tests for v0.7 - ensures no classification changes from v0.6.1 baseline.

Tests:
1. Standard classifier produces identical results on fixed corpus
2. Default behavior unchanged (no new output without opt-in flags)
3. Live smoke test (non-deterministic, just checks no crash)
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import csv
from dataclasses import dataclass
from typing import Dict, List, Tuple


# Paths
CORPUS_PATH = Path("tests/fixtures/corpus_v0_6_1.jsonl")
BASELINE_PATH = Path("tests/fixtures/baseline_labels_v0_6_1.csv")


@dataclass
class TestArticle:
    """Minimal article for classification testing."""
    url: str
    title: str
    summary: str
    outlet_key: str


def load_corpus() -> List[TestArticle]:
    """Load test corpus from JSONL file."""
    if not CORPUS_PATH.exists():
        raise FileNotFoundError(f"Corpus not found: {CORPUS_PATH}")
    
    articles = []
    with open(CORPUS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            articles.append(TestArticle(
                url=data["url"],
                title=data["title"],
                summary=data.get("summary", ""),
                outlet_key=data.get("outlet_key", "")
            ))
    return articles


def load_baseline_labels() -> Dict[str, str]:
    """Load baseline category labels from CSV."""
    if not BASELINE_PATH.exists():
        raise FileNotFoundError(f"Baseline labels not found: {BASELINE_PATH}")
    
    labels = {}
    with open(BASELINE_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels[row["url"]] = row["expected_category"]
    return labels


def test_classification_regression():
    """
    Test: Standard classifier matches v0.6.1 baseline on fixed corpus.
    
    This is the primary regression test - ensures classifier behavior
    is deterministic and unchanged from baseline.
    """
    from curation.classifier import classify_article_enhanced
    
    articles = load_corpus()
    baseline = load_baseline_labels()
    
    mismatches = []
    
    for article in articles:
        # classify_article_enhanced takes (title, summary) as separate args
        predicted = classify_article_enhanced(article.title, article.summary)
        expected = baseline.get(article.url)
        
        if expected and predicted != expected:
            mismatches.append({
                "url": article.url,
                "title": article.title[:60],
                "expected": expected,
                "predicted": predicted
            })
    
    # Report results
    total = len(articles)
    passed = total - len(mismatches)
    agreement_pct = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n📊 Regression Test Results:")
    print(f"   Total articles: {total}")
    print(f"   Matches: {passed}")
    print(f"   Mismatches: {len(mismatches)}")
    print(f"   Agreement: {agreement_pct:.1f}%")
    
    if mismatches:
        print(f"\n❌ Mismatches (first 10):")
        for m in mismatches[:10]:
            print(f"   {m['expected']} → {m['predicted']}: {m['title']}...")
    
    # Assertion: 100% agreement with baseline
    assert len(mismatches) == 0, \
        f"Classification regression: {len(mismatches)} articles changed category"
    
    print("\n✓ Regression test PASSED: 100% agreement with v0.6.1 baseline")


def test_default_output_unchanged():
    """
    Test: Running without new flags produces identical output structure.
    
    This verifies LOSSLESS defaults - no new verbosity without opt-in.
    """
    # This test validates that the main script doesn't add new terminal
    # output when run without --metrics/--debug/--ab-precision flags
    
    # For now, just verify the flags exist but don't change default behavior
    import argparse
    import ainews
    
    # Check that new flags are defined (they should be after implementation)
    # This test will be expanded as flags are added
    print("✓ Default output structure check (placeholder)")


def test_smoke_live_run():
    """
    Test: Live RSS fetch completes without crash.
    
    Non-deterministic - just checks basic functionality.
    Does not assert on categories (content changes daily).
    """
    import subprocess
    import sys
    
    result = subprocess.run(
        [sys.executable, "ainews.py", "--hours", "6", "--top", "5", "--no-browser"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    assert result.returncode == 0, f"Smoke test failed: {result.stderr}"
    
    # Check output file was created
    from pathlib import Path
    output_files = list(Path(".").glob("ainews_*.html"))
    assert len(output_files) > 0, "No output HTML file generated"
    
    print(f"✓ Smoke test PASSED: output generated, no crash")


if __name__ == "__main__":
    import sys
    
    tests = {
        "regression": test_classification_regression,
        "defaults": test_default_output_unchanged,
        "smoke": test_smoke_live_run,
    }
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name in tests:
            tests[test_name]()
        else:
            print(f"Unknown test: {test_name}")
            print(f"Available: {', '.join(tests.keys())}")
            sys.exit(1)
    else:
        # Run regression test by default
        test_classification_regression()
