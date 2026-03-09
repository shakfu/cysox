# Cython declarations for KissFFT (real-valued FFT only)
# KissFFT is compiled with kiss_fft_scalar=double

cdef extern from "kiss_fft.h" nogil:
    ctypedef double kiss_fft_scalar

    ctypedef struct kiss_fft_cpx:
        kiss_fft_scalar r
        kiss_fft_scalar i

    ctypedef struct kiss_fft_state
    ctypedef kiss_fft_state* kiss_fft_cfg

    void kiss_fft_free "KISS_FFT_FREE" (void* ptr)


cdef extern from "kiss_fftr.h" nogil:
    ctypedef struct kiss_fftr_state
    ctypedef kiss_fftr_state* kiss_fftr_cfg

    kiss_fftr_cfg kiss_fftr_alloc(int nfft, int inverse_fft,
                                  void* mem, size_t* lenmem)
    void kiss_fftr(kiss_fftr_cfg cfg, const kiss_fft_scalar* timedata,
                   kiss_fft_cpx* freqdata)
