from koldapi.datastructures import QueryParams


class TestQueryParams:
    def setup_method(self):
        self.scope = {"query_string": b"pk=1&pk=2&sort=asc"}
        self.query_params = QueryParams.from_scope(self.scope)

    def test_from_scope(self):
        assert self.query_params["pk"] == ["1", "2"]
        assert self.query_params["sort"] == ["asc"]

    def test_len(self):
        assert len(self.query_params) == 2

    def test_contains(self):
        assert "pk" in self.query_params
        assert "sort" in self.query_params

    def test_iter(self):
        assert set(iter(self.query_params)) == {"pk", "sort"}
