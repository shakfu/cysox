from cysox import sox


def test_get_effects_globals():
    """Test get_effects_globals function"""
    globals = sox.get_effects_globals()
    assert isinstance(globals, dict)
    assert "plot" in globals


def test_find_effect():
    """Test find_effect function"""
    # Test finding a known effect
    effect_handler = sox.find_effect("trim")
    assert effect_handler is not None
    assert isinstance(effect_handler, sox.EffectHandler)
    assert effect_handler.name
    assert effect_handler.usage
    assert effect_handler.flags
    assert effect_handler.priv_size

    # Test finding a non-existent effect
    effect_info = sox.find_effect("nonexistent_effect")
    assert effect_info is None


# Test EffectHandler class
def test_effect_handler_from_ptr():
    """Test EffectHandler creation from pointer"""
    # This would require a valid sox_effect_handler_t pointer
    # For now, we'll just test that the class exists
    assert hasattr(sox, "EffectHandler")


# Test EffectsGlobals class
def test_effects_globals_creation():
    """Test EffectsGlobals creation"""
    g = sox.EffectsGlobals()
    assert g is not None


def test_effects_globals_properties():
    """Test EffectsGlobals properties"""
    g = sox.EffectsGlobals()
    assert g.plot == 0
    assert isinstance(g.global_info, sox.Globals)
    assert g.global_info.verbosity == 2
    assert g.global_info.repeatable == 0
    assert g.global_info.bufsiz == 8192


# Test Effect class
def test_effect_creation():
    """Test Effect creation"""
    handler = sox.find_effect("trim")
    effect = sox.Effect(handler)
    assert effect is not None


def test_effect_properties():
    """Test Effect properties"""
    handler = sox.find_effect("trim")
    effect = sox.Effect(handler)

    assert effect.handler.name == "trim"
    assert effect.handler.usage
    assert isinstance(effect.handler.flags, int)
    assert effect.handler.priv_size >= 0


def test_effect_invalid_name():
    """Test Effect creation with invalid name"""
    handler = sox.find_effect("invalid_effect_name")
    assert handler is None


# Test EffectsChain class
def test_effects_chain_creation():
    """Test EffectsChain creation"""
    chain = sox.EffectsChain()
    assert chain is not None


def test_effects_chain_properties():
    """Test EffectsChain properties"""
    chain = sox.EffectsChain()

    assert isinstance(chain.effects, list)
    assert chain.length == 0
    assert isinstance(chain.global_info, sox.EffectsGlobals)
    # in_enc and out_enc can be None if not specified
    assert chain.table_size >= 0
