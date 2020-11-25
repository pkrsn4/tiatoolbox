from tiatoolbox.dataloader import wsireader
from tiatoolbox import utils
from tiatoolbox import cli

import pytest
from pytest import approx
import pathlib
import numpy as np
import cv2
from click.testing import CliRunner

# -------------------------------------------------------------------------------------
# Utility Test Functions
# -------------------------------------------------------------------------------------


def strictly_increasing(seq):
    """Return True if sequence is strictly increasing.

    Args:
        seq: Sequence to check.

    Returns:
        bool: True if strictly increasing.
    """
    return all(a < b for a, b in zip(seq, seq[1:]))


def strictly_decreasing(seq):
    """Return True if sequence is strictly decreasing.

    Args:
        seq: Sequence to check.


    Returns:
        bool: True if strictly decreasing.
    """
    return all(a > b for a, b in zip(seq, seq[1:]))


# -------------------------------------------------------------------------------------
# Utility Test Classes
# -------------------------------------------------------------------------------------


class DummyMutableOpenSlideObject:
    """Dummy OpenSlide object with mutable properties."""

    def __init__(self, openslide_obj) -> None:
        self.openslide_obj = openslide_obj
        self._properties = dict(openslide_obj.properties)

    def __getattr__(self, name: str):
        return getattr(self.openslide_obj, name)

    @property
    def properties(self):
        """Return the fake properties."""
        return self._properties


# -------------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------------


def test_wsireader_slide_info(_sample_svs, tmp_path):
    """Test for slide_info in WSIReader class as a python function."""
    file_types = ("*.svs",)
    files_all = utils.misc.grab_files_from_dir(
        input_path=str(pathlib.Path(_sample_svs).parent), file_types=file_types,
    )
    wsi = wsireader.OpenSlideWSIReader(files_all[0])
    slide_param = wsi.info
    out_path = tmp_path / slide_param.file_path.with_suffix(".yaml").name
    utils.misc.save_yaml(slide_param.as_dict(), out_path)


def test__relative_level_scales_openslide_baseline(_sample_ndpi):
    """Test openslide relative level scales for pixels per baseline pixel."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    level_scales = wsi._relative_level_scales(0.125, "baseline")
    level_scales = np.array(level_scales)
    downsamples = np.array(wsi.info.level_downsamples)
    expected = downsamples * 0.125
    assert strictly_increasing(level_scales[:, 0])
    assert strictly_increasing(level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], expected)


def test__relative_level_scales_jp2_baseline(_sample_jp2):
    """Test jp2 relative level scales for pixels per baseline pixel."""
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    level_scales = wsi._relative_level_scales(0.125, "baseline")
    level_scales = np.array(level_scales)
    downsamples = np.array(wsi.info.level_downsamples)
    expected = downsamples * 0.125
    assert strictly_increasing(level_scales[:, 0])
    assert strictly_increasing(level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], expected)


def test__relative_level_scales_openslide_mpp(_sample_ndpi):
    """Test openslide calculation of relative level scales for mpp."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    level_scales = wsi._relative_level_scales(0.5, "mpp")
    level_scales = np.array(level_scales)
    assert strictly_increasing(level_scales[:, 0])
    assert strictly_increasing(level_scales[:, 1])
    assert all(level_scales[0] == wsi.info.mpp / 0.5)


def test__relative_level_scales_jp2_mpp(_sample_jp2):
    """Test jp2 calculation of relative level scales for mpp."""
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    level_scales = wsi._relative_level_scales(0.5, "mpp")
    level_scales = np.array(level_scales)
    assert strictly_increasing(level_scales[:, 0])
    assert strictly_increasing(level_scales[:, 1])
    assert all(level_scales[0] == wsi.info.mpp / 0.5)


