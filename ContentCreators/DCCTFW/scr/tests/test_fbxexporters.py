import scr
import logging
import pytest
from scr.tools.fbxexporters import fbx_character_exporter_ui

"""
sample tests

todo:
write real tests for the exporter
"""

test_log = logging.getLogger(scr.logger_name)


def test_add_fail():
    test_log.info('testing add')
    assert 1+1 == 5


def test_add_pass():
    test_log.info('testing add')
    assert 1+1 == 2


def test_import():
    test_log.info('testing character exporter name')
    character_exporter = fbx_character_exporter_ui.FbxCharacterExporterUI()
    assert character_exporter.tool_name == 'FBX Exporter'


# @pytest.fixture(autouse=True)
# def db():
#     yield
#     import time
#     time.sleep(10)