import re

from second_brain.app import main


def test_main_logs_greeting(capfd):
    main()
    captured = capfd.readouterr()
    assert "Hello from second_brain!" in captured.err


def test_log_timestamp_has_no_milliseconds(capfd):
    main()
    captured = capfd.readouterr()
    # Timestamp should be YYYY-MM-DD HH:MM:SS with no trailing .SSS
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \|", captured.err)


def test_log_level_has_no_padding(capfd):
    main()
    captured = capfd.readouterr()
    # "| INFO |" not "| INFO     |"
    assert "| INFO |" in captured.err


def test_log_message_uses_pipe_separator(capfd):
    main()
    captured = capfd.readouterr()
    # Message should be preceded by "| " not "- "
    assert "| Hello from second_brain!" in captured.err


def test_file_handler_uses_custom_format(tmp_path, monkeypatch):
    log_file = tmp_path / "test_format.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    main()
    content = log_file.read_text()
    assert "| INFO |" in content
    assert "| Hello from second_brain!" in content
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \|", content)
