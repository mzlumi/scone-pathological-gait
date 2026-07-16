import pytest

from scone_gait.zml import ZmlError, get, parse_zml


def test_key_values_blocks_and_arrays():
    text = """
    GaitPlot {
        title = "Hip angle"   # a comment
        left_channel = hip_flexion_l;/jointset/hip_l/hip_flexion_l/value
        channel_multiply = 57.3
        norm_min = [ 1.0  2.0
                     3.0 ]
        row = 0
    }
    GaitPlot { title = "GRF" }
    """
    block = parse_zml(text)
    assert [k for k, _ in block] == ["GaitPlot", "GaitPlot"]
    hip = block[0][1]
    assert get(hip, "title") == "Hip angle"
    assert get(hip, "left_channel") == "hip_flexion_l;/jointset/hip_l/hip_flexion_l/value"
    assert get(hip, "channel_multiply") == "57.3"
    assert get(hip, "norm_min") == ["1.0", "2.0", "3.0"]
    assert get(block[1][1], "title") == "GRF"
    assert get(hip, "missing", 42) == 42


def test_scone_scenario_syntax():
    text = """
    CmaOptimizer {
        init_file = InitParameters.par
        SimulationObjective {
            OpenSimModel {
                initial_state_offset =	0~0.01<-0.5,0.5>
                initial_state_offset_exclude = "*_tx;*_ty;*_u"
                Properties { soleus_l { max_isometric_force.factor = 0.5 } }
            }
        }
    }
    """
    root = get(parse_zml(text), "CmaOptimizer")
    model = get(get(root, "SimulationObjective"), "OpenSimModel")
    assert get(model, "initial_state_offset") == "0~0.01<-0.5,0.5>"
    assert get(model, "initial_state_offset_exclude") == "*_tx;*_ty;*_u"
    soleus = get(get(model, "Properties"), "soleus_l")
    assert get(soleus, "max_isometric_force.factor") == "0.5"


def test_hash_inside_quotes_is_not_a_comment():
    assert get(parse_zml('title = "a # b"'), "title") == "a # b"


@pytest.mark.parametrize("text", ["a = { b = 1", "a = [ 1 2", "a b", "= 1", "a = }"])
def test_malformed_input_raises(text):
    with pytest.raises(ZmlError):
        parse_zml(text)
