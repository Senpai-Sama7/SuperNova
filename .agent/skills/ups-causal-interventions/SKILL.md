---
name: ups-causal-interventions
description: Causal and interventional prediction focused on estimating effects (P(y|do(x))) and converting them into decisions under uncertainty.
---

# UPS Causal and Interventional Prediction

## Overview

This Skill prevents answering intervention questions with observational predictions. It routes work into causal identification, estimation, uncertainty, and decision-making.

Use when the user asks: what happens if we change X, uplift, treatment effects, experimentation design, or causal inference plans.

## Core capabilities

- Distinguish P(y|x) from P(y|do(x))
- Identification: experiments first; otherwise credible observational strategies
- Estimation: doubly robust patterns (propensity + outcome); heterogeneity via causal forests
- Sensitivity analysis and assumptions made explicit
- Translate effect distributions into expected utility recommendations

## Method

1) Clarify the estimand
   - ATE/ATT for average effects; CATE for personalization.
2) Identify
   - Prefer randomized experiments.
   - If observational, state confounders and adjustment strategy; justify plausibility.
3) Estimate
   - Prefer doubly robust estimators; quantify uncertainty (CI/posterior).
4) Stress-test
   - Placebo checks, negative controls, sensitivity to unmeasured confounding.
5) Decide
   - Convert the effect distribution into an action policy under constraints and risk tolerance.

## Output format

A) Question restated as a causal estimand
B) Identification strategy (experiment vs observational)
C) Estimation plan (models, features, uncertainty)
D) Key assumptions and how to probe them
E) Decision recommendation (expected utility + risk notes)
F) What data would change the conclusion

## Example prompts

- If we lower price 10%, what’s the causal impact on churn?
- Design an experiment to measure onboarding impact on retention.
- We can’t randomize. What’s a credible observational plan?
