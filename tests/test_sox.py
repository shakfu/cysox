import sox


def test_sox_convert():
	sox.convert("tests/s00.wav", "tests/s00-out.wav")
	assert True
