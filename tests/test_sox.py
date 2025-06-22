import sox


def test_sox_convert():

	sox.convert("s00.wav", "s00-out.wav")
