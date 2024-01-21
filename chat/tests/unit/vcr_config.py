import vcr as _vcr


vcr = _vcr.VCR(
    serializer="yaml",
    cassette_library_dir="fixtures/cassettes",
    record_mode="new_episodes",
    match_on=["uri", "method", "path", "query", "body"],
    record_on_exception=False,
)
