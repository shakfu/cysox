0.3.5.alpha.1: 20110410
 * Fix error in manifest

0.3.5.alpha: 20110331
 * calculate outsignal length on the fly to get correct results for unknown length sources (pipes)
 * rework mixer effects to accept Pipe driven input streams, thereby remove MixSockets class
 * add CPysoxPipeStream which accepts multiprocess.Pipe endpoint as input
 * documentation update and corrections

0.3.4.alpha: 20110327
 * internal version of sockets
 * renamed internal c api functions
 	CSignalInfo.get_signal to CSignalInfo.cget_signal, CSignalInfo.cset_signal, CEncodingInfo.cset_encoding
 * deepcopy arguments for CEffect, sox changes arguments while parsing (e.g. compand)

0.3.3.alpha: 20110326
 * make SoxBuffer write access usable, move SoxBuffer from customeffects to sox core

0.3.2.alpha: 20110324
 * regressiontests against multiple python interpreters if installed in /opt/python/%version%/bin/python[3]
 * output flow effect support (example9)
 * fix tobytearray and buffer protocol for SoxBuffer

0.3.1.alpha: 20110324
 * drop src directory

0.3.0.alpha: 20110324
 * Buffer interface and Container interface for Customeffects
 * rename CInputDrain to CCustomEffect, cleanup api
 * unittests and doctests framework

0.2.4.alpha: 20110322
 * Mix and PowerMix input combiner classes
 * python3 compatibility

0.2.3.alpha: 20110321
 * Integrated api documentation
 * check build and example with python 2.7.1

0.2.3.alpha: 20110320
 * include audio editors and conversion in pypi Topic
 * remove debug output
 * add get_signalinfo and get_encodinginfo to signal and encoding classes
 * add example for signalinfo and encodinginfo evaluation (example7-soxi)
 
0.2.2.alpha: 20110320
 * include changelog
 * provide setup without cython
 * document libsox version in setup.py longdescription
