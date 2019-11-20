from enum import Enum


class CurrentProjectStageEnum(Enum):
    SAVED = 'save_and_refine_search'
    ENDED = 'search_ended'
    DOWNLOADED = 'download_results'
    READY_TO_ASSESS = 'ready_to_assess'
    # the following correspond with digitalmarketplace-api:app.models.outcomes.Outcome.RESULT_CHOICES
    FAILED = 'none-suitable'
    CANCELLED = 'cancelled'
    AWARDED = 'awarded'


CUSTOM_DIMENSION_IDENTIFIERS = {
    CurrentProjectStageEnum: 8
}


def custom_dimension(custom_dimension_enum, value):
    """
    Create a custom dimension dictionary for Google Analytics.

    Pass in the relevant enum from this module, and either an instance or an actual value from that enum.
    """
    if isinstance(value, str):
        # If we've been given a string, try to convert it to an instance of the enum - if that fails then it'll be loud.
        custom_dimension_instance = custom_dimension_enum(value)
    elif value in CurrentProjectStageEnum:
        custom_dimension_instance = value

    return {
        "data_id": CUSTOM_DIMENSION_IDENTIFIERS[custom_dimension_enum],
        "data_value": custom_dimension_instance.value,
    }
