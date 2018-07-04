import pytest

from app.main.helpers.dm_google_analytics import custom_dimension, CurrentProjectStageEnum


def test_custom_dimension_create_with_enum_instance():
    dimension_dict = custom_dimension(CurrentProjectStageEnum, CurrentProjectStageEnum.AWARDED)
    assert dimension_dict == {'data_id': 8, 'data_value': 'awarded'}


def test_custom_dimension_create_with_string():
    dimension_dict = custom_dimension(CurrentProjectStageEnum, 'awarded')
    assert dimension_dict == {'data_id': 8, 'data_value': 'awarded'}


def test_custom_dimension_fail():
    with pytest.raises(ValueError) as excinfo:
        custom_dimension(CurrentProjectStageEnum, 'fubar')
    assert "'fubar' is not a valid CurrentProjectStageEnum" in str(excinfo)
