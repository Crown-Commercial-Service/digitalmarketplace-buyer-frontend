import mock
import pytest

from dmutils.api_stubs import framework

from app.main.helpers.search_save_helpers import get_saved_search_temporary_message_status
from ...helpers import CustomAbortException


class TestGetSavedSearchTemporaryMessageStatus:
    def setup(self):
        self.current_app = mock.patch('app.main.helpers.search_save_helpers.current_app').start()

    @pytest.mark.parametrize(
        ('project_locked_at', 'fwork_status', 'following_fwork_status', 'status'),
        (
            (None, None, 'coming', 'not_locked_pre_live'),
            (None, None, 'open', 'not_locked_pre_live'),
            (None, None, 'pending', 'not_locked_pre_live'),
            (None, None, 'standstill', 'not_locked_pre_live'),
            (None, None, 'live', 'not_locked_post_live'),
            (None, None, 'expired', 'not_locked_post_live'),
            ('2018-06-25T13:39:54.167852Z', None, 'coming', 'locked_pre_live'),
            ('2018-06-25T13:39:54.167852Z', None, 'open', 'locked_pre_live'),
            ('2018-06-25T13:39:54.167852Z', None, 'pending', 'locked_pre_live'),
            ('2018-06-25T13:39:54.167852Z', None, 'standstill', 'locked_pre_live'),
            ('2018-06-25T13:39:54.167852Z', 'live', 'live', 'locked_post_live_during_interim'),
            ('2018-06-25T13:39:54.167852Z', 'expired', 'live', 'locked_post_live_post_interim'),
            ('2018-06-25T13:39:54.167852Z', 'expired', 'expired', 'locked_post_live_post_interim'),
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
