"""TransNetV2's Conv3d layers rewritten as Conv2d give the same output."""
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("scenedetect")
nn = torch.nn

from silentshorts.pipeline.scene_detection import conv3d_as_conv2d  # noqa: E402


def _net():
    torch.manual_seed(0)
    return nn.Sequential(
        nn.Conv3d(3, 8, kernel_size=(1, 3, 3), padding=(0, 1, 1), bias=False),
        nn.Conv3d(8, 4, kernel_size=(3, 1, 1), dilation=(4, 1, 1), padding=(4, 0, 0)),
        nn.Conv3d(4, 4, kernel_size=3, padding=1),  # not separable: kept as is
    ).eval()


def test_rewrite_matches_conv3d_and_keeps_other_layers():
    x = torch.rand(2, 3, 20, 9, 16)
    ref = _net()
    with torch.no_grad():
        want = ref(x)
        got_net = conv3d_as_conv2d(_net())
        got = got_net(x)
    kinds = [type(m).__name__ for m in got_net]
    assert kinds == ["Spatial", "Temporal", "Conv3d"]
    assert got.shape == want.shape
    assert torch.allclose(got, want, atol=1e-5)


def test_real_model_predictions_unchanged():
    tn = pytest.importorskip("transnetv2_pytorch")
    import numpy as np
    model = tn.TransNetV2(device="cpu").eval()
    frames = torch.from_numpy(np.random.default_rng(1).integers(
        0, 255, (1, 100, 27, 48, 3), dtype=np.uint8))
    with torch.no_grad():
        want = model(frames)[0]
        got = conv3d_as_conv2d(model)(frames)[0]
    assert not any(isinstance(m, nn.Conv3d) for m in model.modules())
    assert torch.allclose(got, want, atol=1e-4)
