# NEXTRON X-100 Model Registry

The Model Registry stores information about every AI model available to
NEXTRON.

## Purpose

The registry allows the NEXTRON Brain to compare models and select the most
appropriate model for a task.

## Model Record

Each model should eventually contain:

- Provider
- Model ID
- Display name
- Supported task types
- Coding score
- Reasoning score
- Vision score
- Image generation score
- Research score
- Speed score
- Reliability score
- Context length
- Cost
- Availability
- Health status

## Example

```text
Model: Example Coding Model
Provider: Example Provider

Capabilities:
- Coding: 95
- Reasoning: 85
- Vision: 20
- Research: 70
- Image Generation: 0

Performance:
- Speed: 85
- Reliability: 90

Status:
- Available