<div align="center">

<h1>SREGym: A Benchmarking Platform for SRE Agents</h1>

[Overview](#🤖overview) | 
[🚀Quick Start](#🚀quickstart) |
[📦Installation](#📦installation) |
[⚙️Usage](#⚙️usage) |
[🤝Contributing](./CONTRIBUTING.md) |
[![Slack](https://img.shields.io/badge/-Slack-4A154B?style=flat-square&logo=slack&logoColor=white)](https://join.slack.com/t/SREGym/shared_invite/zt-3gvqxpkpc-RvCUcyBEMvzvXaQS9KtS_w)
</div>

<h2 id="overview">🤖 Overview</h2>

SREGym is a unified platform to enable the design, development, and evaluation of AI agents for Site Reliability Engineering (SRE). The core idea is to create live system environments for SRE agents to solve real-world problems.

SREGym also provides a comprehensive SRE benchmark suite with a wide variety of problems for evaluating SRE agents and for training next-generation AI agents.

![SREGym Architecture Figure](./assets/SREGymFigure.png)

### SRE Problems
Problems in SREGym consist of three components: an application, a fault, and an oracle. When evaluating a problem, SREGym first deploys the application specified in the problem. After deployment, the fault is injected into the system to cause the incident. Then, SREGym begins evaluating the agent and uses the oracle as the ground truth for the problem’s solution.
<!-- TODO, merge sentences, shouldn't have just a couple sentences on their own. -->
<!-- We should clarify our advantages and why it's unique compared to AIOpsLab and ITBench,
we should articulate it in the first paragraph -->

<!-- Figure note: We list some of the applications, we should list some of the faults as well in the figure/ -->
<!-- Remove the numbers, and the stuff in the legend -->
<!-- Take the problem set out, not as necessary for the figure -->
<!-- Have a big amount of space for the problem definition -->
<!-- Use a black background for the figure -->

<!-- SRE Problems is too specific, we should aim to sell here We should show our features -->
![alt text](image.png)
See our [registry](https://sregym.com/problems/problem-repertoire/head) for a complete list of problems.

SREGym is built to be extensible, we always welcome new contributions. See [CONTRIBUTING](./CONTRIBUTING.md) to get started.

<h2 id="📦installation">📦 Installation</h2>

### Requirements
- Python >= 3.12
- [Helm](https://helm.sh/)
- [brew](https://docs.brew.sh/Homebrew-and-Python)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [uv](https://github.com/astral-sh/uv)
- [kind](https://kind.sigs.k8s.io/) (if running locally)

### Recommendations
- [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) to test MCP tools.
- [k9s](https://k9scli.io/) to observe the cluster.

```bash
git clone --recurse-submodules https://github.com/SREGym/SREGym
cd SREGym
uv sync
uv run pre-commit install
```

<h2 id="🚀quickstart">🚀 Quickstart</h2>

## Setup your cluster
Choose either a) or b) to set up your cluster and then proceed to the next steps.

### a) Kubernetes Cluster (Recommended)
SREGym supports any kubernetes cluster that your `kubectl` context is set to, whether it's a cluster from a cloud provider or one you build yourself. 

We have an Ansible playbook to setup clusters on providers like [CloudLab](https://www.cloudlab.us/) and our own machines. Follow this [README](./scripts/ansible/README.md) to set up your own cluster.

### b) Emulated cluster
SREGym can be run on an emulated cluster using [kind](https://kind.sigs.k8s.io/) on your local machine. However, not all problems are supported.

```bash
# For x86 machines
kind create cluster --config kind/kind-config-x86.yaml

# For ARM machines
kind create cluster --config kind/kind-config-arm.yaml
```

<h2 id="⚙️usage">⚙️ Usage</h2>

### Running an Agent

#### Quick Start

To get started with the included Stratus agent:

1. Create your `.env` file:
```bash
mv .env.example .env
```

2. Open the `.env` file and configure your model and API key.

3. Run the benchmark:
```bash
python main.py
```

### Monitoring with Dashboard

SREGym provides a dashboard to monitor the status of your evaluation. The dashboard runs automatically when you start the benchmark with `python main.py` and can be accessed at `http://localhost:11451` in your web browser.

## Acknowledgements
This project is generously supported by a Slingshot grant from the [Laude Institute](https://www.laude.org/).

## License
Licensed under the [MIT](LICENSE.txt) license.
