# STEP42_WORKSPACE_FACTS

Researcher-side verification; do not append this report to model history.
Only the raw step42 archive was inspected; no task command was executed.
Every last-authored file body matches the checkpoint archive byte for byte.
The mypy configuration matches the complete step1 observation.
The hook remains executable and the marker remains empty.
Fourteen Python source files have authored replacements; __init__.py remains empty.
No git-status result appears in the visible history; staged-state claims are not invented.

| Path | Last authored step | Mode | Bytes | SHA-256 |
|---|---:|---|---:|---|
| .git/HEAD | not authored | 0600 | 23 | f6f2b945f6c411b02ba3da9c7ace88dcf71b6af65ba2e0d89aa82900042b5a10 |
| .git/hooks/pre-commit | 5 | 0700 | 322 | 49f30165ba35da8ba11908a4ace9da7eea09445073891c68352c63bc06d6329e |
| .git/index | not authored | 0600 | 1375 | cfc922c2a8a737c525992b1e2bee0c475779911f544e986d13350ef325bbed00 |
| pyproject.toml | not authored | 0600 | 479 | 6e7d571206536818b52942417eeca8cd0fb5219418bd78d0ef1819671753e69f |
| src/__init__.py | not authored | 0600 | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| src/api_source.py | 36 | 0600 | 3484 | fb71179f339841f2fb24a6a906c124a1f03807ff313b77ee4361859721d34ef2 |
| src/cache.py | 15 | 0600 | 2942 | e71ac9cec30fc9c6e01845b86e582dee2a403bb17162f4d79c601bd2590ae5ab |
| src/cli.py | 39 | 0600 | 7104 | 6b734a8eb3a8d54eed4c3b35c87f2f475d0ddb25bb6d51c856ab85974e371394 |
| src/config.py | 34 | 0600 | 2030 | df5e78f5b5970d034cd6209e07915ad0510d1ab79365248751fa0a13ef2beb53 |
| src/csv_source.py | 17 | 0600 | 3130 | cfc55b8df2c6d6e9846358915327211f9610412f24661585950a69e4550aa340 |
| src/db.py | 19 | 0600 | 3756 | 1c21a9c3b8d1683858fb54bc148f9609b5047fb2db13e715dd98595c9d927d99 |
| src/db_source.py | 32 | 0600 | 3817 | 1d19e8b65dc25d3f64ce245bf5193e35ef547a37af7eaa60be12f7d443254b1d |
| src/logging_setup.py | 29 | 0600 | 2020 | f2cf53bee1654a4e32c2a3cd6fd21efd0f151bc61c1dad9f63a8f1874ef14302 |
| src/metrics.py | 13 | 0600 | 5115 | cf3e1aac46062dff525a0ecec9b179122d0109555de58044ee30e55df7d8bd62 |
| src/models.py | 11 | 0600 | 2873 | 07b454611071f4ad33fa29a5b4c34018abcade39306133b777f8ecc1ae4ad2d3 |
| src/py.typed | not authored | 0600 | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| src/scheduler.py | 27 | 0600 | 3413 | abef1d176a395fa940bf5c91bcb8b83aeeabdf615876f48f1e3f48411866c87e |
| src/transform.py | 25 | 0600 | 4616 | f6f12943811567f39cdd1b4b5b79841d9e28a5831467539bc7369fac35223d54 |
| src/validation.py | 23 | 0600 | 5018 | 005e2ab91167246e26aa169a2a492685793e99bd86667790c06746db2729bd95 |
| src/writer.py | 21 | 0600 | 4918 | 1c5f8bc41f3caf328e275b3eb100edfa5ba38d5c170fcccf88097a53cf86ed95 |

## Targeted ignores still present at step42

| File and line | Exact source line |
|---|---|
| src/cache.py:67 | `class _CachedWrapper(Callable[P, R]):  # type: ignore[misc]` |
| src/cache.py:83 | `return result  # type: ignore[return-value]` |
| src/cache.py:88 | `wrapper.cache = cache  # type: ignore[attr-defined]` |
| src/cache.py:89 | `wrapper.cache_clear = cache.clear  # type: ignore[attr-defined]` |
| src/cache.py:90 | `return wrapper  # type: ignore[return-value]` |
| src/metrics.py:108 | `return _registry[name]  # type: ignore[return-value]` |
| src/metrics.py:116 | `return _registry[name]  # type: ignore[return-value]` |
| src/metrics.py:124 | `return _registry[name]  # type: ignore[return-value]` |

Line numbers and hashes are verification metadata.
The model payload uses only the actual source observations and authored edits.