def test__relative_level_scales_openslide_power(_sample_ndpi):
    """Test openslide calculation of relative level scales for objective power."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    level_scales = wsi._relative_level_scales(wsi.info.objective_power, "power")
    level_scales = np.array(level_scales)
    assert strictly_increasing(level_scales[:, 0])
    assert strictly_increasing(level_scales[:, 1])
    assert np.array_equal(level_scales[0], [1, 1])
    downsamples = np.array(wsi.info.level_downsamples)
    assert np.array_equal(level_scales[:, 0], level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], downsamples)


def test__relative_level_scales_jp2_power(_sample_jp2):
    """Test jp2 calculation of relative level scales for objective power."""
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    level_scales = wsi._relative_level_scales(wsi.info.objective_power, "power")
    level_scales = np.array(level_scales)
    assert strictly_increasing(level_scales[:, 0])
    assert strictly_increasing(level_scales[:, 1])
    assert np.array_equal(level_scales[0], [1, 1])
    downsamples = np.array(wsi.info.level_downsamples)
    assert np.array_equal(level_scales[:, 0], level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], downsamples)


def test__relative_level_scales_openslide_level(_sample_ndpi):
    """Test openslide calculation of relative level scales for level."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    level_scales = wsi._relative_level_scales(3, "level")
    level_scales = np.array(level_scales)
    assert np.array_equal(level_scales[3], [1, 1])
    downsamples = np.array(wsi.info.level_downsamples)
    expected = downsamples / downsamples[3]
    assert np.array_equal(level_scales[:, 0], level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], expected)


def test__relative_level_scales_jp2_level(_sample_jp2):
    """Test jp2 calculation of relative level scales for level."""
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    level_scales = wsi._relative_level_scales(3, "level")
    level_scales = np.array(level_scales)
    assert np.array_equal(level_scales[3], [1, 1])
    downsamples = np.array(wsi.info.level_downsamples)
    expected = downsamples / downsamples[3]
    assert np.array_equal(level_scales[:, 0], level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], expected)


def test__relative_level_scales_openslide_level_float(_sample_ndpi):
    """Test openslide calculation of relative level scales for fracitonal level."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    level_scales = wsi._relative_level_scales(1.5, "level")
    level_scales = np.array(level_scales)
    assert level_scales[0] == approx([1 / 3, 1 / 3])
    downsamples = np.array(wsi.info.level_downsamples)
    expected = downsamples / downsamples[0] * (1 / 3)
    assert np.array_equal(level_scales[:, 0], level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], expected)


def test__relative_level_scales_jp2_level_float(_sample_jp2):
    """Test jp2 calculation of relative level scales for fracitonal level."""
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    level_scales = wsi._relative_level_scales(1.5, "level")
    level_scales = np.array(level_scales)
    assert level_scales[0] == approx([1 / 3, 1 / 3])
    downsamples = np.array(wsi.info.level_downsamples)
    expected = downsamples / downsamples[0] * (1 / 3)
    assert np.array_equal(level_scales[:, 0], level_scales[:, 1])
    assert np.array_equal(level_scales[:, 0], expected)


def test__relative_level_scales_invalid_units(_sample_svs):
    """Test _relative_level_scales with invalid units."""
    wsi = wsireader.OpenSlideWSIReader(_sample_svs)
    with pytest.raises(ValueError):
        wsi._relative_level_scales(1.0, "gibberish")


def test__relative_level_scales_no_mpp():
    """Test _relative_level_scales objective when mpp is None."""

    class DummyWSI:
        _relative_level_scales = wsireader.WSIReader._relative_level_scales

        @property
        def info(self):
            return wsireader.WSIMeta((100, 100))

    wsi = DummyWSI()
    with pytest.raises(ValueError):
        wsi._relative_level_scales(1.0, "mpp")


def test__relative_level_scales_no_objective_power():
    """Test _relative_level_scales objective when objective power is None."""

    class DummyWSI:
        _relative_level_scales = wsireader.WSIReader._relative_level_scales

        @property
        def info(self):
            return wsireader.WSIMeta((100, 100))

    wsi = DummyWSI()
    with pytest.raises(ValueError):
        wsi._relative_level_scales(10, "power")


def test__relative_level_scales_level_too_high(_sample_svs):
    """Test _relative_level_scales levels set too high."""
    wsi = wsireader.OpenSlideWSIReader(_sample_svs)
    with pytest.raises(ValueError):
        wsi._relative_level_scales(100, "level")


def test_find_optimal_level_and_downsample_openslide_interpolation_warning(
    _sample_ndpi,
):
    """Test finding optimal level for mpp read with scale > 1.

    This tests the case where the scale is found to be > 1 and interpolation
    will be applied to the output. A UserWarning should be raised in this case.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    with pytest.warns(UserWarning):
        _, _ = wsi._find_optimal_level_and_downsample(0.1, "mpp")


