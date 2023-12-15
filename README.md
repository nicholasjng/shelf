# `shelf` - a lightweight Python artefact store client

## What is it?

`shelf` combines the [pytree registry](https://jax.readthedocs.io/en/latest/pytrees.html) from JAX with the [fsspec](https://filesystem-spec.readthedocs.io/en/latest/index.html) project.

Similarly to what you do in JAX, registering a pair of serialization and deserialization callbacks allows you to easily save your custom Python types as files _anywhere_ fsspec can reach!

## A ⚡️- quick demo

Here's how you register a custom neural network type that uses [pickle](https://docs.python.org/3/library/pickle.html) to store trained models on disk.

```python
# my_model.py
import numpy as np
import pickle
import shelf


class MyModel:
    def __call__(self):
        return 42
    
    def train(self, data: np.ndarray):
        pass
    
    def score(self, data: np.ndarray):
        return 1.


def save_to_disk(model: MyModel) -> str:
    """Dumps the model to disk using `pickle`."""
    fname = "my-model.pkl"
    with open(fname, "wb") as f:
        pickle.dump(model, f)
    return fname


def load_from_disk(fname: str) -> MyModel:
    """Reloads the previously pickled model."""
    with open(fname, "rb") as f:
        model: MyModel = pickle.load(f)
        return model


shelf.register_type(MyModel, save_to_disk, load_from_disk)
```

Now, for example in your training loop, save the model to anywhere using a `Shelf`:

```python
import numpy as np
from shelf import Shelf

from my_model import MyModel


def train():
    # Initialize a `Shelf` to handle remote I/O.
    shelf = Shelf()
    
    model = MyModel()
    data = np.random.randn(100)

    # Train your model...
    for epoch in range(10):
        model.train(data)
    
    # and save it to S3...
    shelf.put(model, "s3://my-bucket/my-model.pkl")
    # ... or GCS if you prefer...
    shelf.put(model, "gs://my-bucket/my-model.pkl")
    # ... or Azure!
    shelf.put(model, "az://my-blob/my-model.pkl")
```

Conversely, if you want to reinstantiate a remotely stored model:

```python
def score():
    model: MyModel = shelf.get("s3://my-bucket/my-model.pkl", MyModel)
    accuracy = model.score(np.random.randn(100))
    
    print(f"And here's how accurately it predicts: {accuracy:.2%}")
```

And just like that, push and pull your custom models and data artifacts anywhere you like - your service of choice just has to have a supporting `fsspec` [filesystem implementation](https://github.com/fsspec/filesystem_spec/blob/master/fsspec/registry.py) available.

## Installation

⚠️ `shelf` is an experimental project - expect bugs and sharp edges.

Install it directly from source, for example either using `pip` or `poetry`:

```shell
pip install git+https://github.com/nicholasjng/shelf.git
# or
poetry add git+https://github.com/nicholasjng/shelf.git
```

A PyPI package release is planned for the future.
