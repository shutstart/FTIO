# Artifacts Reproducibility

This file describes how to reproduce the experiments in the Paper entitled:
"Capturing Periodic I/O Using Frequency Techniques" which was published at the IPDPS 2024

Before you start, first set up the correct [`ftio` version](#ftio-version).
The experiments are divided into four parts:
- [Artifacts Reproducibility](#artifacts-reproducibility)
	- [FTIO Version](#ftio-version)
	- [1. Running Example and Overhead](#1-running-example-and-overhead)
	- [2. Case Studies](#2-case-studies)
		- [LAMMPS](#lammps)
		- [Nek5000](#nek5000)
		- [Modified HACC-IO](#modified-hacc-io)
	- [3. Limitations of FTIO](#3-limitations-of-ftio)
	- [4. Use Case: I/O Scheduling](#4-use-case-io-scheduling)

## FTIO Version

For all the cases below, `ftio`` first needs to be installed (see [Installation](https://github.com/tuda-parallel/FTIO?tab=readme-ov-file#installation)). We used `ftio` version 0.0.1 for the experiment in the paper. To get this version simply execute the following code:
```sh
git checkout v0.0.1 
```


## 1. Running Example and Overhead
Throughout Section II of the paper "Capturing Periodic I/O Using Frequency Techniques", IOR was used to demonstrate the approach. Moreover, In Section III-C the overhead of our approach was examined using IOR with a varying number of ranks (from 1 to 10752 ranks).
- Follow the instructions provided in the [IOR/README.md](/artifacts/capturing_periodic_io_using_frequency_techniques/IOR/README.md) to setup and run IOR. 
- Instructions regarding the overhead are provided [here](/artifacts/capturing_periodic_io_using_frequency_techniques/IOR/README.md#tracing-library-overhead). 

<p align="right"><a href="#artifacts-reproducibility">⬆</a></p>

## 2. Case Studies
Bellow instructions are provided on how to recreate the case studies from Section III-B. As mentioned [above](#ftio-version), `ftio` version 0.0.1 was used for all examples here. 

### LAMMPS

This experiment was executed on the Lichtenberg cluster with 3072 ranks. 
Follow the instructions provided in the [LAMMPS/README.md](/artifacts/capturing_periodic_io_using_frequency_techniques/LAMMPS/README.md) to reconstruct this experiment. 

<!-- The provided [tar archive](/LAMMPS/lammps.tar.gz) contains not only the result from our -->
<p align="right"><a href="#artifacts-reproducibility">⬆</a></p>


### Nek5000
The trace can be downloaded from [here](https://hpcioanalysis.zdv.uni-mainz.de/trace/64ed13e0f9a07cf8244e45cc).
After downloading, instructions on how to reproduce the results are provided in the [NEK5000/README](/artifacts/capturing_periodic_io_using_frequency_techniques/NEK5000/README.md).

<p align="right"><a href="#artifacts-reproducibility">⬆</a></p>

### Modified HACC-IO
Navigate to [HACC-IO/README](/artifacts/capturing_periodic_io_using_frequency_techniques/HACC-IO/README.md) and follow the provided instructions. 


<p align="right"><a href="#artifacts-reproducibility">⬆</a></p>

## 3. Limitations of FTIO

The details for this experiment are provided here: 
<br>
<https://gitlab.inria.fr/hpc_io/ftio_paper_exps_with_synthetic_traces>

<p align="right"><a href="#artifacts-reproducibility">⬆</a></p>


## 4. Use Case: I/O Scheduling
The details for this experiment are provided here:
<br>
<https://gitlab.inria.fr/hpc_io/iosets-ftio-experiments>

<p align="right"><a href="#artifacts-reproducibility">⬆</a></p>



