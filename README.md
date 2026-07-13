# inm-rspace

Python tools for interaction with the Rspace Electronic Lab Notebook. Developed at INM - Leibniz Institute for New Materials in Saarbrücken, Germany.

`inm-rspace` adds functionality to the `rspace-client` API to make it easier to include personal scientific data workflows.
The main feature is the `Workflow` class, with which you can wrap arbitrary existing Python code in order to execute it on RSpace documents.


## Installation and Setup

You can install `inm-rspace` through PyPI, which should automatically take care of installing dependencies (especially `rspace-client`). Simply type:

`pip install inm-rspace`

To use the API, you need to first create an API key as explained [here](https://documentation.researchspace.com/article/v0dxtfvj7u-rspace-api-introduction).
As soon as you import `inm-rspace`, it will try to connect to RSpace automatically by checking if you have saved your API key as `RSPACE_API_KEY` along with your RSpace URL as `RSPACE_URL` (e.g. https://leibniz-inm.researchspace.com) as environment variables in your terminal.
If you haven't, you can connect using the included `connect(url, key)` method instead.
For convenience, it is recommended to use the environment variables.
For app development, it is recommended to use Python's `keyring` package to manage API keys instead to avoid saving secrets in plain text.



## Documentation and Examples

To learn how to generally use the `rspace-client` API, please refer to the official [examples](https://github.com/rspace-os/rspace-client-python/tree/master/examples).

As for how to use the `inm-rspace` extension for workflows, check the `examples` folder of this repository.
The full API documentation is available [here](https://sintharic.github.io/inm-rspace/).