# inm-rspace

Python tools for interaction with the Rspace Electronic Lab Notebook. Developed at INM - Leibniz Institute for New Materials in Saarbrücken, Germany.

`inm-rspace` adds functionality to the `rspace-client` API to make it easier to include personal scientific data workflows.
The main feature is the `Workflow` class, with which you can wrap arbitrary existing Python code in order to execute it on RSpace documents.


## Installation and Setup

You can install `inm-rspace` through PyPI, which should automatically take care of installing dependencies (especially `rspace-client`). Simply type:

`pip install inm-rspace`

However, to use the API, you need to first create an API key as explained [here](https://documentation.researchspace.com/article/v0dxtfvj7u-rspace-api-introduction).
Furthermore, `inm-rspace` assumes you have saved this API key as `RSPACE_API_KEY` along with your RSpace URL as `RSPACE_URL` (e.g. https://leibniz-inm.researchspace.com) as environment variables in your terminal.


## Examples

To learn how to generally use the `rspace-client` API, please refer to their [examples](https://github.com/rspace-os/rspace-client-python/tree/master/examples).

As for how to use the `inm-rspace` extension for workflows, check the `examples` folder of this repository.


## Documentation

The full API documentation is still in progress, but the current state is already available [here](https://sintharic.github.io/inm-rspace/).