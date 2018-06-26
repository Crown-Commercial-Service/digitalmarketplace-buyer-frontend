import mock
import pytest

from dmcontent.errors import ContentNotFoundError
from dmutils.api_stubs import framework

from app.main.helpers.search_save_helpers import get_saved_search_temporary_message
from ...helpers import CustomAbortException


class TestGetSavedSearchTemporaryMessage:
    def setup(self):
        self.content_loader = mock.Mock()
        self.get_framework_or_500_patch = mock.patch('app.main.helpers.search_save_helpers.get_framework_or_500')
        self.get_framework_or_500 = self.get_framework_or_500_patch.start()
        self.current_app_patch = mock.patch('app.main.helpers.search_save_helpers.current_app')
        self.current_app = self.current_app_patch.start()

        self.get_framework_or_500.return_value = framework(status='live')['frameworks']

    def teardown(self):
        self.get_framework_or_500_patch.stop()
        self.current_app_patch.stop()

    def test_returns_none_if_following_framework_metadata_not_found_for_framework(self):
        self.content_loader.get_metadata.side_effect = ContentNotFoundError()

        temp_message = get_saved_search_temporary_message(
            mock.Mock(), self.content_loader, {'slug': 'B-Cloud-1'}, 'search url', {}
        )

        assert self.content_loader.get_metadata.call_args_list == [
            mock.call('B-Cloud-1', 'following_framework', 'slug')
        ]
        assert temp_message is None

    def test_returns_none_if_temporary_messages_not_found_for_framework(self):
        self.content_loader.get_message.side_effect = ContentNotFoundError()

        temp_message = get_saved_search_temporary_message(
            mock.Mock(), self.content_loader, {'slug': 'B-Cloud-1'}, 'search url', {}
        )

        assert self.content_loader.get_message.call_args_list == [
            mock.call('B-Cloud-1', 'saved-search-temporary-messages')
        ]
        assert temp_message is None

    def test_the_correct_context_is_applied_to_messages(self):
        message_mock = mock.Mock()
        self.content_loader.get_message.return_value = message_mock
        message_mock.filter.return_value = {'not_locked_post_live': 'content'}

        get_saved_search_temporary_message(
            mock.Mock(),
            self.content_loader,
            framework(slug='B-Cloud-1')['frameworks'],
            'www.example.com/search?q=sausages',
            {'lockedAt': None}
        )

        assert message_mock.filter.call_args_list == [
            mock.call({
                'search_url': 'www.example.com/search?q=sausages',
                'expiration_date': 'Thursday 6 January 2000',
            })
        ]

    @pytest.mark.parametrize(
        ('project_locked_at', 'fwork_status', 'following_fwork_status', 'type', 'content'),
        (
            (None, None, 'coming', 'sidebar', 'Not locked pre-live content'),
            (None, None, 'open', 'sidebar', 'Not locked pre-live content'),
            (None, None, 'pending', 'sidebar', 'Not locked pre-live content'),
            (None, None, 'standstill', 'sidebar', 'Not locked pre-live content'),
            (None, None, 'live', 'sidebar', 'Not locked post-live content'),
            (None, None, 'expired', 'sidebar', 'Not locked post-live content'),
            ('2018-06-25T13:39:54.167852Z', None, 'coming', 'banner', 'Locked pre-live content'),
            ('2018-06-25T13:39:54.167852Z', None, 'open', 'banner', 'Locked pre-live content'),
            ('2018-06-25T13:39:54.167852Z', None, 'pending', 'banner', 'Locked pre-live content'),
            ('2018-06-25T13:39:54.167852Z', None, 'standstill', 'banner', 'Locked pre-live content'),
            ('2018-06-25T13:39:54.167852Z', 'live', 'live', 'banner', 'Locked post-live during interim content'),
            ('2018-06-25T13:39:54.167852Z', 'live', 'expired', 'banner', 'Locked post-live during interim content'),
            ('2018-06-25T13:39:54.167852Z', 'expired', 'live', 'banner', 'Locked post-live post interim content'),
            ('2018-06-25T13:39:54.167852Z', 'expired', 'expired', 'banner', 'Locked post-live post interim content'),
        ),
    )
    def test_returns_correct_message_for_framework_status_and_project_combinations(
        self, project_locked_at, fwork_status, following_fwork_status, type, content
    ):
        self.get_framework_or_500.return_value = framework(status=following_fwork_status)['frameworks']
        fake_content = {
            'not_locked_pre_live': 'Not locked pre-live content',
            'not_locked_post_live': 'Not locked post-live content',
            'locked_pre_live': 'Locked pre-live content',
            'locked_post_live_during_interim': 'Locked post-live during interim content',
            'locked_post_live_post_interim': 'Locked post-live post interim content',
        }
        message_mock = mock.Mock()
        self.content_loader.get_message.return_value = message_mock
        message_mock.filter.return_value = fake_content

        temp_message = get_saved_search_temporary_message(
            mock.Mock(),
            self.content_loader,
            framework(slug='B-Cloud-1', status=fwork_status)['frameworks'],
            'search url',
            {'lockedAt': project_locked_at}
        )

        assert temp_message == {'type': type, 'content': content}

    @mock.patch('app.main.helpers.search_save_helpers.abort')
    def test_raises_an_error_if_invalid_state(self, abort):
        abort.side_effect = CustomAbortException()

        with pytest.raises(CustomAbortException):
            get_saved_search_temporary_message(
                mock.Mock(),
                self.content_loader,
                framework(slug='B-Cloud-1', status='some-new-status')['frameworks'],
                'search url',
                {'lockedAt': '2018-06-25T13:39:54.167852Z'},
            )

        assert self.current_app.logger.error.call_args_list == [
            mock.call(
                "Saved search temporary messages not found, "
                "invalid frameworks state: 'B-Cloud-1' - 'some-new-status' and 'g-cloud-7' - 'live'"
            )
        ]
