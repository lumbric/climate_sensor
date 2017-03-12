import os.path as op
from nose.tools import *
from unittest.mock import patch

import config
from config import Config

CONFIG_PATH = op.dirname(op.realpath(__file__))


def create_mock_input(answers):
    """Pass a dict with substrings of questions/answers."""
    def mock_input(question):
        try:
            answer = next(answers[question_part]
                        for question_part in answers
                        if question_part in question)
        except StopIteration:
            raise ValueError("No answer for question={}".format(question))
        return answer
    return mock_input


def test_construct_empty():
    cfg = Config(keys=[], types=[], descriptions=[], defaults=[],
                 filename='my_file_name')
    assert_equal(cfg.filename, 'my_file_name')


def test_config_not_read():
    cfg = Config(keys=['my_param'], types=[str],
                 descriptions=['my description'],
                 defaults=['my_val'],
                 filename=op.join(CONFIG_PATH, 'testconfig1.json'))
    with assert_raises(KeyError):
        cfg.my_param


def test_config_not_found():
    cfg = Config(keys=['my_param'], types=[str],
                 descriptions=['my description'],
                 defaults=['my_val'],
                 filename='wrong_file.json')
    with assert_raises_regex(ValueError,
                             'wrong_file.json not found.*import setup'):
        cfg.read()


def test_read_config():
    cfg = Config(keys=['my_param'], types=[str],
                 descriptions=['my description'],
                 defaults=['my_val'],
                 filename=op.join(CONFIG_PATH, 'testconfig1.json'))
    cfg.read()
    assert_equal(cfg.my_param, 'my_val')


def test_config_write():
    # TODO should be a temp file
    filename = op.join(CONFIG_PATH, 'testconfig2.json')
    cfg = Config(keys=['my_param'], types=[str],
                 descriptions=['my description'],
                 defaults=['my_val'],
                 filename=filename)
    with open(filename, 'r') as f:
        config_raw = f.read()
    cfg.read()
    cfg.write()

    with open(filename, 'r') as f:
        config_raw_after = f.read()
    assert_equal(config_raw, config_raw_after)


@patch('config.Config.write')
def test_input_config_from_defaults(mock_write):
    cfg = Config(keys=['my_param'], types=[str],
                 descriptions=['my description'],
                 defaults=['my_val'])

    answers = {
        'File exists. Overwrite': 'y',
        'Defaults from old file? [Y/n]': 'n',
        'my_param': ''   # from default
    }
    with patch('builtins.input', create_mock_input(answers)):
        cfg.input()

    assert_equal(cfg.my_param, 'my_val')


@patch('config.Config.write')
def test_input_config_dont_overwrite(mock_write):
    cfg = Config(keys=['my_param'], types=[str],
                 descriptions=['my description'],
                 defaults=['my_val'])

    answers = {
        'File exists. Overwrite': 'n',
    }
    with patch('builtins.input', create_mock_input(answers)):
        cfg.input()


@patch('config.Config.write')
def test_input_config_from_old(mock_write):
    cfg = Config(keys=['my_param'], types=[str],
                 descriptions=['my description'],
                 defaults=['my_default'],
                 filename=op.join(CONFIG_PATH, 'testconfig1.json'))
    answers = {
        'File exists. Overwrite': 'y',
        'Defaults from old file? [Y/n]': '',
        'my_param': '',         # from default
    }
    with patch('builtins.input', create_mock_input(answers)):
        cfg.input()

    assert_equal(cfg.my_param, 'my_val')


@patch('config.Config.write')
def test_input_config_from_old_and_defaults(mock_write):
    cfg = Config(keys=['my_param', 'my_second_param'], types=[str, int],
                 descriptions=['my description', 'my_second_desc'],
                 defaults=['my_val', 2],
                 filename=op.join(CONFIG_PATH, 'testconfig1.json'))
    answers = {
        'File exists. Overwrite': 'y',
        'Defaults from old file? [Y/n]': '',
        'my_param': '',         # from default
        'my_second_param': ''   # from default
    }
    with patch('builtins.input', create_mock_input(answers)):
        cfg.input()

    assert_equal(cfg.my_param, 'my_val')
    assert_equal(cfg.my_second_param, 2)


def test_read_config_missing_keys():
    cfg = Config(keys=['my_param', 'my_second_param'], types=[str, int],
                 descriptions=['my description', 'my_second_desc'],
                 defaults=['my_val', 2],
                 filename=op.join(CONFIG_PATH, 'testconfig1.json'))
    with assert_raises_regex(ValueError, 'invalid config keys.*missing:'
                             ' {\'my_second_param'):
        cfg.read()


def test_read_config_invalid_keys():
    cfg = Config(keys=['my_other_param'], types=[str],
                 descriptions=['my description'] ,
                 defaults=['my_val'],
                 filename=op.join(CONFIG_PATH, 'testconfig1.json'))
    with assert_raises_regex(ValueError, 'invalid config keys.*undefined:'
                             ' {\'my_param'):
        cfg.read()


#def test_invalid_length_defaults():
#def test_invalid_length_descriptions():

def test_value_types():
    cfg = Config(keys=['my_param_int', 'my_param_bool', 'my_param_false'],
                 types=[int, config._bool, config._bool],
                 descriptions=['my int description', 'my bool description', 'my falsy bool'],
                 defaults=[1, True, False],
                 filename=op.join(CONFIG_PATH, 'testconfig3.json'))
    cfg.read()
    assert_equal(cfg.my_param_int, 3)
    assert_equal(type(cfg.my_param_int), int)
    assert_equal(cfg.my_param_bool, True)
    assert_equal(type(cfg.my_param_bool), bool)
    assert_equal(cfg.my_param_false, False)
    assert_equal(type(cfg.my_param_false), bool)


#def test_value_type_str():
#def test_value_type_float():
#def test_value_type_bool():

@patch('config.Config.write')
def test_value_type_func(mock_write):
    cfg = Config(keys=['my_param', 'my_second_param', 'callable', 'my_bool'],
                 types=[str, int, config._callable, config._bool],
                 descriptions=['my description', 'my_second_desc', 'callable', 'my bool'],
                 defaults=['my_val', 2, 'x**2', False],
                 filename='whatever')
    answers = {
        'File exists. Overwrite': 'y',
        'Defaults from old file? [Y/n]': '',
        'my_param': '',          # from default
        'my_second_param': '',   # from default
        'callable': '3* x**2',
        'my_bool': 'true'
    }
    with patch('builtins.input', create_mock_input(answers)):
        cfg.input()

    assert_equal(cfg.my_param, 'my_val')
    assert_equal(cfg.callable(2), 12)


def test_write_func():
    cfg = Config(keys=['callable'],
                 types=[config._callable],
                 descriptions=['callable'],
                 defaults=['x**2'],
                 filename=op.join(CONFIG_PATH, 'tmp.json'))
    cfg.read()
    cfg.write()



#def test_access_default_value():
#    cfg = Config(keys=['my_param'], types=[str],
#                 descriptions=['my description'],
#                 defaults=['my_val'],
#                 filename='test_config1.json')
#    assert_equal(cfg.my_param, 'my_val')


#def test_fill_defaults():
#    assert False
#
#
