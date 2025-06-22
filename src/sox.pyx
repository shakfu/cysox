
cimport sox


def convert(infile, outfile):
    cdef sox_format_t *in_
    cdef sox_format_t *out
    cdef sox_effects_chain_t * chain
    cdef sox_effect_t * e;
    cdef char * args[10]

    assert sox_init() == SOX_SUCCESS

    in_ = sox_open_read(infile.encode(), NULL, NULL, NULL)
    out = sox_open_write(outfile.encode(), &in_.signal, NULL, NULL, NULL, NULL)

    chain = sox_create_effects_chain(&in_.encoding, &out.encoding)

    e = sox_create_effect(sox_find_effect("input"))

    assert sox_effect_options(e, 1, args) == SOX_SUCCESS
    args[0] = <char *>in_

    assert sox_add_effect(chain, e, &in_.signal, &in_.signal) == SOX_SUCCESS
    # free(e)

    ## Create the `vol' effect, and initialise it with the desired parameters: */
    e = sox_create_effect(sox_find_effect("vol"))
    assert sox_effect_options(e, 1, args) == SOX_SUCCESS
    args[0] = "10dB"
    assert sox_add_effect(chain, e, &in_.signal, &in_.signal) == SOX_SUCCESS
    # free(e)

    # Create the `flanger' effect, and initialise it with default parameters: */
    e = sox_create_effect(sox_find_effect("flanger"))
    assert sox_effect_options(e, 0, NULL) == SOX_SUCCESS
    # Add the effect to the end of the effects processing chain: */
    assert sox_add_effect(chain, e, &in_.signal, &in_.signal) == SOX_SUCCESS
    #free(e)

    # The last effect in the effect chain must be something that only consumes
    # samples; in this case, we use the built-in handler that outputs
    # data to an audio file
    e = sox_create_effect(sox_find_effect("output"))
    assert sox_effect_options(e, 1, args) == SOX_SUCCESS
    args[0] = <char *>out
    assert sox_add_effect(chain, e, &in_.signal, &in_.signal) == SOX_SUCCESS
    #free(e)

    sox_flow_effects(chain, NULL, NULL)


    sox_delete_effects_chain(chain)
    sox_close(out)
    sox_close(in_)
    sox_quit()
