#
# Python objects wrapping the c implementation
#
# $Id: sox.pyx 10 2011-03-20 09:20:13Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
cimport pysox.csox as csox

ctypedef struct pysoxtransportheader_t:
    char magic[4]
    csox.sox_signalinfo_t signalinfo

#
# interface for pyx implementation
#
cdef char * toCharP(uobj)

cdef class CEffect:
    cdef int argc
    cdef char ** argv
    cdef csox.sox_effect_t *effect
    cdef name
    cpdef get_name(self)
    cdef csox.sox_effect_t * get_effect(self)
    cdef create(self, name, arguments)

cdef class CSignalInfo:
    cdef csox.sox_signalinfo_t * signal
    cdef csox.sox_signalinfo_t s_signal
    cdef cset_signal(self, csox.sox_signalinfo_t * signal)
    cdef csox.sox_signalinfo_t * cget_signal(self)

cdef class CEncodingInfo:
    cdef csox.sox_encodinginfo_t * encoding
    cdef csox.sox_encodinginfo_t  s_encoding
    cdef cset_encoding(self, csox.sox_encodinginfo_t * encoding)
    cdef csox.sox_encodinginfo_t * cget_encoding(self)

cdef class CSoxStream:
    cdef csox.sox_format_t * ft
    
    cdef csox.sox_format_t * get_ft(self)
    cdef char * asCharP(self)
    cdef int sox_read(self, csox.sox_sample_t * obuf, size_t rlen)
    cdef int sox_read_wide(self, csox.sox_sample_t * obuf, size_t max)
    cpdef int open_read(self, path, CSignalInfo signalInfo=?, CEncodingInfo encodingInfo=?, fileType=?) except ?0
    cpdef open_write(self, path, CSignalInfo signalInfo, CEncodingInfo encodingInfo=?, fileType=?)
    cdef csox.sox_signalinfo_t * cget_signal(self)
    cdef csox.sox_encodinginfo_t * cget_encoding(self)

cdef class CPysoxPipeStream(CSoxStream):
    cdef object channel
    cdef object initialdata
    cdef int receive_header(self)

cdef class SoxSampleBuffer:
    cdef object format, offset
    cdef csox.sox_sample_t * buffer
    cdef int len #total length of memory in bytes
    cdef int datalen #total length of valid memory in bytes (for iteration and export)
    cdef int itemsize
    cdef int ndim #number of dimensions
    cdef Py_ssize_t* strides
    cdef Py_ssize_t* shape
    cdef Py_ssize_t* suboffsets
    cdef readonly object recieved_flags, release_ok
    cdef bint must_dealloc_buffer, read_only
    cdef int viewcount
    
    cdef void set_buffer(self, csox.sox_sample_t* buffer, size_t lsamp)
    cdef int __create_buffer(self, data) except -1
    cdef void __do_dealloc_if(self)
    cdef int write(self, csox.sox_sample_t* buf, object value) except -1
    cdef get_default_format(self)
    cdef Py_ssize_t* list_to_sizebuf(self, l)