def test_find_optimal_level_and_downsample_jp2_interpolation_warning(_sample_jp2):
    """Test finding optimal level for mpp read with scale > 1.

    This tests the case where the scale is found to be > 1 and interpolation
    will be applied to the output. A UserWarning should be raised in this case.
    """
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    with pytest.warns(UserWarning):
        _, _ = wsi._find_optimal_level_and_downsample(0.1, "mpp")


def test_find_optimal_level_and_downsample_mpp(_sample_ndpi):
    """Test finding optimal level for mpp read."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)

    mpps = [0.5, 10]
    expected_levels = [0, 4]
    expected_scales = [[0.91282519, 0.91012514], [0.73026016, 0.72810011]]

    for mpp, expected_level, expected_scale in zip(
        mpps, expected_levels, expected_scales
    ):
        read_level, post_read_scale_factor = wsi._find_optimal_level_and_downsample(
            mpp, "mpp"
        )

        assert read_level == expected_level
        assert post_read_scale_factor == approx(expected_scale)


def test_find_optimal_level_and_downsample_power(_sample_ndpi):
    """Test finding optimal level for objective power read."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)

    objective_powers = [20, 10, 5, 2.5, 1.25]
    expected_levels = [0, 1, 2, 3, 4]
    for objective_power, expected_level in zip(objective_powers, expected_levels):
        read_level, post_read_scale_factor = wsi._find_optimal_level_and_downsample(
            objective_power, "power"
        )

        assert read_level == expected_level
        assert np.array_equal(post_read_scale_factor, [1.0, 1.0])


def test_find_optimal_level_and_downsample_level(_sample_ndpi):
    """Test finding optimal level for level read."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)

    for level in range(wsi.info.level_count):
        read_level, post_read_scale_factor = wsi._find_optimal_level_and_downsample(
            level, "level"
        )

        assert read_level == level
        assert np.array_equal(post_read_scale_factor, [1.0, 1.0])


def test_find_read_rect_params_power(_sample_ndpi):
    """Test finding read rect parameters for objective power."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)

    location = (0, 0)
    size = (256, 256)
    # Test a range of objective powers
    for target_scale in [1.25, 2.5, 5, 10, 20]:
        (level, _, read_size, post_read_scale, _) = wsi._find_read_rect_params(
            location=location, size=size, resolution=target_scale, units="power",
        )
        assert level >= 0
        assert level < wsi.info.level_count
        # Check that read_size * scale == size
        post_read_downscaled_size = np.round(read_size * post_read_scale).astype(int)
        assert np.array_equal(post_read_downscaled_size, np.array(size))


def test_find_read_rect_params_mpp(_sample_ndpi):
    """Test finding read rect parameters for objective mpp."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)

    location = (0, 0)
    size = (256, 256)
    # Test a range of MPP
    for target_scale in range(1, 10):
        (level, _, read_size, post_read_scale, _) = wsi._find_read_rect_params(
            location=location, size=size, resolution=target_scale, units="mpp",
        )
        assert level >= 0
        assert level < wsi.info.level_count
        # Check that read_size * scale == size
        post_read_downscaled_size = np.round(read_size * post_read_scale).astype(int)
        assert np.array_equal(post_read_downscaled_size, np.array(size))


def test_read_rect_openslide_baseline(_sample_ndpi):
    """Test openslide read rect at baseline.

    Location coordinate is in baseline (level 0) reference frame.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    location = (1000, 2000)
    size = (1000, 1000)
    im_region = wsi.read_rect(location, size, resolution=0, units="level")

    assert isinstance(im_region, np.ndarray)
    assert im_region.dtype == "uint8"
    assert im_region.shape == (1000, 1000, 3)


def test_read_rect_jp2_baseline(_sample_jp2):
    """Test jp2 read rect at baseline.

    Location coordinate is in baseline (level 0) reference frame.
    """
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    location = (1000, 2000)
    size = (1000, 1000)
    im_region = wsi.read_rect(location, size, resolution=0, units="level")

    assert isinstance(im_region, np.ndarray)
    assert im_region.dtype == "uint8"
    assert im_region.shape == (1000, 1000, 3)


