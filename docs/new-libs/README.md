# MARL Mathematical Foundations Library

This folder is a local reading library for the mathematical foundations named
in the supplied MARL report. The corpus was curated for the HMASD objective of
supporting a variable agent count `N` or a variable skill period `k`.

## Contents

- `papers/`: 27 verified PDFs (about 49 MiB). The repository-wide `*.pdf`
  rule keeps these files local-only.
- [corpus/README.md](corpus/README.md): LLM-oriented, page-traceable corpus
  with topic/method/evidence/HMASD-axis navigation, typed claims, compact local
  search, per-paper overviews, and page-aligned chunks.
- [LIBRARY_INDEX.md](LIBRARY_INDEX.md): verified bibliography, source links,
  version notes, HMASD relevance, and claim boundaries.
- [references.bib](references.bib): BibTeX for the downloaded corpus and the
  important metadata-only books.

Every local PDF passed all of the following checks on 2026-08-12:

1. the file begins with a PDF signature;
2. the complete page tree can be parsed;
3. text extracted from page 1 matches the intended title and authors; and
4. page 1 renders visibly without corruption.

The collection uses publisher, proceedings, institutional-repository, author,
or arXiv copies. Public download and third-party redistribution are different
permissions, so the PDFs remain local rather than being committed. In
particular, the Shoham--Leyton-Brown manuscript asks readers to obtain their
own copy from the official site.

## Recommended reading order

1. `B01`--`B03`, `P01`: game models, solution concepts, learning objectives,
   and Dec-POMDP information structure.
2. `P19`, `P02`, `P03`, `P13`: stochastic learning rates, Markov potential
   games, large-player independent learning, and entropy regularization.
3. `P04`, `P05`, `P06`, `P07`: rotational dynamics, variational inequalities,
   extrapolation, and stochastic variance reduction.
4. `P08`--`P14`, `P20`--`P25`: mean-field, finite-`N` approximation, Graphon
   heterogeneity, fictitious play, and function-approximation sample complexity.
5. `P15`--`P18`: information bottlenecks, KL trust regions, mutual-information
   exploration, and optimal-transport hypotheses.

For question-driven retrieval instead of sequential reading, start from the
[corpus navigation table](corpus/README.md#best-entry-point-by-question).

## Project-level boundary

Several sources provide mechanisms or asymptotic motivation for variable
`N`, but none proves that one frozen HMASD policy generalizes to a held-out
roster size or survives within-episode churn. None directly studies a variable
skill period `k`. MAVEN (`P17`) is only an indirect temporal-abstraction bridge:
its latent persists for a fixed episode rather than learning or adapting a
skill duration.
