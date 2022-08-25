# Allocating computation steps to compute nodes

## Intro

A pipepline is a multi-DAG where each node holds a processor, and edges represent data that
needs to flow from the output of one node to the inputs of another.

We need to allocate each node to a compute instance (e.g. AKS node / pod).

The allocation should

1. work within the allocated compute resources
1. meet the DAG nodes' compute requirements (e.g. GPU)
1. minimize total compute time

This document suggests a formalization of the optimization problem.  This is just a start, and
should evolve to capture more nuiances and to adapt to the solver we would use.

## Formatlization

### Inputs

$G(N, E)$ is a directed-multi-graph, where nodes $N$ hold processors and edges $E$ represent data
dependencies.

$K$ is number of compute instances.

$r(k)$ is the capabilities of compute instance $k \in [K]$.

$r(n)$ is the compute requirements of node $n \in N$.  $r(n) \leq r(k)$ means that compute instance
$k$ supports running node $n$.

$d(n)$ is the (estimated) length of time it takes to run node $n \in N$.

$d(e)$ is the (estimated) length of time it takes to move the data on edge $e \in E$ from one
compute instance to another.

### Assignment of nodes to compute instances

$a(k) = (a_{k,1}, a_{k,2}, ..., a_{k,m_k}); a_{k,m} \in N$ is the assignment of nodes, in
order, to compute instance $k \in [K]$.

$k(n) = (k | n \in a(k))$ is the compute instance $k$ that node $n$ is assigned to.

$m(n) = (m | a_{k(n), m} = n)$ is the position of node $n$ in the order of nodes that are assigned to
the same compute instance.

### Compute requirements constraint

The assignment must meet the compute requirements of the nodes: for all $n$, $r(n) \leq r(k(n))$.

### Start and completion times for each node

$e(n)$ is the completion time of node $n$.  We'll define it soon.

$s_1(n) = 1_{m(n)>1} e(a_{k(n), m(n)-1})$ is the completion time of the previous node assigned to
the same compute instance as $n$, or 0 if $n$ is the first node assigned to the compute instance.

$s_2(n) = max_{(p,n) \in E} (e(p) + 1_{k(n) \neq k(p)} d(p,n))$ is the time the latest input to $n$
is available in the compute instance $n$ is assigned to.

$s(n) = max(s_1(n), s_2(n))$ is the start time for node $n$.

$e(n) = s(n) + d(n)$ is the completion time of node $n$.

$g = max_{n \in N} e(n)$ is the time that last node completes.

### Minimization problem

Find assignments $a$ such that for all $n$, $r(n) \leq r(k(n))$ and $g$ is minimized.
