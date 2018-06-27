import mock
import pytest

from dmutils.api_stubs import framework

from app.main.helpers.search_save_helpers import (
    get_saved_search_temporary_message_status,
    NOT_LOCKED_PRE_LIVE,
    NOT_LOCKED_POST_LIVE,
    LOCKED_PRE_LIVE,
    LOCKED_POST_LIVE_DURING_INTERIM,
    LOCKED_POST_LIVE_POST_INTERIM,
)

from ...helpers import CustomAbortException


class TestGetSavedSearchTemporaryMessageStatus:
    def setup(self):
        self.current_app = mock.patch('app.main.helpers.search_save_helpers.current_app').start()

    @pytest.mark.parametrize(
        ('project_locked_at', 'fwork_status', 'following_fwork_status', 'status'),
        (
            (None, None, 'coming', NOT_LOCKED_PRE_LIVE),
            (None, None, 'open', NOT_LOCKED_PRE_LIVE),
            (None, None, 'pending', NOT_LOCKED_PRE_LIVE),
            (None, None, 'standstill', NOT_LOCKED_PRE_LIVE),
            (None, None, 'live', NOT_LOCKED_POST_LIVE),
            (None, None, 'expired', NOT_LOCKED_POST_LIVE),
            ('2018-06-25T13:39:54.167852Z', None, 'coming', LOCKED_PRE_LIVE),
            ('2018-06-25T13:39:54.167852Z', None, 'open', LOCKED_PRE_LIVE),
            ('2018-06-25T13:39:54.167852Z', None, 'pending', LOCKED_PRE_LIVE),
            ('2018-06-25T13:39:54.167852Z', None, 'standstill', LOCKED_PRE_LIVE),
            ('2018-06-25T13:39:54.167852Z', 'live', 'live', LOCKED_POST_LIVE_DURING_INTERIM),
            ('2018-06-25T13:39:54.167852Z', 'expired', 'live', LOCKED_POST_LIVE_POST_INTERIM),
            ('2018-06-25T13:39:54.167852Z', 'expired', 'expired', LOCKED_POST_LIVE_POST_INTERIM),
        ),
    )
    def test_returns_correct_status_for_framework_status_and_project_combinations(
        self, project_locked_at, fwork_status, following_fwork_status, status
    ):

        temp_message_status = get_saved_search_temporary_message_status(
            {'lockedAt': project_locked_at},
            framework(slug='B-Cloud-1', status=fwork_status)['frameworks'],
            framework(slug='B-Cloud-2', status=following_fwork_status)['frameworks'],
        )

        assert temp_message_status == status

    @mock.patch('app.main.helpers.search_save_helpers.abort')
    def test_raises_an_error_if_invalid_state(self, abort):
        abort.side_effect = CustomAbortException()

        with pytest.raises(CustomAbortException):
            get_saved_search_temporary_message_status(
                {'lockedAt': '2018-06-25T13:39:54.167852Z'},
                framework(slug='B-Cloud-1', status='some-new-status')['frameworks'],
                framework(status='live')['frameworks'],
            )

        assert self.current_app.logger.error.call_args_list == [
            mock.call(
                "Saved search temporary messages invalid frameworks state: "
                "'B-Cloud-1' - 'some-new-status' and 'g-cloud-7' - 'live'"
            )
        ]