def test_read_rect_openslide_levels(_sample_ndpi):
    """Test openslide read rect with resolution in levels.

    Location coordinate is in baseline (level 0) reference frame.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    location = (1000, 2000)
    size = (256, 256)
    for level in range(wsi.info.level_count):
        im_region = wsi.read_rect(location, size, resolution=level, units="level")

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        assert im_region.shape == (256, 256, 3)


def test_read_rect_jp2_levels(_sample_jp2):
    """Test jp2 read rect with resolution in levels.

    Location coordinate is in baseline (level 0) reference frame.
    """
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    location = (1000, 2000)
    size = (256, 256)
    for level in range(wsi.info.level_count):
        level_width, level_height = wsi.info.level_dimensions[level]
        im_region = wsi.read_rect(location, size, resolution=level, units="level")

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        assert im_region.shape == (min(256, level_height), min(256, level_width), 3)


def test_read_rect_openslide_mpp(_sample_ndpi):
    """Test openslide read rect with resolution in microns per pixel.

    Location coordinate is in baseline (level 0) reference frame.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    location = (1000, 2000)
    size = (256, 256)
    for factor in range(1, 10):
        mpp = wsi.info.mpp * factor
        im_region = wsi.read_rect(location, size, resolution=mpp, units="mpp")

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        assert im_region.shape == (256, 256, 3)


def test_read_rect_jp2_mpp(_sample_jp2):
    """Test jp2 read rect with resolution in microns per pixel.

    Location coordinate is in baseline (level 0) reference frame.
    """
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    location = (1000, 2000)
    size = (256, 256)
    for factor in range(1, 10):
        mpp = wsi.info.mpp * factor
        im_region = wsi.read_rect(location, size, resolution=mpp, units="mpp")

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        assert im_region.shape == (256, 256, 3)


def test_read_rect_openslide_objective_power(_sample_ndpi):
    """Test openslide read rect with resolution in objective power.

    Location coordinate is in baseline (level 0) reference frame.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    location = (0, 0)
    size = (256, 256)
    for objective_power in [20, 10, 5, 2.5, 1.25]:
        im_region = wsi.read_rect(
            location, size, resolution=objective_power, units="power"
        )

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        assert im_region.shape == (256, 256, 3)


def test_read_rect_jp2_objective_power(_sample_jp2):
    """Test jp2 read rect with resolution in objective power.

    Location coordinate is in baseline (level 0) reference frame.
    """
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    location = (0, 0)
    size = (256, 256)
    for objective_power in [20, 10, 5, 2.5, 1.25]:
        im_region = wsi.read_rect(
            location, size, resolution=objective_power, units="mpp"
        )

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        assert im_region.shape == (256, 256, 3)


def test_read_bounds_openslide_baseline(_sample_ndpi):
    """Test openslide read bounds at baseline.

    Coordinates in baseline (level 0) reference frame.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    bounds = (1000, 2000, 2000, 3000)
    im_region = wsi.read_bounds(bounds, resolution=0, units="level")

    assert isinstance(im_region, np.ndarray)
    assert im_region.dtype == "uint8"
    assert im_region.shape == (1000, 1000, 3)


def test_read_bounds_jp2_baseline(_sample_jp2):
    """Test jp2 read bounds at baseline.

    Coordinates in baseline (level 0) reference frame.
    """
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    bounds = (1000, 2000, 2000, 3000)
    im_region = wsi.read_bounds(bounds, resolution=0, units="level")

    assert isinstance(im_region, np.ndarray)
    assert im_region.dtype == "uint8"
    assert im_region.shape == (1000, 1000, 3)


