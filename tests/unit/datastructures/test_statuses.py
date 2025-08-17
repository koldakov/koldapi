from koldapi import Status


class TestStatusBodyNotAllowed:
    def test_body_not_allowed_should_return_true_when_status_less_than_200(self):
        assert Status.body_not_allowed(Status.HTTP_100_CONTINUE) is True
        assert Status.body_not_allowed(Status.HTTP_101_SWITCHING_PROTOCOLS) is True

    def test_body_not_allowed_should_return_true_when_status_is_204(self):
        assert Status.body_not_allowed(Status.HTTP_204_NO_CONTENT) is True

    def test_body_not_allowed_should_return_true_when_status_is_304(self):
        assert Status.body_not_allowed(Status.HTTP_304_NOT_MODIFIED) is True

    def test_body_not_allowed_should_return_false_when_status_is_regular_success(self):
        assert Status.body_not_allowed(Status.HTTP_200_OK) is False
        assert Status.body_not_allowed(Status.HTTP_201_CREATED) is False

    def test_body_not_allowed_should_return_false_when_status_is_client_or_server_error(self):
        assert Status.body_not_allowed(Status.HTTP_400_BAD_REQUEST) is False
        assert Status.body_not_allowed(Status.HTTP_500_INTERNAL_SERVER_ERROR) is False
