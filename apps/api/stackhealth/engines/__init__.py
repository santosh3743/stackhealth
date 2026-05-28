"""Scanning engines.

Each engine is a small module exposing a `run(workdir: Path, ...) -> EngineResult`
function. They are intentionally independent so they can run in parallel and
fail individually without taking the whole scan down.

Spec: docs/03-SCORING-METHODOLOGY.md, docs/04-ARCHITECTURE.md
"""
