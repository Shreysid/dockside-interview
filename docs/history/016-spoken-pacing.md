# 016 Spoken pacing

## Summary

The interviewer asks for succinct, conversational follow-ups.

## Motivation

Long replies increase generation, synthesis, and playback time. A short question gives the candidate more time to explain their reasoning.

## Design

The model receives a short word target for normal turns and a larger allowance for final feedback. An explicit hint request can receive a brief hint.

## Implementation

The Ollama request sets separate generation budgets for regular and final turns. The prompt asks for plain speech and one focused question.

## Files Changed

- `dockside/interviewer.py`
- `.ai/STATUS.md`
- `.ai/HANDOFF.md`

## Tradeoffs

The model can vary in how closely it follows the word target.

## Future Work

Measure response-time distributions across different problems and recording durations.
