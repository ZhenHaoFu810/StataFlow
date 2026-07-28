# ADR-0006: Command-Aware Result Display

## Status

Accepted for StataFlow 1.3.0.

## Context

`ResultSchema.summary()` originally used one generic text template. It could
show coefficients and a few common statistics, but it could not reliably
represent fixed-effects, IV, GLM, DID, or RD command-specific information.
Some useful values were attached dynamically or stored in private fields,
which also meant they did not survive JSON serialization.

## Decision

StataFlow uses a renderer-neutral `DisplayDocument` between result data and
output:

1. Command-family adapters select applicable fields and sections.
2. A width-aware text renderer produces terminal output.
3. An escaped HTML renderer produces notebook output from the same document.

The display follows Stata's field vocabulary and information hierarchy, but
does not promise character-for-character replication. Inapplicable fields are
omitted rather than filled with invented values.

`display()` and `summary()` default to full output with 95% confidence
intervals. `detail="compact"` keeps the model header, coefficient table, and
core fit statistics. Existing positional `width` and `show_ci` arguments
remain valid. Only `style="stata"` is currently supported.

Command-specific metadata is stored in typed `IVInfo`, `DIDInfo`, and `RDInfo`
structures and is included in JSON serialization. New fields have defaults so
1.2-era JSON remains readable.

## Consequences

- Text and HTML cannot drift in field selection or numeric formatting.
- Users no longer need private fields or manual formatting for a complete
  single-model result.
- The default output is intentionally more complete than in 1.2.0.
- Multi-model comparison and LaTeX, Markdown, Excel, or colored terminal
  output remain outside this ADR.
