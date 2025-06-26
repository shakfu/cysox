# pysox - python bindings for libsox

## Notes on the Fork

This is the a version of `pysox` by Patrick Atamaniuk, <atamaniuk@frobs.net> and <https://github.com/patrickatamaniuk> which can only be found on pypi <https://pypi.org/project/pysox> and which wraps sox using cython!

This will be modernized first and try to re-use prior work on cysox!

## Installation from source

Required prerequisite are the development libraries of sox at version 14.3.x,
i.e. the header files and libraries to link against.
Specifically you need sox.h in your include path and libsox.so and libsox.a in your link path.
Pysox will not compile against any sox version prior to 14.3.0.

Then simply run::

```sh
python setup.py build

python setup.py install
```


## Usage
See the examples included in the source, or the api doc at http://packages.python.org/pysox/

```python
import pysox

#open an audio file
testwav = pysox.CSoxStream("test.wav")
#create an audio file with the same parameters as the input file
out = pysox.CSoxStream('out.wav', 'w', testwav.get_signal())

#create an effects chain using the signal and encoding parameters of our files
chain = pysox.CEffectsChain(testwav, out)
chain.add_effect(pysox.CEffect("vol",[b'18db']))
chain.flow_effects()
#cleanup
out.close()
```

## Python 3

This package is compatible with python 3, tested on 2.6.6, 2.7.1, 3.0.1, 3.1.3 and 3.2.
It is however not compatible with python 2.5 and prior.