def test_read_bounds_openslide_levels(_sample_ndpi):
    """Test openslide read bounds with resolution in levels.

    Coordinates in baseline (level 0) reference frame.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    bounds = (1000, 2000, 2000, 3000)
    for level, downsample in enumerate(wsi.info.level_downsamples):
        im_region = wsi.read_bounds(bounds, resolution=level, units="level")

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        expected_output_shape = tuple(
            np.round([1000 / downsample, 1000 / downsample, 3]).astype(int)
        )
        assert im_region.shape == expected_output_shape


def test_read_bounds_jp2_levels(_sample_jp2):
    """Test jp2 read bounds with resolution in levels.

    Coordinates in baseline (level 0) reference frame.
    """
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    bounds = (1000, 2000, 2000, 3000)
    for level, downsample in enumerate(wsi.info.level_downsamples):
        im_region = wsi.read_bounds(bounds, resolution=level, units="level")

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        expected_output_shape = tuple(np.round([1000 / downsample, 1000 / downsample]))
        assert im_region.shape[:2] == approx(expected_output_shape, abs=1)
        assert im_region.shape[2] == 3


def test_read_bounds_openslide_mpp(_sample_ndpi):
    """Test openslide read bounds with resolution in microns per pixel.

    Coordinates in baseline (level 0) reference frame.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    bounds = (1000, 2000, 2000, 3000)
    slide_mpp = wsi.info.mpp
    for factor in range(1, 10):
        mpp = slide_mpp * factor
        downsample = mpp / slide_mpp

        im_region = wsi.read_bounds(bounds, resolution=mpp, units="mpp")

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        expected_output_shape = tuple(
            np.round((np.array([1000] * 2) / downsample)).astype(int)
        )
        assert im_region.shape[:2] == expected_output_shape
        assert im_region.shape[2] == 3


def test_read_bounds_jp2_mpp(_sample_jp2):
    """Test jp2 read bounds with resolution in microns per pixel.

    Coordinates in baseline (level 0) reference frame.
    """
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    bounds = (1000, 2000, 2000, 3000)
    slide_mpp = wsi.info.mpp
    for factor in range(1, 10):
        mpp = slide_mpp * factor
        downsample = mpp / slide_mpp

        im_region = wsi.read_bounds(bounds, resolution=mpp, units="mpp")

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        expected_output_shape = tuple(
            np.round((np.array([1000] * 2) / downsample)).astype(int)
        )
        assert im_region.shape[:2] == approx(expected_output_shape, abs=1)
        assert im_region.shape[2] == 3


