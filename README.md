<!-- # FTIO -->
![GitHub Release](https://img.shields.io/github/v/release/tuda-parallel/FTIO)
![GitHub Release Date](https://img.shields.io/github/release-date/tuda-parallel/FTIO)
![](https://img.shields.io/github/last-commit/tuda-parallel/FTIO)
![contributors](https://img.shields.io/github/contributors/tuda-parallel/FTIO)
![issues](https://img.shields.io/github/issues/tuda-parallel/FTIO)
![](https://img.shields.io/github/languages/code-size/tuda-parallel/FTIO)
![](https://img.shields.io/github/languages/top/tuda-parallel/FTIO)
![license][license.bedge]
[![Upload Python Package](https://img.shields.io/github/actions/workflow/status/tuda-parallel/FTIO/python-publish.yml)](https://github.com/tuda-parallel/FTIO/actions/workflows/python-publish.yml)
[![Python Package](https://img.shields.io/pypi/status/ftio-hpc)](https://pypi.org/project/ftio-hpc/)



<br />
<div align="center">
  <h1 align="center">FTIO</h1>
  <p align="center">
 <h3 align="center"> Frequency Techniques for I/O </h2>
    <!-- <br /> -->
    <a href="https://github.com/tuda-parallel/FTIO/tree/main/docs/approach.md"><strong>Explore the approach »</strong></a>
    <br />
    <!-- <br /> -->
    <a href="#testing">View Demo</a>
    ·
    <a href="https://github.com/tuda-parallel/FTIO/issues">Report Bug</a>
    ·
    <a href="https://github.com/tuda-parallel/FTIO/issues">Request Feature</a>
  </p>
</div>

FTIO captures periodic I/O using frequency techniques.
Many high-performance computing (HPC) applications perform their I/O in bursts following a periodic pattern.
Predicting such patterns can be very efficient for I/O contention avoidance strategies, including burst buffer management, for example.
FTIO allows [*offline* detection](/docs/approach.md#offline-detection) and [*online* prediction](/docs/approach.md#online-prediction) of periodic I/O phases.
FTIO uses the discrete Fourier transform (DFT), combined with outlier detection methods to extract the dominant frequency in the signal.
Additional metrics gauge the confidence in the output and tell how far from being periodic the signal is.
A complete description of the approach is provided [here](https://github.com/tuda-parallel/FTIO/tree/main/docs/approach.md).

This repository provides two main Python-based tools:

- [`ftio`](/docs/approach.md#offline-detection):  uses frequency techniques and outlier detection methods to find the period of I/O phases 
- [`predictor`](/docs/approach.md#online-prediction): implements the online version of FTIO. It reinvokes FTIO whenever new traces are appended to the monitored file. See [online prediction](/docs/approach.md#online-prediction) for more details. We recommend using [TMIO](https://github.com/tuda-parallel/TMIO) to generate the file with the I/O traces.

Other tools:

- [`ioplot`](https://github.com/tuda-parallel/FTIO/tree/main/docs/tools.md#ioplot) generates interactive plots in HTML
- [`ioparse`](https://github.com/tuda-parallel/FTIO/tree/main/docs/tools.md#ioparse) parses and merges several traces to an [Extra-P](https://github.com/extra-p/extrap) supported format. This allows one to examine the scaling behavior of the monitored metrics. Traces generated by FTIO (frequency modls), [TMIO](https://github.com/tuda-parallel/TMIO) (msgpack, json and jsonl) and other tools (Darshan, Recorder, and TAU Metric Proxy) are supported.

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#installation">Installation</a>
      <ul>
        <li><a href="#automated-installation">Automated installation</a></li>
        <li><a href="#manual-installation">Manual installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
 	<li><a href="#testing">Testing</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
 <li><a href="#citation">Citation</a></li>
 <li><a href="#publications">Publications</a></li>
  </ol>
</details>

Join the [Slack channel](https://join.slack.com/t/ftioworkspace/shared_invite/zt-2bydqdt13-~hIHzIrKW2zJY_ZWJ5oE_g) or see the latest updates here: [Latest News](https://github.com/tuda-parallel/FTIO/tree/main/ChangeLog.md)

## Installation

FTIO is available on PYPI and can be easily installed via pip:
```sh
pip install ftio-hpc
```

For the latest GitHub version, FTIO can be installed either [automatically](#automated-installation) or [manually](#manual-installation). As a prerequisite,
for the virtual environment, `python3.11-venv` is needed, which can be installed on Ubuntu, for example, with:
```sh
apt install python3.11-venv
```

### Automated installation

Simply call the make command:

```sh
make install
```

This generates a virtual environment in the current directory, sources `.venv/bin/activate`, and installs FTIO as a module.

If you don't need a dedicated environment, just call:

```sh
make ftio PYTHON=python3
```

### Manual installation

Create a virtual environment if needed and activate it:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install all tools provided in this repository simply by using pip:

```sh
pip install .
```

Note: you need to activate the environment to use `ftio` and the other tools using:

```sh
source path/to/venv/bin/activate
```

<p align="right"><a href="#ftio">⬆</a></p>

## Usage

For installation instructions see [installation](#installation).

To call `ftio` on a single file, use:

```sh
ftio filename.extension
```

Supported extensions are `json`, `jsonLines`, `msgpack`, and `darshan`. For recorder, you provide the path to the folder instead of `filename.extension`. For more on the input format including a [custom format](/docs/file_formats.md#custom-file-format) see [supported file formats](/docs/file_formats.md#file-formats-and-tools).

FTIO provides various options and extensions. To see all available command line arguments, call:

```
ftio -h

  
usage: ftio [-h] [-m MODE] [-r RENDER] [-f FREQ] [-ts TS] [-te TE] [-tr TRANSFORMATION] [-e ENGINE]
            [-o OUTLIER] [-le LEVEL] [-t TOL] [-d] [-nd] [-re] [--no-reconstruction] [-p] [-np] [-c] [-w]
            [-fh FREQUENCY_HITS] [-v] [-s] [-ns] [-a] [-na] [-i] [-ni] [-x DXT_MODE] [-l LIMIT]
            files [files ...]
```

`ftio` generates frequency predictions. There are several options available to enhance the predictions. In the standard mode, the DFT is used in combination with an outlier detection method. Additionally, autocorrelation can be used to further increase the confidence in the results:

1. DFT + outlier detection (Z-score, DB-Scan, Isolation forest, peak detection, or LOF)​
2. Optionally: Autocorrelation + Peak detection (`-c` flag)
3. If step 2. is performed, the results from both predictions aer merged automatically

Several flags can be specified. The most relevant settings are:

| Flag                        | Description|
|---                          | --- |
|file                         | file, file list (file 0 ... file n), folder, or folder list (folder 0.. folder n) containing traces  (positional argument)|
|-h, --help                   | show this help message and exit|
|-m MODE, --mode MODE         | if the trace file contains several I/O modes, a specific mode can be selected. Supported modes are: async_write, async_read, sync_write, sync_read|
|-r RENDER, --render RENDER   | specifies how the plots are rendered. Either dynamic (default) or static|
|-f FREQ, --freq FREQ         | specifies the sampling rate with which the continuous signal is discretized (default=10Hz). This directly affects the highest captured frequency (Nyquist). The value is specified in Hz. In case this value is set to -1, the auto mode is launched which sets the sampling frequency automatically to the smallest change in the bandwidth detected. Note that the lowest allowed frequency in the auto mode is 2000 Hz|
|-ts TS, --ts TS              | Modifies the start time of the examined time window
|-te TE, --te TE              | Modifies the end time of the examined time window
|-tr TRANSFORMATION, --transformation TRANSFORMATION| specifies the frequency technique to use. Supported modes are: dft (default), wave_disc, and wave_cont|
|-e ENGINE, --engine ENGINE   | specifies the engine used to display the figures. Either plotly (default) or mathplotlib can be used. Plotly is used to generate interactive plots as HTML files. Set this value to no if you do not want to generate plots
|-o OUTLIER, --outlier OUTLIER| outlier detection method: Z-score (default), DB-Scan, Isolation_forest, or LOF|
|-le LEVEL, --level LEVEL     | specifies the decomposition level for the discrete wavelet transformation (default=3). If specified as auto, the maximum decomposition level is automatic calculated |
|-t TOL, --tol TOL            | tolerance value|
|-d, --dtw                    | performs dynamic time wrapping on the top 3 frequencies (highest contribution) calculated using the DFT if set (default=False) |
|-re, --reconstruction        | plots reconstruction of top 10 signals on figure |
|-np, --no-psd                | if set, replace the power density spectrum (a*a/N) with the amplitude spectrum (a) |
|-c, --autocorrelation        | if set, autocorrelation is calculated in addition to DFT. The results are merged to a single prediction at the end |
|-w, --window_adaptation      | online time window adaptation. If set to true, the time window is shifted on X hits to X times the previous phases from the current instance. X corresponds to frequency_hits|
|-fh FREQUENCY_HITS, --frequency_hits FREQUENCY_HITS |  specifies the number of hits needed to adapt the time window. A hit occurs once a dominant frequency is found|
|-v, --verbose                | sets verbose on or off (default=False)|
|-x DXT_MODE, --dxt_mode DXT_MODE| select data to extract from Darshan traces (DXT_POSIX or DXT_MPIIO (default)) |
|-l LIMIT, --limit LIMIT         | max ranks to consider when reading a folder |

`predictor` has the same syntax as `ftio`.
All arguments that are available for `ftio` are also available for `predictor`.

<p align="right"><a href="#ftio">⬆</a></p>

## Testing

There is a `8.jsonl` file provided for testing under [examples](https://github.com/tuda-parallel/FTIO/examples). On your system, navigate to the folder and  call:

```sh
ftio 8.jsonl
```

<p align="right"><a href="#ftio">⬆</a></p>

<!-- CONTRIBUTING -->
## Contributing

If you have a suggestion that would make this better, please fork the repository and create a pull request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

<p align="right"><a href="#ftio">⬆</a></p>

<!-- CONTACT -->
## Contact

[![][parallel.bedge]][parallel_website]

- Ahmad Tarraf: <ahmad.tarraf@tu-darmstadt.de>

<p align="right"><a href="#ftio">⬆</a></p>

## License

![license][license.bedge]

Distributed under the BSD 3-Clause License. See [LISCENCE](./LICENSE) for more information.
<p align="right"><a href="#ftio">⬆</a></p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

Authors:

- Ahmad Tarraf

This work is a result of cooperation between the Technical University of Darmstadt and INRIA in scope of the [EuroHPC ADMIRE project](https://admire-eurohpc.eu/).

<p align="right"><a href="#ftio">⬆</a></p>

## Citation

```
 @inproceedings{Tarraf_Bandet_Boito_Pallez_Wolf_2024, 
  author={Tarraf, Ahmad and Bandet, Alexis and Boito, Francieli and Pallez, Guillaume and Wolf, Felix},
  title={Capturing Periodic I/O Using Frequency Techniques}, 
  booktitle={2024 IEEE International Parallel and Distributed Processing Symposium (IPDPS)}, 
  address={San Francisco, CA, USA}, 
  year={2024},
  month=may, 
  pages={1–14}, 
  notes = {(accepted)}
 }
```

<p align="right"><a href="#ftio">⬆</a></p>

## Publications

1. A. Tarraf, A. Bandet, F. Boito, G. Pallez, and F. Wolf, “Capturing Periodic I/O Using Frequency Techniques,” in 2024 IEEE International Parallel and Distributed Processing Symposium (IPDPS), San Francisco, CA, USA, May 2024, pp. 1–14.

2. A. Tarraf, A. Bandet, F. Boito, G. Pallez, and F. Wolf, “FTIO: Detecting I/O periodicity using frequency techniques.” arXiv preprint arXiv:2306.08601 (2023).

<p align="right"><a href="#ftio">⬆</a></p>


<!-- https://img.shields.io/badge/any_text-you_like-blue -->

<!--* Badges *-->
[license.bedge]: https://img.shields.io/badge/License-BSD_3--Clause-blue.svg
[parallel_website]: https://www.parallel.informatik.tu-darmstadt.de/laboratory/team/tarraf/tarraf.html
[parallel.bedge]: https://img.shields.io/badge/Parallel_Programming:-Ahmad_Tarraf-blue

<!--* links *-->