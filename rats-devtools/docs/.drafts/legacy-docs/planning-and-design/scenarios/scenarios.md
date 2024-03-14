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
   1. calculate $\max_i U_{i,j}$, then threshold.
   1. calculate $\max_i U_{i,j}$, then take top K.
   1. calculate $\max_k \mathrm{robust\_fet} (\{U_{i,j}\}_i, \{L_{i,k}\}_i, \{M_i\}_i)$, then
      threshold.
   1. calculate $\mathrm{robust\_fet} (\{U_{i,j}\}_i, \{L_{i,k}\}_i, \{M_i\}_i)$ for each $k$, take
      top K for each $k$, then union.

1. Train pytorch model, using training and validation datasets.  Single machine.  Monitor training
   as it proceeds. Store trained model.

### Rats key features

* Scatter / gather distributed processing for scale (e.g. parallel FET calculation)
* Future: Use Spark for scale in early stages of preprocessing, then transform to numpy matrices or Pandas dataframes

# Scenario: train and validate P2 models

1. For each of ~200 antigens

1. Filter MIRA data for training & validation using m1a/m2a, other filters.
   MIRA datasets currently behind an API developed by Katie that loads
   either across all diseases or adds disease-specific metadata (e.g. COVID
   genome coordinates)

1. Combine binders, non-binders, and other binders (TCRs that bind other antigens),
   and partition into folds, typically <100k TCRs total

1. Train models & generate predictions using cross-fold validation on generated slices. Compute-intensive - hours of GPU time per antigen.

1. Gather prediction metrics by antigen, either by cross-fold validation or on holdout

*see immunoshare.mira.modeling.p2.data*

### Rats key features

* Multiple inputs and outputs from Processors, with varied schemas
* Distributed processing for training separate models for each antigen
* Scatter/gather to apply P2 prediction model to millions of TCRs in repertoires

# Scenario: train and evaluate P6 models

TBD

# Scenario: TCR-Antigen Co-Clustering (TACC) on HLAdb

1. For each HLA $h$ retrieve set of TCRs $HLAdb_h = \{j\}$ associated with $h$.
   Currently filter to top $k$ TCRs by p-value, currently $k \approx 2000$.

   1. Filter to set of repertoires $\{i\}$ that have HLA $h$.

   1. Create repertoire-TCR indicator matrix $X$

    1. Find top $k$ clusters $cluster_k = \{j\}$ using `sklearn` clustering algorithms e.g. spectral co-clustering,
   Wards clustering, etc.

1. Gather clusters from all HLAs together for analysis.

1. Evaluate clustering results against MIRA data

   - MIRA antigen / taxon purity vs. overlap

1. Evaluate clustering results against ES from diagnostic models for Lyme, COVID, Parvo, etc.

   - Purity vs. overlap

1. Evaluate by using clusters as seeds for pseudolabeling.

1. Evaluate cluster quality by internal metrics, referencing training data

   - Average Spearman Rho (ASR) of TCR feature vectors within or across clusters

### Rats key features

* Multiple inputs and outputs from Processors, with varied schemas

# Scenario: Sparse NMF models for disease diagnostics or TACC

1. Can start with an ExperimentConfig or a set of unlabeled repertoires

1. Select repertoire-TCR feature matrix (e.g. `upr_counts`). Filter to TCRs that occur in at least $k$ repertoires, where $k \approx 5-20$.

1. Apply Pearson residual transform to regularize matrix along both axes. Filter to top $k$ TCRs by variance, where $k \approx 10^5-10^6$ to get feature matrix $X$.

1. Generate HLA mask matrix showing which TCRs have HLA overlap with which repertoires.

   1. Assign HLAs to repertoires using `x_inferred_hlas` or sideloaded RUO HLA assignments,
       yielding binary matrix $RH$.
   1. Compute TCR-HLA association using FET or Mann-Whitney.
   1. Binarize TCR-HLA assocation by p-value threshold or FDR, yielding binary matrix $TH$.
   1. Compute binary mask matrix $M = RH \cdot TH^T > 0$
   1. Filter TCRs to those that are associated with at least one repertoire $F = \{j | \sum_i M_{ij} > 0\}$,
       typically $\approx$ 20k-100k

1. Filter $X$ using $F$.

1. Optimize PyTorch Sparse Projective NMF model to yield component matrix $V \ge 0$
   so that $X \cdot V^T \cdot V \approx X$ subject to mask $M$ and various side constraints
   like regularization, orthogonality, etc.

1. Save component matrix $V$ for downstream applications

1. For disease diagnostics, project processed features $X$ onto components $V$
   and use in regularized logistic regression to predict labels $Y$

1. For TACC

   1. Create TACC clusters from V, e.g. $cluster_k =\{ j | V_{kj} >= \epsilon \}$

   1. Analyze TACC clusters as above.

### Rats key features

* Large-scale matrix operations, e.g. using Dask
* Multiple inputs and outputs from Processors, with varied schemas

# Scenario: train on lots of TCRs

When training sequence models, we'll need 100Ms or 1Gs TCRs.


## Variation 1

Sequence only models, where each sample is a single TCR.

## Variation 2

Sequence model as the initial layers of a repertoire model.  E.g. integrate a sequence model into an AIRIVA model.

## Variation 3

Pre-trained sequence model as the initial layers of a repertoire model.

### Rats key features

* Multi node pytorch training.

# Scenario: Pseudo-labeling

This is an example of an iterative meta-estimator.

## Wraps over

1. Initializer $a$.  Examples:
   1. Take given labels, filter out unlabeled samples.
   1. Assign repertoire labels by mapping MIRA to repertoire TCRs.

1. Internal estimator $e$.  Any process that learns a predictor given labeled samples.

1. Predictions to labels process $l$.

1. Stop criteria $c$.

## Input

Any sampleset with (some) missing labels.  Call it $s$.

## Process

1. $s' = a(s)$
1. Iterate until $c(s, s')$ says stop.
   1. $p = e(f(s'))$ where $f$ is a sampleset filter that returns only labeled samples.
   1. $s' = l(p(s))$
1. Return $p$

Monitor iteration process as it proceeds.

### Rats key features

* Composition of components to enable meta-Processors
* Multiple inputs and outputs from Processors, with varied schemas and types

# Scenario: score any sampleset using any compatible trained model.

Inputs:
* Sampleset
* Trained model

Outputs:
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

### Rats key features

* Composition of components to enable meta-Processors
* Distributed & parallel execution of multiple folds and experiments

## Hyperparameter assignments to explore
Could be fixed, allowing us to know in advance what tasks we will be running

Could be dynamically generated.

Should allow early-stopping.

## Flexible evaluation criteria

What score do we use?

What data do we use (holdout / cross-val)
