import math

import cysox as sox


def test_sox_format():
	f = sox.Format('tests/data/s00.wav')
	assert f.signal.channels == 2
	assert f.signal.length == 502840
	assert f.signal.precision == 16
	assert f.signal.rate == 44100.0	

	assert f.encoding.bits_per_sample == 16
	assert f.encoding.compression == math.inf
	assert f.encoding.encoding == 1
	assert sox.ENCODINGS[f.encoding.encoding] == ("SIGN2", "signed linear 2's comp: Mac")
	assert f.encoding.opposite_endian == 0
	assert f.encoding.reverse_bits == 0
	assert f.encoding.reverse_bytes == 0
	assert f.encoding.reverse_nibbles == 0

def test_sox_format_mp3():
	f = sox.Format('tests/data/s00.mp3')
	assert f.signal.channels == 2
	assert f.signal.length == 506798
	assert f.signal.precision == 16
	assert f.signal.rate == 44100.0	

	assert f.encoding.bits_per_sample == 0
	assert f.encoding.compression == math.inf
	assert f.encoding.encoding == 22
	assert sox.ENCODINGS[f.encoding.encoding] == ('MP3', 'MP3 compression')
	assert f.encoding.opposite_endian == 0
	assert f.encoding.reverse_bits == 0
	assert f.encoding.reverse_bytes == 0
	assert f.encoding.reverse_nibbles == 0

