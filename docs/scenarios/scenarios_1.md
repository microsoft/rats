# Scenario: train on lots of samples, 10Ks TCRs

This is an immediate scenario, e.g. for training AIRIVA on many disease labels at once.

## Notation

* $i$ is indexing input repertoires.
* $j$ is indexing input TCRs.
* $k$ is indexing label columns (e.g. diseases, HLAs).
* $U_{i,j}$ is upr count of TCR $j$ in repetoire $i$.
* $L_{i,k}$ is labels.
* $M_i$ is repertoire metadata.

Note: I'm using matrix notation, but that does not mean we need to use matrices or even sequential
indices.

## Process

1. Define training, validation, and holdout samplesets.  Samples are multi-labeled repertoires.  Samplesets contain large fractions of all AMP repertoires.

1. Preprocess, mostly to filter TCRs to the 10K region.  Examples:
1. 1. calculate $\max_i U_{i,j}$, then threshold.
1. 1. calculate $\max_i U_{i,j}$, then take top K.
1. 1. calculate $\max_k \text{robust\_fet} (\{U_{i,j}\}_i, \{L_{i,k}\}_i, \{M_i\}_i)$, then
      threshold.
1. 1. calculate $\text{robust\_fet} (\{U_{i,j}\}_i, \{L_{i,k}\}_i, \{M_i\}_i)$ for each $k$, take
      top K for each $k$, then union.

1. Train pytorch model, using training and validation datasets.  Single machine.  Monitor training
   as it proceeds. Store trained model.

# Scenario: train on lots of TCRs

When training sequence models, we'll need 100Ms or 1Gs TCRs.

We'll need to support multi node pytorch training.

## Variation 1

Sequence only models, where each sample is a single TCR.

## Variation 2

Sequence model as the initial layers of a repertoire model.  E.g. integrate a sequence model into an AIRIVA model.

## Variation 3

Pre-trained sequence model as the initial layers of a repertoire model.

# Scenario: Pseudo-labeling

This is an example of an iterative meta-estimator.

## Wraps over

1. Initializer $a$.  Examples:
1. 1. Take given labels, filter out unlabeled samples.
1. 1. Assign repertoire labels by mapping MIRA to repertoire TCRs.

1. Internal estimator $e$.  Any process that learns a predictor given labeled samples.

1. Predictions to labels process $l$.

1. Stop criteria $c$.

## Input

Any sampleset with (some) missing labels.  Call it $s$.

## Process

1. $s' = a(s)$
1. Iterate until $c(s, s')$ says stop.
1. 1. $p = e(f(s'))$ where $f$ is a sampleset filter that returns only labeled samples.
1. 1. $s' = l(p(s))$
1. Return $p$

Monitor iteration process as it proceeds.

# Scenario: score any sampleset using any compatible trained model.

Inputs:
* Sampleset
* Trained model

Output:
* Predictions

# Scenario: Calculate metrics given scores and labels

Inputs:
* Scores per sample
* Labels per sample
* Metric function
Outputs:
* Metric

# Scenario: Hyperparameter optimization

Should be a generic procedure that can wrap over any training procedure + evaluation criteria.

Should expose the API of a training procedure.

## Hyperparameter assignments to explore
Could be fixed, allowing us to know in advance what tasks we will be running

Could be dynamically generated.

Should allow early-stopping.

## Flexible evaluation criteria

What score do we use?

What data do we use (holdout / cross-val)
