# SVD source register

Reviewed 19 September 2026. [input_manifest.json](data/input_manifest.json) records the exact
per-ticker provider URLs, retrieval times, fields, coverage and hashes for the retained Yahoo
Finance adjusted-close snapshots. Numerical returns are decimal daily changes in USD adjusted
closes, representing a revised split/distribution-adjusted proxy, not a point-in-time ledger.
No raw data are newly downloaded for this SVD revision; the separate allocation/regime projects
have a later explicitly refreshed vintage. Their outputs are not independent replications.

- [NumPy SVD documentation](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html): full/reduced shapes and reconstruction conventions; variance uses squared singular values of centered returns.
- [scikit-learn Ledoit–Wolf](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html): the identity-target shrinkage comparator and original 2004 reference.
- [yfinance history API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.history.html): explicit adjusted-close retrieval; provider revisions remain possible.
- [Original public article](https://quhiquhihi.github.io/posts/SVD_and_Portfolio/): educational provenance, reviewed against the maintained derivation rather than treated as performance proof.
- Further primary-method references and exact assumptions are in [the protocol](../docs/research_protocol.md).

Snapshot retrieval timestamps are not original information-availability timestamps. Exact
reproduction needs the pinned permitted cache; no independent second-provider reconciliation
or unrestricted redistribution permission is asserted. Raw inputs remain ignored. Preserved
original illustrations retain their existing attribution; this work adds no blanket license.
