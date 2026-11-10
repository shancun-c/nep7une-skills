# Open-source enrichment roadmap

Research date: 2026-11-07. Target baseline:
`6f4ead640728712612b2caccfd20b856ea5879ec`.
The [machine-readable snapshot](upstream-projects.json) records source revisions,
license references, activity, and exact popularity counts. Stars are a rough
adoption signal, not evidence of security or suitability. Repository push dates
can include branch or maintenance activity; they are not release dates.

## Existing capability and duplication check

The repository currently ships three skills: Obsidian Wiki, Knowledge Canvas
Sync, and Server Ops. It is an orchestration/packaging collection, not a running
agent, scheduler, Obsidian plugin, or document conversion service.

- PRs [#1](https://github.com/shancun-c/nep7une-skills/pull/1) through
  [#6](https://github.com/shancun-c/nep7une-skills/pull/6) are merged; no open PR
  was present at research time. Recheck before starting another branch.
- Kepano companions, a reviewed companion baseline, explicit vault preflight,
  and Defuddle webpage routing already exist. Adding them again is not new work.
- QMD already has synthetic generation/verification and sealed-copy experiments.
  Its public QMD execution remains disabled. Do not replace that boundary with
  an upstream quickstart or describe it as production-ready retrieval.
- Canvas already has color validation, guarded replacement, and backups.
- Server Ops already has observe-first SSH/deploy/repair workflows. A new tool
  should supply evidence to those workflows, not take over deployments.
- There is no top-level LICENSE file at this baseline. Choose the repository's
  own distribution license separately before broader redistribution or vendoring.
  An upstream project's license does not choose this repository's license.

## Priority 1: MarkItDown for local source extraction

[Microsoft MarkItDown](https://github.com/microsoft/markitdown) had 194,235 stars;
latest observed release was [v0.1.9, 2026-10-21](https://github.com/microsoft/markitdown/releases/tag/v0.1.9).
The reviewed default branch had a 2026-11-07 commit. Code license: MIT.

**Specific gain:** supply PDF/Office-to-Markdown preprocessing before the existing
source-note ingest. Defuddle stays the public-web extractor; QMD stays retrieval.
This fills a concrete execution gap without introducing another wiki skill.

**Dependencies:** the reviewed tree requires Python >=3.10,<3.15. Core packages
include requests, BeautifulSoup, markdownify, magika, and defusedxml. Format
extras add PDF/Office parsers; use selected extras, not `[all]`. Keep this optional
environment separate from the collection's base Python compatibility.

**Privacy and limitations:** local file APIs still run with process privileges.
The generic API accepts URLs; image captioning, audio transcription, and Azure
features can use web services. Disabled plugins and narrow APIs do not constitute
an OS/network sandbox. Markdown may lose page boundaries, layout, or table meaning.

**Implementation:** first add the
[local document workflow](../skills/obsidian-wiki-skill/references/local-document-ingest.md)
and route selected local documents to it. Next, after checking the actual runtime,
build a separate opt-in adapter with explicit input/output scope, provenance,
resource bounds, no-network enforcement, and fail-closed behavior. Use synthetic
multilingual/table fixtures before any separately authorized real document.

**Acceptance:** actual pinned conversion tests, source/output hashes, quality
comparison against original pages, malformed/oversize inputs, network-denial
tests, and independent Linux/Windows results. None of those integration results
is implied by this documentation-only first phase.

Sources: [README/security](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/README.md),
[dependencies](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/pyproject.toml),
[license](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/LICENSE).

## Priority 1: Gitleaks for publication checks

[Gitleaks](https://github.com/gitleaks/gitleaks) had 30,748 stars;
latest observed release was [v8.30.1, 2026-03-21](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1).
The reviewed default branch had a 2026-10-23 commit. Code license: MIT.

**Specific gain:** add a repeatable secret-detection check to the existing
independent-checkout publication procedure. It supplements manual review and
does not scan the real vault, initialize Git there, or authorize publishing.

**Dependencies:** use a verified platform CLI binary; source builds require Go.
`git` mode additionally uses Git. No Python dependency or always-running service
is needed. Do not automatically install hooks or a GitHub Action.

**Privacy and limitations:** logs/reports may contain secrets and private paths.
Use complete redaction, private output, and a freshly sanitized summary. Review
effective configuration and allowlists. Default exit code 1 covers both findings
and errors; no clean conclusion is possible from that code alone. A clean result
does not prove the absence of secrets or ordinary private information.

**Implementation:** connect the
[optional scan workflow](../skills/obsidian-wiki-skill/references/publication-secret-scan.md)
to the existing staged-diff gate. Later test a bounded invocation on a disposable,
explicit file export; distinguish current-content scans from authorized history
scans, and bind results to unchanged file/configuration hashes.

**Acceptance:** synthetic matching canary, clean case, redaction checks,
config/ignore tampering, history/current-content differences, errors/timeouts,
and no raw report in public artifacts. No credential rotation or history rewrite.

Sources: [CLI and configuration](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/README.md),
[license](https://github.com/gitleaks/gitleaks/blob/5f6ec56cfa6f8c67648d863582c7ae2f206d5c1c/LICENSE).

## Priority 2: lychee for link-health evidence

[lychee](https://github.com/lycheeverse/lychee) had 4,100 stars;
latest observed release was [0.24.2, 2026-05-01](https://github.com/lycheeverse/lychee/releases/tag/lychee-v0.24.2),
with a 2026-11-02 default-branch commit. It offers MIT **or** Apache-2.0 licensing;
the GitHub metadata's single license value does not describe the full choice.

**Gain:** support `audit/lint` with broken Markdown/HTML links. Start with an
explicit file list in offline mode. It does not replace Obsidian wikilink/block
semantics, evidence-quality review, or the Canvas workflow.

**Dependencies/risk:** a Rust CLI; a release binary avoids a local Rust build.
Online checks contact link destinations and may disclose private URLs/query
tokens. Cookies, auth headers, cache, redirects, and private-IP destinations need
review. Offline mode blocks network requests; do not infer that it confines
filesystem access. Use a scoped synthetic copy, not a whole vault. Online checks
need a separately reviewed public-URL allowlist and egress constraints.

**Plan:** prove missing-file/anchor handling on synthetic fixtures; label online
URLs as unchecked when offline. Do not treat a 200 response as a factual source
verification or a 401/429 as conclusive evidence that a link is dead.

Sources: [CLI/offline/privacy options and dual license](https://github.com/lycheeverse/lychee/blob/d119b686aba77707bb4fc2037bdce3eea0ccaee6/README.md).

## Priority 2: Trivy for scoped Server Ops diagnostics

[Trivy](https://github.com/aquasecurity/trivy) had 39,087 stars;
latest observed release was [v0.76.2, 2026-11-05](https://github.com/aquasecurity/trivy/releases/tag/v0.76.2),
with a 2026-11-06 default-branch commit. Code license: Apache-2.0.

**Gain:** provide vulnerability, dependency/SBOM, and IaC findings to `inspect`
and `harden`; retain the existing plan/confirm/change separation.

**Dependencies/risk:** platform CLI plus vulnerability/policy data and caches;
image/registry access can cause network traffic. Inventory, paths, manifests, and
secret-scanner reports may be private. Do not scan the whole host, attach the
Docker socket, access Kubernetes/cloud accounts, or publish SBOMs by default.

**Plan:** begin with an explicitly selected synthetic/local project or exported
image, fixed scanner selection, verified database freshness, and private output.
Report severity and remediation options, never auto-upgrade or restart services.
Before implementation, verify the chosen release's offline/cache flags and
database setup against its versioned docs. That operational verification remains
pending; the README alone is not an offline-operation proof.

Sources: [targets and scanners](https://github.com/aquasecurity/trivy/blob/c22582a1a226379b070041a9e76dcd615c343328/README.md),
[license](https://github.com/aquasecurity/trivy/blob/c22582a1a226379b070041a9e76dcd615c343328/LICENSE).

## Conditional: Docling for difficult documents

[Docling](https://github.com/docling-project/docling) had 70,243 stars;
latest observed release was [v2.148.0, 2026-11-05](https://github.com/docling-project/docling/releases/tag/v2.148.0),
with a 2026-11-06 default-branch commit. Code is MIT; model licenses are separate.

**Gain:** PDF reading order, table structure, OCR, and a richer document model
when a representative MarkItDown sample is inadequate. Do not install both by
default or assume a larger model guarantees more faithful extraction.

**Dependencies/risk:** Python >=3.10; the reviewed project is modular
`docling-slim`, with format, OCR, and model extras. Advanced pipelines may require
substantial model/runtime assets. Local execution is supported, but downloads,
remote pipelines, individual model terms, and resource limits require explicit
selection and verification. Compare outputs on the same synthetic corpus before
adopting it as a fallback. Do not silently switch to cloud OCR on failure.

Sources: [features and license caveat](https://github.com/docling-project/docling/blob/1e26b84c5f5690128ddcd65a20a5d7ffb9e80dcd/README.md),
[modular dependencies](https://github.com/docling-project/docling/blob/1e26b84c5f5690128ddcd65a20a5d7ffb9e80dcd/pyproject.toml).

## Standards reference, not a production dependency

[agentskills/agentskills](https://github.com/agentskills/agentskills) had 27,030
stars and a 2026-11-04 default-branch commit. Use its format specification to
review packaging and progressive disclosure. Code is Apache-2.0; documentation
is CC-BY-4.0. The `skills-ref` package requires Python >=3.11, Click, and StrictYAML
and explicitly describes itself as demonstration-only, not production-ready.
Do not add it as a mandatory installer dependency or treat its validation as
proof of runtime discovery, safety, or semantic correctness.

Sources: [project and license split](https://github.com/agentskills/agentskills/blob/83021e2be457a9b6679148719c1f6074f0ad975e/README.md),
[reference-library caveat](https://github.com/agentskills/agentskills/blob/83021e2be457a9b6679148719c1f6074f0ad975e/skills-ref/README.md),
[dependencies](https://github.com/agentskills/agentskills/blob/83021e2be457a9b6679148719c1f6074f0ad975e/skills-ref/pyproject.toml).

## Delivery phases and review gate

1. **This change:** original optional workflow references, routing links, dated
   upstream research, and structural documentation regressions. No upstream code
   or documentation is copied, no runtime dependency is added, and no program is
   installed. These tests verify packaging/documentation contracts only.
2. **Next isolated experiment:** actual pinned MarkItDown on a synthetic local
   PDF/Office corpus; actual Gitleaks on disposable canaries. Validate privacy
   and failure behavior before producing executable wrappers.
3. **Then:** consider lychee and scoped Trivy based on demonstrated user need.
   Consider Docling only after documenting an extraction-quality gap.

Recheck upstream revisions, release advisories, dependencies, and licenses before
installation or code reuse. If vendoring later becomes justified, preserve the
required notices and record every copied path/revision; model and third-party
dependency licenses need separate review. No popularity metric overrides this.

Keep current installers, required companions, the three skill slugs, and QMD's
default-off boundary unchanged. Avoid concurrent edits to active work. Run the
complete repository regression suite plus any new integration checks against
the exact final revision; disclose missing platforms, skipped tests, and absent
CI rather than calling those checks passed.
