import cysox as sox


def test_get_effects_globals():
    """Test get_effects_globals function"""
    globals = sox.get_effects_globals()
    assert isinstance(globals, dict)
    assert 'plot' in globals


def test_find_effect():
    """Test find_effect function"""
    # Test finding a known effect
    effect_handler = sox.find_effect('trim')
    assert effect_handler is not None
    assert isinstance(effect_handler, sox.EffectHandler)
    assert effect_handler.name
    assert effect_handler.usage
    assert effect_handler.flags
    assert effect_handler.priv_size
    
    # Test finding a non-existent effect
    effect_info = sox.find_effect('nonexistent_effect')
    assert effect_info is None


# Test EffectHandler class
def test_effect_handler_from_ptr():
    """Test EffectHandler creation from pointer"""
    # This would require a valid sox_effect_handler_t pointer
    # For now, we'll just test that the class exists
    assert hasattr(sox, 'EffectHandler')


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


# # Test Effect class
# def test_effect_creation():
#     """Test Effect creation"""
#     effect = sox.Effect("trim", "0 10")
#     assert effect is not None


# def test_effect_properties():
#     """Test Effect properties"""
#     effect = sox.Effect("trim", "0 10")
    
#     assert effect.name == "trim"
#     assert effect.usage == "0 10"
#     assert isinstance(effect.flags, int)
#     assert effect.priv_size >= 0


# def test_effect_invalid_name():
#     """Test Effect creation with invalid name"""
#     with pytest.raises(MemoryError):
#         sox.Effect("invalid_effect", "params")


# Test EffectsChain class
def test_effects_chain_creation():
    """Test EffectsChain creation"""
    chain = sox.EffectsChain()
    assert chain is not None


# def test_effects_chain_properties():
#     """Test EffectsChain properties"""
#     chain = sox.EffectsChain()
    
#     assert isinstance(chain.effects, list)
#     assert chain.length == 0
#     assert isinstance(chain.global_info, sox.EffectsGlobals)
#     assert chain.in_enc is None
#     assert chain.out_enc is None
#     assert chain.table_size >= 0


# def test_effects_chain_add_effect():
#     """Test EffectsChain add_effect method"""
#     chain = sox.EffectsChain()
#     effect = sox.Effect("trim", "0 10")
    
#     chain.add_effect(effect)
#     assert chain.length == 1
#     assert len(chain.effects) == 1


# def test_effects_chain_workflow():
#     """Test a complete effects chain workflow"""
#     chain = sox.EffectsChain()
    
#     # Add a trim effect
#     trim_effect = sox.Effect("trim", "0 10")
#     chain.add_effect(trim_effect)
    
#     assert chain.length == 1
#     assert len(chain.effects) == 1


# def test_multiple_effects():
#     """Test adding multiple effects to a chain"""
#     chain = sox.EffectsChain()
    
#     # Add multiple effects
#     trim_effect = sox.Effect("trim", "0 10")
#     vol_effect = sox.Effect("vol", "0.5")
    
#     chain.add_effect(trim_effect)
#     chain.add_effect(vol_effect)
    
#     assert chain.length == 2
#     assert len(chain.effects) == 2


# def test_effect_invalid_effect():
#     """Test Effect with invalid effect name"""
#     with pytest.raises(MemoryError):
#         sox.Effect('invalid_effect_name', 'params')


