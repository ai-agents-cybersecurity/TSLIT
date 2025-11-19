from tslit.cli import _infer_quantized


def test_infer_quantized_handles_q_prefix_without_flagging():
    assert _infer_quantized("llama3:8b-q4_k_m") is True
    assert _infer_quantized("mixtral:8x7b-int4") is True
    assert _infer_quantized("qwen3:8b-fp16") is False
