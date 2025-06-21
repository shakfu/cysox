__doc__ = """
>>> output = OEff("output", [])
>>> input = IEff("input", [])
>>> input.get_out_signal().set_param(rate=44100, channels=2, precision=32)
>>> chain = pysox.CEffectsChain()
>>> chain.add_effect(input)
>>> chain.add_effect(output)
>>> chain.flow_effects()
Extern callback 0 0
Extern callback 18 18
-4
4
-3
3
-2
2
-1
1
0
0
1
-1
2
-2
3
-3
4
-4
Extern callback 0 0
0
"""

import pysox
def testcase(cls):
    """helper for runtests.py which tries to pickle the builtin objects"""
    import sys
    def dummy():
        pass
    def fakereduce(self):
        return dummy, [], {}
    def fakesetstate(self, state):
        pass
    cls.__reduce__=fakereduce
    cls.__setstate__=fakesetstate
    return cls

@testcase
class IEff(pysox.CCustomEffect):
    count=1
    def drain(self, buffer_object):
        """create 1.68 seconds of sawtooth on both channels
        using the container interface of the buffer"""
        if 0 == self.count:
            return 0
        self.count -= 1
        l = 9
        for i in range(l):
            buffer_object[i*2]=i-4
            buffer_object[i*2+1]=4-i
        return l*2

@testcase
class OEff(pysox.CCustomEffect):
    def flow(self, ibuf, obuf, isamp):
        """read from ibuf and end the chain by providing 0 output"""
        print("Extern callback %s %s"%( isamp, len(ibuf)))
        for n in ibuf:
            print(n)
        return 0 #0 samples put in obuf, we are end of chain