def test_read_bounds_openslide_objective_power(_sample_ndpi):
    """Test openslide read bounds with resolution in objective power.

    Coordinates in baseline (level 0) reference frame.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    bounds = (1000, 2000, 2000, 3000)
    slide_power = wsi.info.objective_power
    for objective_power in [20, 10, 5, 2.5, 1.25]:
        downsample = slide_power / objective_power

        im_region = wsi.read_bounds(bounds, resolution=objective_power, units="power",)

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        expected_output_shape = tuple(
            np.round((np.array([1000] * 2) / downsample)).astype(int)
        )
        assert im_region.shape[:2] == expected_output_shape
        assert im_region.shape[2] == 3


def test_read_bounds_interpolated(_sample_svs):
    """Test openslide read bounds with interpolated output.

    Coordinates in baseline (level 0) reference frame.
    """
    wsi = wsireader.OpenSlideWSIReader(_sample_svs)
    bounds = (0, 0, 500, 500)
    im_region = wsi.read_bounds(bounds, resolution=0.1, units="mpp",)

    assert 0.1 < wsi.info.mpp[0]
    assert 0.1 < wsi.info.mpp[1]
    assert isinstance(im_region, np.ndarray)
    assert im_region.dtype == "uint8"
    assert im_region.shape[2] == 3
    assert all(np.array(im_region.shape[:2]) > 500)


def test_read_bounds_jp2_objective_power(_sample_jp2):
    """Test jp2 read bounds with resolution in objective power.

    Coordinates in baseline (level 0) reference frame.
    """
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    bounds = (1000, 2000, 2000, 3000)
    slide_power = wsi.info.objective_power
    for objective_power in [20, 10, 5, 2.5, 1.25]:
        downsample = slide_power / objective_power

        im_region = wsi.read_bounds(bounds, resolution=objective_power, units="power",)

        assert isinstance(im_region, np.ndarray)
        assert im_region.dtype == "uint8"
        expected_output_shape = tuple(
            np.round((np.array([1000] * 2) / downsample)).astype(int)
        )
        assert im_region.shape[:2] == approx(expected_output_shape[:2], abs=1)
        assert im_region.shape[2] == 3


def test_read_bounds_level_consistency_openslide(_sample_ndpi):
    """Test read_bounds produces the same visual field across resolution levels."""
    wsi = wsireader.OpenSlideWSIReader(_sample_ndpi)
    bounds = (30400, 11810, 30912, 12322)
    imgs = [wsi.read_bounds(bounds, power, "power") for power in [60, 40, 20, 10]]
    smallest_size = imgs[-1].shape[:2][::-1]
    resized = [
        cv2.GaussianBlur(cv2.resize(img, smallest_size), (5, 5), cv2.BORDER_REFLECT)
        for img in imgs
    ]
    # Pair-wise check resolutions for mean squared error
    for a in resized:
        for b in resized:
            assert np.sum((a - b) ** 2) / np.prod(a.shape) < 16


def test_read_bounds_level_consistency_jp2(_sample_jp2):
    """Test read_bounds produces the same visual field across resolution levels."""
    bounds = (32768, 42880, 33792, 43904)
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    imgs = [wsi.read_bounds(bounds, power, "power") for power in [60, 40, 20, 10]]
    smallest_size = imgs[-1].shape[:2][::-1]
    resized = [
        cv2.GaussianBlur(cv2.resize(img, smallest_size), (5, 5), cv2.BORDER_REFLECT)
        for img in imgs
    ]
    # Pair-wise check resolutions for mean squared error
    for a in resized:
        for b in resized:
            assert np.sum((a - b) ** 2) / np.prod(a.shape) < 16


def test_wsireader_get_thumbnail_openslide(_sample_svs):
    """Test for get_thumbnail as a python function."""
    wsi = wsireader.OpenSlideWSIReader(_sample_svs)
    slide_thumbnail = wsi.get_thumbnail()
    assert isinstance(slide_thumbnail, np.ndarray)
    assert slide_thumbnail.dtype == "uint8"


def test_wsireader_get_thumbnail_jp2(_sample_jp2):
    """Test for get_thumbnail as a python function."""
    wsi = wsireader.OmnyxJP2WSIReader(_sample_jp2)
    slide_thumbnail = wsi.get_thumbnail()
    assert isinstance(slide_thumbnail, np.ndarray)
    assert slide_thumbnail.dtype == "uint8"


def test_wsireader_save_tiles(_sample_svs, tmp_path):
    """Test for save_tiles in wsireader as a python function."""
    file_types = ("*.svs",)
    files_all = utils.misc.grab_files_from_dir(
        input_path=str(pathlib.Path(_sample_svs).parent), file_types=file_types,
    )
    wsi = wsireader.OpenSlideWSIReader(
        files_all[0],
        output_dir=str(pathlib.Path(tmp_path).joinpath("test_wsireader_save_tiles")),
        tile_objective_value=5,
    )
    wsi.save_tiles(verbose=True)
    assert (
        pathlib.Path(tmp_path)
        .joinpath("test_wsireader_save_tiles")
        .joinpath("CMU-1-Small-Region.svs")
        .joinpath("Output.csv")
        .exists()
    )
    assert (
        pathlib.Path(tmp_path)
        .joinpath("test_wsireader_save_tiles")
        .joinpath("CMU-1-Small-Region.svs")
        .joinpath("slide_thumbnail.jpg")
        .exists()
    )
    assert (
        pathlib.Path(tmp_path)
        .joinpath("test_wsireader_save_tiles")
        .joinpath("CMU-1-Small-Region.svs")
        .joinpath("Tile_5_0_0.jpg")
        .exists()
    )


# -------------------------------------------------------------------------------------
# Command Line Interface
# -------------------------------------------------------------------------------------


def test_command_line_read_bounds(_sample_ndpi, tmp_path):
    """Test OpenSlide read_bounds CLI."""
    runner = CliRunner()
    read_bounds_result = runner.invoke(
        cli.main,
        [
            "read-bounds",
            "--wsi_input",
            str(pathlib.Path(_sample_ndpi)),
            "--resolution",
            "0",
            "--units",
            "level",
            "--mode",
            "save",
            "--region",
            "0",
            "0",
            "2000",
            "2000",
            "--output_path",
            str(pathlib.Path(tmp_path).joinpath("im_region.jpg")),
        ],
    )

    assert read_bounds_result.exit_code == 0
    assert pathlib.Path(tmp_path).joinpath("im_region.jpg").is_file()

    read_bounds_result = runner.invoke(
        cli.main,
        [
            "read-bounds",
            "--wsi_input",
            str(pathlib.Path(_sample_ndpi)),
            "--resolution",
            "0",
            "--units",
            "level",
            "--mode",
            "save",
            "--output_path",
            str(pathlib.Path(tmp_path).joinpath("im_region2.jpg")),
        ],
    )

    assert read_bounds_result.exit_code == 0
    assert pathlib.Path(tmp_path).joinpath("im_region2.jpg").is_file()


def test_command_line_jp2_read_bounds(_sample_jp2, tmp_path):
    """Test JP2 read_bounds."""
    runner = CliRunner()
    read_bounds_result = runner.invoke(
        cli.main,
        [
            "read-bounds",
            "--wsi_input",
            str(pathlib.Path(_sample_jp2)),
            "--resolution",
            "0",
            "--units",
            "level",
            "--mode",
            "save",
            "--output_path",
            str(pathlib.Path(tmp_path).joinpath("im_region.jpg")),
        ],
    )

    assert read_bounds_result.exit_code == 0
    assert pathlib.Path(tmp_path).joinpath("im_region.jpg").is_file()


def test_command_line_slide_thumbnail(_sample_ndpi, tmp_path):
    """Test for the slide_thumbnail CLI."""
    runner = CliRunner()
    slide_thumb_result = runner.invoke(
        cli.main,
        [
            "slide-thumbnail",
            "--wsi_input",
            str(pathlib.Path(_sample_ndpi)),
            "--mode",
            "save",
            "--output_path",
            str(pathlib.Path(tmp_path).joinpath("slide_thumb.jpg")),
        ],
    )

    assert slide_thumb_result.exit_code == 0
    assert pathlib.Path(tmp_path).joinpath("slide_thumb.jpg").is_file()


def test_command_line_jp2_slide_thumbnail(_sample_jp2, tmp_path):
    """Test for the jp2 slide_thumbnail CLI."""
    runner = CliRunner()
    slide_thumb_result = runner.invoke(
        cli.main,
        [
            "slide-thumbnail",
            "--wsi_input",
            str(pathlib.Path(_sample_jp2)),
            "--mode",
            "save",
            "--output_path",
            str(pathlib.Path(tmp_path).joinpath("slide_thumb.jpg")),
        ],
    )

    assert slide_thumb_result.exit_code == 0
    assert pathlib.Path(tmp_path).joinpath("slide_thumb.jpg").is_file()


def test_openslide_objective_power_from_mpp(_sample_svs):
    """Test OpenSlideWSIReader approximation of objective power from mpp."""
    wsi = wsireader.OpenSlideWSIReader(_sample_svs)
    wsi.openslide_wsi = DummyMutableOpenSlideObject(wsi.openslide_wsi)
    props = wsi.openslide_wsi._properties

    del props["openslide.objective-power"]
    with pytest.warns(UserWarning, match=r"Objective power inferred"):
        _ = wsi.info

    props["openslide.mpp-x"] = 10
    props["openslide.mpp-y"] = 10
    with pytest.warns(UserWarning, match=r"MPP outside of sensible range"):
        _ = wsi.info

    del props["openslide.mpp-x"]
    del props["openslide.mpp-y"]
    with pytest.warns(UserWarning, match=r"Unable to determine objective power"):
        _ = wsi.info


def test_openslide_mpp_from_tiff_resolution(_sample_svs):
    """Test OpenSlideWSIReader mpp from TIFF resolution tags."""
    wsi = wsireader.OpenSlideWSIReader(_sample_svs)
    wsi.openslide_wsi = DummyMutableOpenSlideObject(wsi.openslide_wsi)
    props = wsi.openslide_wsi._properties

    del props["openslide.mpp-x"]
    del props["openslide.mpp-y"]
    props["tiff.ResolutionUnit"] = "centimeter"
    props["tiff.XResolution"] = 1e4  # Pixels per cm
    props["tiff.YResolution"] = 1e4  # Pixels per cm
    with pytest.warns(UserWarning, match=r"Falling back to TIFF resolution"):
        _ = wsi.info

    assert np.array_equal(wsi.info.mpp, [1, 1])