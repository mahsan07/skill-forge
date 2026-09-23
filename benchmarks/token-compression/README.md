# Token Compression Benchmark

This benchmark extends Skill Forge's Hermes-style task-adaptive harness instead of creating a second benchmark framework.

## Goal

Compare token/context compressors on identical fixtures while enforcing one rule:

> A smaller result is not a successful result if critical information disappeared.

The runner treats compressors as external adapters. It does not vendor or imitate Caveman, context-compress, Compressoor, or another project's algorithm. Results therefore describe the tool actually installed on the machine running the benchmark.

## What is measured

Each run records:

- bytes before and after
- provider-neutral estimated token units before and after
- estimated reduction percentage
- exact critical facts preserved or missing
- latency
- process success
- whether the result expanded instead of compressed

The token estimate is deliberately simple: four UTF-8 bytes per comparison unit. It is useful for consistent before/after comparisons but is **not** an OpenAI, Anthropic, or other provider billing token count.

## Fixtures

`fixtures.json` includes four representative workloads:

1. persistent project/handoff context
2. verbose git history
3. failing test output
4. a precision-sensitive assistant response

The first fixture intentionally contains the phrase `owner/tool`. This guards against the over-compression failure previously observed when prose was misclassified as a path.

## Run the control

```bash
skill-forge benchmark-tokens \
  --fixtures benchmarks/token-compression/fixtures.json \
  --adapters benchmarks/token-compression/adapters.example.json
```

Only the identity control is enabled in the example file so a clean checkout remains deterministic.

## Test real compressors

Copy the adapter file:

```bash
cp benchmarks/token-compression/adapters.example.json \
   benchmarks/token-compression/adapters.local.json
```

Install the compressor you want to test, edit its command/path, set `"enabled": true`, then run:

```bash
skill-forge benchmark-tokens \
  --fixtures benchmarks/token-compression/fixtures.json \
  --adapters benchmarks/token-compression/adapters.local.json \
  --output token-compression-results.json
```

### context-compress

The example invokes the installed CLI directly in balanced or aggressive mode and supplies each fixture's original source command through `{source_command}`.

### Compressoor

Point the adapter at the upstream `compact_prompt.py` script. The benchmark will fail any fixture where a required fact is lost, even if the reduction percentage is very high.

### Caveman Compress

Point the file-rewrite adapter at Caveman's upstream compression CLI. Skill Forge copies each fixture into a temporary file first, so the benchmark never rewrites the source fixture.

### Caveman output skill

Caveman's response skill is an agent instruction, not a deterministic stdin compressor. Test it through the same harness by providing a small local wrapper that:

1. sends the fixture text to the chosen agent/model with the installed Caveman skill enabled;
2. writes only the model response to stdout;
3. exits non-zero on agent/provider failure.

Configure that wrapper as a `stdin_command` adapter. This keeps the benchmark honest: the result comes from the real installed skill and real model rather than a local imitation.

## Pass criteria

A run passes when:

- the adapter exits successfully; and
- every fixture `must_contain` fact survives exactly.

Compression percentage is reported separately. A 99% reduction that deletes a required constraint is a failure.

See `harness/token-compression-manifest.json` for the JIT-style module and verification contract.
