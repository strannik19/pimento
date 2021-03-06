'''
Test suite for pimento
'''


# [ Imports ]
# [ - Python ]
import inspect
import sys
# [ - Third Party ]
import pexpect
import pytest
# [ - Project ]
import pimento


# [ Helpers ]
def expect_color_menu_prompt(process):
    # expect the following lines to be in the prompt, in this order.
    process.expect_exact('which color?')
    process.expect_exact('  red')
    process.expect_exact('  blue')
    process.expect_exact('  green')
    process.expect_exact('  black')
    process.expect_exact('  grey')
    process.expect_exact('  white')
    process.expect_exact('Please select one: ')


def get_color_menu_process():
    # create a process which prompts for a color selection
    p = pexpect.spawn('pimento red blue green black grey white -p "which color?" -P "Please select one: "', timeout=1)
    expect_color_menu_prompt(p)
    return p


def expect_menu_prompt(process):
    # expect the following lines to be in the prompt, in this order.
    process.expect_exact('yes or no?')
    process.expect_exact('  yes')
    process.expect_exact('  no')
    process.expect_exact('Please choose: ')


def get_menu_process():
    # create a process which prompts for a yes/no selection
    p = pexpect.spawn('pimento yes no -p "yes or no?" -P "Please choose: "', timeout=1)
    expect_menu_prompt(p)
    return p


# [ Tests ]
def test_menu_accepts_full_response():
    # yes
    p = get_menu_process()
    p.sendline('yes')
    p.expect('yes')
    # no
    p = get_menu_process()
    p.sendline('no')
    p.expect('no')


def test_menu_rejects_unmatching_response():
    # maybe, then yes
    p = get_menu_process()
    p.sendline('maybe')
    p.expect_exact('[!] "maybe" does not match any of the valid choices.')
    expect_menu_prompt(p)
    p.sendline('yes')
    p.expect('yes')
    # maybe, then no
    p = get_menu_process()
    p.sendline('maybe')
    p.expect_exact('[!] "maybe" does not match any of the valid choices.')
    expect_menu_prompt(p)
    p.sendline('no')
    p.expect('no')


def test_menu_rejects_no_response():
    # empty, then yes
    p = get_menu_process()
    p.sendline('')
    p.expect_exact('[!] an empty response is not valid.')
    expect_menu_prompt(p)
    p.sendline('yes')
    p.expect('yes')
    # empty, then no
    p = get_menu_process()
    p.sendline('')
    p.expect_exact('[!] an empty response is not valid.')
    expect_menu_prompt(p)
    p.sendline('no')
    p.expect('no')


def test_menu_accepts_partial_response():
    # just y for yes
    p = get_menu_process()
    p.sendline('y')
    p.expect('yes')
    p = get_menu_process()
    p.sendline('ye')
    p.expect('yes')
    # just n for no
    p = get_menu_process()
    p.sendline('n')
    p.expect('no')


def test_menu_rejects_multiple_matches():
    # blue, partial then full
    p = get_color_menu_process()
    p.sendline('b')
    p.expect_exact('[!] "b" matches multiple choices:')
    p.expect_exact('[!]   blue')
    p.expect_exact('[!]   black')
    p.expect_exact('[!] Please specify your choice further.')
    expect_color_menu_prompt(p)
    p.sendline('bl')
    p.expect_exact('[!] "bl" matches multiple choices:')
    p.expect_exact('[!]   blue')
    p.expect_exact('[!]   black')
    p.expect_exact('[!] Please specify your choice further.')
    p.sendline('blu')
    p.expect('blue')
    # black, partial then full
    p = get_color_menu_process()
    p.sendline('bla')
    p.expect('black')


def test_menu_default():
    # select the default
    p = pexpect.spawn('pimento yes no -p "Yes/No?" -P "Please select one [{}]: " --default-index=1', timeout=1)
    p.expect_exact('Yes/No?')
    p.expect_exact('  yes')
    p.expect_exact('  no')
    p.expect_exact('Please select one [no]: ')
    p.sendline('')
    p.expect('no')


def test_menu_numbered():
    # select by number
    p = pexpect.spawn('pimento yes no maybe -i --pre "Select one of the following:" --post "Please select by index or value [{}]: " -d 0', timeout=1)
    p.expect_exact('Select one of the following:')
    p.expect_exact('  [0] yes')
    p.expect_exact('  [1] no')
    p.expect_exact('  [2] maybe')
    p.expect_exact('Please select by index or value [yes]: ')
    p.sendline('1')
    p.expect('no')


def test_indexed_numbers():
    # select by either index number or number value
    p = pexpect.spawn('python test_pimento.py --indexed-numbers', timeout=1)
    p.expect_exact('Select one of the following:')
    p.expect_exact('  [0] 100')
    p.expect_exact('  [1] 200')
    p.expect_exact('  [2] 300')
    p.expect_exact('Please select by index or value: ')
    # index
    p.sendline('1')
    p.expect('Result is 200')
    p = pexpect.spawn('python test_pimento.py --indexed-numbers', timeout=1)
    p.expect_exact('Select one of the following:')
    p.expect_exact('  [0] 100')
    p.expect_exact('  [1] 200')
    p.expect_exact('  [2] 300')
    p.expect_exact('Please select by index or value: ')
    # value
    p.sendline('3')
    p.expect('Result is 300')


def test_default_not_in_range():
    # negative
    with pytest.raises(ValueError):
        pimento.menu(['yes', 'no'], "Yes/No?", "Please select one [{}]: ", default_index=-1)
    # past range
    with pytest.raises(ValueError):
        pimento.menu(['yes', 'no'], "Yes/No?", "Please select one [{}]: ", default_index=2)


def test_default_incorrect_type():
    # float
    with pytest.raises(TypeError):
        pimento.menu(['yes', 'no'], "Yes/No?", "Please select one [{}]: ", default_index=1.5)


def test_no_items():
    # try to create a menu with no items
    with pytest.raises(ValueError):
        pimento.menu([], "Yes/No?", "Please select one: ")


def test_bad_items_type():
    # try to create a menu with bad items
    # with a non-iterable
    with pytest.raises(TypeError):
        pimento.menu(6, "Yes/No?", "Please select one: ")
    # with an unbounded iterable
    def generator():
        x = 0
        while True:
            yield x
            x += 1
    with pytest.raises(TypeError):
        pimento.menu(generator(), "Yes/No?", "Please select one: ")


def test_iterable_items():
    # with a tuple
    p = pexpect.spawn('python test_pimento.py --tuple', timeout=1)
    p.expect_exact('Select one of the following:')
    p.expect_exact('  100')
    p.expect_exact('  200')
    p.expect_exact('  300')
    p.expect_exact('Please select: ')
    # a string
    p = pexpect.spawn('python test_pimento.py --string', timeout=1)
    p.expect_exact('Select one of the following:')
    p.expect_exact('  a')
    p.expect_exact('  b')
    p.expect_exact('  c')
    p.expect_exact('Please select: ')
    # a dict
    p = pexpect.spawn('python test_pimento.py --dictionary', timeout=1)
    p.expect_exact('Select one of the following:')
    i = p.expect_exact(['  key1', '  key2'])
    if i == 0:
        p.expect_exact('  key2')
    else:
        p.expect_exact('  key1')
    p.expect_exact('Please select: ')
    # a set
    p = pexpect.spawn('python test_pimento.py --set', timeout=1)
    p.expect_exact('Select one of the following:')
    p.expect_exact('  1')
    p.expect_exact('  2')
    p.expect_exact('Please select: ')


def test_string_prompts():
    # not a string (int) for pre-prompt
    with pytest.raises(TypeError):
        pimento.menu(123, [1, 2, 3], "Please select one: ")
    # not a string (list) for post-prompt
    with pytest.raises(TypeError):
        pimento.menu("Yes/No?", ['y', 'n'], ['prompt'])


def test_non_string_items():
    # use a set of ints for items
    p = pexpect.spawn('python test_pimento.py --set', timeout=1)
    p.expect_exact('Select one of the following:')
    p.expect_exact('  1')
    p.expect_exact('  2')
    p.expect_exact('Please select: ')
    p.sendline('1')
    p.expect_exact('Result is 1')


def test_default_post_prompt():
    # the the post prompt, no default
    p = pexpect.spawn('pimento 1 2 -p "Select one of the following:"', timeout=1)
    p.expect_exact('Select one of the following:')
    p.expect_exact('  1')
    p.expect_exact('  2')
    p.expect_exact('Enter an option to continue: ')
    # get the post propmt, with default
    p = pexpect.spawn('pimento 1 2 -p "Select one of the following:" -d 0', timeout=1)
    p.expect_exact('Select one of the following:')
    p.expect_exact('  1')
    p.expect_exact('  2')
    p.expect_exact('Enter an option to continue [1]: ')


def test_post_prompt_not_string():
    # test for https://github.com/toejough/pimento/issues/15
    # test post prompt is int
    try:
        pimento.menu([1,2,3], "pre-prompt", 5)
    except Exception as e:
        assert "pre_prompt" not in e.args[0]


def test_menu_documentation():
    # check the menu documentation
    assert pimento.menu.__doc__ == '''
    Prompt with a menu.

    Arguments:
        pre_prompt -  Text to print before the option list.
        items -  The items to print as options.
        post_prompt -  Text to print after the option list.
        default_index -  The index of the item which should be default, if any.
        indexed -  Boolean.  True if the options should be indexed.
        stream -  the stream to use to prompt the user.  Defaults to stderr so that stdout
            can be reserved for program output rather than interactive menu output.
        insensitive -  allow insensitive matching.  Also drops items which case-insensitively match
          prior items.
        fuzzy -  search for the individual words in the user input anywhere in the item strings.

    Specifying a default index:
        The default index must index into the items.  In other words, `items[default_index]`
        must exist.  It is encouraged, but not required, that you show the user that there is
        a default, and what it is, via string interpolation in either of the prompts:
            "prompt [{}]" as the prompt string will print "prompt [default]" if "default" were
            the value of the item at the default index.

    The default post-prompt:
        The default post prompt is different depending on whether or not you provide a default_index.
        If you don't, the prompt is just "Enter an option to continue: ".
        If you do, the prompt adds the default value: "Enter an option to continue [{}]: "

    Return:
        result -  The full text of the unambiguously selected item.
    '''


def test_package_documentation():
    # test the package doc string
    assert pimento.__doc__ == '\nMake simple python cli menus!\n'


def test_module_contents():
    # check that only the expected public functions are public in the module
    public_attributes = [a for a in pimento.__dict__ if not a.startswith('_')]
    assert public_attributes == ['menu']


def test_cli_script_help():
    # check the CLI script help message
    expected_help_text = '''usage: pimento [-h] [--version] [--pre TEXT] [--post TEXT]
               [--default-index INT] [--indexed] [--insensitive] [--fuzzy]
               [--stdout]
               [option [option ...]]


Present the user with a simple CLI menu, and return the option chosen. The
menu is presented via stderr. The output is printed to stdout for piping.

positional arguments:
  option                The option(s) to present to the user.

optional arguments:
  -h, --help            show this help message and exit
  --version, -v         Print the version and then exit
  --pre TEXT, -p TEXT   The pre-prompt/title/introduction to the menu.
                        [Options:]
  --post TEXT, -P TEXT  The prompt presented to the user after the menu items.
  --default-index INT, -d INT
                        The index of the item to use as the default
  --indexed, -i         Print indices with the options, and allow the user to
                        use them to choose.
  --insensitive, -I     Perform insensitive matching. Also drops any items
                        that case-insensitively match prior items.
  --fuzzy, -f           search for the individual words in the user input
                        anywhere in the item strings.
  --stdout              Use stdout for interactive output (instead of the
                        default: stderr).

The default for the post prompt is "Enter an option to continue: ". If
--default-index is specified, the default option value will be printed in the
post prompt as well.'''
    expected_lines = expected_help_text.splitlines()
    p = pexpect.spawn('pimento --help', timeout=1)
    for line in expected_lines:
        try:
            p.expect_exact(line)
        except:
            assert line in p.before


def test_default_pre_prompt():
    # validate the default pre-prompt
    p = pexpect.spawn('python test_pimento.py --list-only', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  1')
    p.expect_exact('  2')
    p.expect_exact('Enter an option to continue: ')


def test_deduplication():
    # validate deduplication
    # repeated elsewehre
    p = pexpect.spawn('pimento foo bar baz bar foo', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  foo')
    p.expect_exact('  bar')
    p.expect_exact('  baz')
    p.expect_exact('Enter an option to continue: ')
    # repeated immediately
    p = pexpect.spawn('pimento foo foo foo', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  foo')
    p.expect_exact('Enter an option to continue: ')


def test_insensitive_matching():
    # match caps to non-caps
    # first letter
    p = pexpect.spawn('pimento FOO BAR BAZ --insensitive', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  FOO')
    p.expect_exact('  BAR')
    p.expect_exact('  BAZ')
    p.expect_exact('Enter an option to continue: ')
    p.sendline('Foo')
    p.expect_exact('FOO')
    # whole word
    p = pexpect.spawn('pimento FOO BAR BAZ --insensitive', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  FOO')
    p.expect_exact('  BAR')
    p.expect_exact('  BAZ')
    p.expect_exact('Enter an option to continue: ')
    p.sendline('bar')
    p.expect_exact('BAR')
    # last letter
    p = pexpect.spawn('pimento FOO BAR BAZ --insensitive', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  FOO')
    p.expect_exact('  BAR')
    p.expect_exact('  BAZ')
    p.expect_exact('Enter an option to continue: ')
    p.sendline('baZ')
    p.expect_exact('BAZ')


def test_insensitive_deduplication():
    # deduplicate non-sequential
    p = pexpect.spawn('pimento FOO bar baz bAr foo', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  FOO')
    p.expect_exact('  bar')
    p.expect_exact('  baz')
    p.expect_exact('Enter an option to continue: ')
    # deduplicate sequential
    p = pexpect.spawn('pimento Foo fOo foO', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  Foo')
    p.expect_exact('Enter an option to continue: ')


def test_arrows():
    # test arrow support
    p = pexpect.spawn('pimento foo bar', timeout=1)
    # until the python3 input bug is fixed, and the warnings are removed, expect a warning message here
    if sys.version_info.major == 3:
        p.expect_exact('python3 input bug (issue24402)')
    p.expect_exact('Enter an option to continue: ')
    p.send('oo')
    p.sendline()
    p.expect_exact('[!] "oo" does not match any of the valid choices.')
    p.expect_exact('Enter an option to continue: ')
    KEY_UP = '\x1b[A'
    #KEY_DOWN = '\x1b[B'
    #KEY_RIGHT = '\x1b[C'
    KEY_LEFT = '\x1b[D'
    p.send(KEY_UP)
    # until the python3 input bug is fixed, expect an actual tab in python3
    i = p.expect_exact(['oo', pexpect.TIMEOUT])
    if sys.version_info.major == 2:
        assert i == 0
    else:
        assert i == 1
        return
    p.send(KEY_LEFT*2)
    p.sendline('f')
    p.expect('\r\nfoo')


def test_tab():
    # test the tab completion functionality
    p = pexpect.spawn('pimento "hello there" "hello joe" "hey you" "goodbye hector"', timeout=1)
    # until the python3 input bug is fixed, and the warnings are removed, expect a warning message here
    if sys.version_info.major == 3:
        p.expect_exact('python3 input bug (issue24402)')
    p.expect_exact('Enter an option to continue: ')
    p.send('h')
    p.sendcontrol('i')
    # until the python3 input bug is fixed, expect an actual tab in python3
    i = p.expect_exact(['e', pexpect.TIMEOUT])
    if sys.version_info.major == 2:
        assert i == 0
    else:
        assert i == 1
        return
    # double tab to get a list of matches
    p.sendcontrol('i')
    p.sendcontrol('i')
    p.expect_exact('[!] "he" matches multiple options:')
    p.expect_exact('[!]   hello there')
    p.expect_exact('[!]   hello joe')
    p.expect_exact('[!]   hey you')
    p.expect_exact('Enter an option to continue: he')
    p.send('l')
    # single tab to complete up to common completion
    p.sendcontrol('i')
    p.expect_exact('lo')
    # double tab to get a list of matches
    p.sendcontrol('i')
    p.sendcontrol('i')
    p.expect_exact('[!] "hello " matches multiple options:')
    p.expect_exact('[!]   hello there')
    p.expect_exact('[!]   hello joe')
    p.expect_exact('Enter an option to continue: hello')


def test_tab_with_middle():
    # test if the text to complete starts in the middle of some other word, too
    p = pexpect.spawnu('pimento "foo bar" "baz bar" "quux.bar" "barbell" "barstool"', timeout=1)
    # until the python3 input bug is fixed, and the warnings are removed, expect a warning message here
    if sys.version_info.major == 3:
        p.expect_exact('python3 input bug (issue24402)')
    p.expect_exact(u'Enter an option to continue: ')
    p.send('bar')
    # double tab for completion list
    p.sendcontrol('i')
    p.sendcontrol('i')
    # until the python3 input bug is fixed, expect an actual tab in python3
    i = p.expect_exact([u'[!] "bar" matches multiple options:', pexpect.TIMEOUT])
    if sys.version_info.major == 2:
        assert i == 0
    else:
        assert i == 1
        return
    # for python 2, expect just the options that START with the completion text
    p.expect_exact(u'[!]   barbell')
    assert 'foo' not in p.before
    p.expect_exact(u'[!]   barstool')
    assert 'foo' not in p.before


def test_tab_ci():
    # test case-insensitive tab completion
    p = pexpect.spawn('pimento "HELLO you" "hello joe" "hey you" "goodbye hector" -I', timeout=1)
    # until the python3 input bug is fixed, and the warnings are removed, expect a warning message here
    if sys.version_info.major == 3:
        p.expect_exact('python3 input bug (issue24402)')
    p.expect_exact('Enter an option to continue: ')
    p.send('h')
    p.sendcontrol('i')
    # until the python3 input bug is fixed, expect an actual tab in python3
    i = p.expect_exact(['e', pexpect.TIMEOUT])
    if sys.version_info.major == 2:
        assert i == 0
    else:
        assert i == 1
        return
    # double tab to display options
    p.sendcontrol('i')
    p.sendcontrol('i')
    p.expect_exact('[!] "he" matches multiple options:')
    p.expect_exact('[!]   HELLO you')
    p.expect_exact('[!]   hello joe')
    p.expect_exact('[!]   hey you')
    p.expect_exact('Enter an option to continue: he')
    p.send('l')
    # single tab to extend completion
    p.sendcontrol('i')
    p.expect_exact('lo')
    # double tab to show options
    p.sendcontrol('i')
    p.sendcontrol('i')
    p.expect_exact('[!] "hello " matches multiple options:')
    p.expect_exact('[!]   HELLO you')
    p.expect_exact('[!]   hello joe')
    p.expect_exact('Enter an option to continue: hello')


def test_tab_fuzzy():
    # test tab completion with fuzzy matching
    p = pexpect.spawn('pimento "HELLO you" "hello joe" "hey you" "goodbye hector" -f', timeout=1)
    # until the python3 input bug is fixed, and the warnings are removed, expect a warning message here
    if sys.version_info.major == 3:
        p.expect_exact('python3 input bug (issue24402)')
    p.expect_exact('Enter an option to continue: ')
    p.send('h')
    p.sendcontrol('i')
    # until the python3 input bug is fixed, expect an actual tab in python3
    i = p.expect_exact(['e', pexpect.TIMEOUT])
    if sys.version_info.major == 2:
        assert i == 0
    else:
        assert i == 1
        return
    # double tab for options
    p.sendcontrol('i')
    p.sendcontrol('i')
    p.expect_exact('[!] "he" matches multiple options:')
    p.expect_exact('[!]   hello joe')
    p.expect_exact('[!]   hey you')
    p.expect_exact('[!]   goodbye hector')
    p.expect_exact('Enter an option to continue: he')
    p.send(' g')
    # single tab to expand
    p.sendcontrol('i')
    p.expect_exact('oodbye')
    p.send(' ')
    p.sendcontrol('i')
    i = p.expect_exact(['he goodbye hector', pexpect.EOF, pexpect.TIMEOUT])
    assert i != 0, "got incorrect completion of 'hector'"


def test_tab_fuzzy_ci():
    # fuzzy completion, case insensitive
    p = pexpect.spawn('pimento "HELLO you" "hello joe" "hey you" "goodbye hector" -fI', timeout=1)
    # until the python3 input bug is fixed, and the warnings are removed, expect a warning message here
    if sys.version_info.major == 3:
        p.expect_exact('python3 input bug (issue24402)')
    p.expect_exact('Enter an option to continue: ')
    p.send('h')
    p.sendcontrol('i')
    # until the python3 input bug is fixed, expect an actual tab in python3
    i = p.expect_exact(['e', pexpect.TIMEOUT])
    if sys.version_info.major == 2:
        assert i == 0
    else:
        assert i == 1
        return
    # double tab for options
    p.sendcontrol('i')
    p.sendcontrol('i')
    p.expect_exact('[!] "he" matches multiple options:')
    p.expect_exact('[!]   HELLO you')
    p.expect_exact('[!]   hello joe')
    p.expect_exact('[!]   hey you')
    p.expect_exact('[!]   goodbye hector')
    p.expect_exact('Enter an option to continue: he')


def test_fuzzy_matching():
    # test fuzzy matching
    p = pexpect.spawn('pimento "a blue thing" "one green thing" --fuzzy', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  a blue thing')
    p.expect_exact('  one green thing')
    p.expect_exact('Enter an option to continue: ')
    # send a word at the end of multiple options
    p.sendline('thing')
    p.expect_exact('[!] "thing" matches multiple choices:')
    p.expect_exact('[!]   a blue thing')
    p.expect_exact('[!]   one green thing')
    p.expect_exact('[!] Please specify your choice further.')
    # send a partial word which, with the prior one, still matches multiple options
    p.sendline('thing e')
    p.expect_exact('[!] "thing e" matches multiple choices:')
    p.expect_exact('[!]   a blue thing')
    p.expect_exact('[!]   one green thing')
    p.expect_exact('[!] Please specify your choice further.')
    # send another partial word, which, with the prior two, limits to one option
    p.sendline('thing e e')
    p.expect_exact('one green thing')
    # test words out of order
    p = pexpect.spawn('pimento "a blue thing" "one green thing" --fuzzy', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  a blue thing')
    p.expect_exact('  one green thing')
    p.expect_exact('Enter an option to continue: ')
    p.sendline('thing blue')
    p.expect_exact('a blue thing')


def test_insensitive_fuzzy_matching():
    # insensitive fuzzy matching
    p = pexpect.spawn('pimento "a BLUE thing" "one GREEN thing" -I --fuzzy', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  a BLUE thing')
    p.expect_exact('  one GREEN thing')
    p.expect_exact('Enter an option to continue: ')
    # send a word at the end of multiple options, but wrong case
    p.sendline('THING')
    p.expect_exact('[!] "THING" matches multiple choices:')
    p.expect_exact('[!]   a BLUE thing')
    p.expect_exact('[!]   one GREEN thing')
    p.expect_exact('[!] Please specify your choice further.')
    # send a partial word which, with the prior one, still matches multiple options
    p.sendline('thing e')
    p.expect_exact('[!] "thing e" matches multiple choices:')
    p.expect_exact('[!]   a BLUE thing')
    p.expect_exact('[!]   one GREEN thing')
    p.expect_exact('[!] Please specify your choice further.')
    # send another partial word with wrong case, which, with the prior two, limits to one option
    p.sendline('thing e e')
    p.expect_exact('one GREEN thing')
    # thest words out of order
    p = pexpect.spawn('pimento "a BLUE thing" "one GREEN thing" --fuzzy', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  a BLUE thing')
    p.expect_exact('  one GREEN thing')
    p.expect_exact('Enter an option to continue: ')
    p.sendline('thing blue')
    p.expect_exact('a BLUE thing')


def test_functions_documented():
    # verify all functions have a docstring
    for name, func in inspect.getmembers(pimento, inspect.isfunction):
        assert func.__doc__, "{} not documented!".format(name)


def test_empty_option_cli():
    # test error response with empty items provided on the CLI
    # all empty
    p = pexpect.spawn('pimento "" "" ""', timeout=1)
    p.expect_exact('ERROR: The item list is empty.')
    # some empty
    p = pexpect.spawn('pimento "" "a BLUE thing" "" "one GREEN thing" "" --fuzzy', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  a BLUE thing')
    p.expect_exact('  one GREEN thing')
    p.expect_exact('Enter an option to continue: ')


def test_empty_option_menu():
    # list with only an empty option
    with pytest.raises(ValueError):
        pimento.menu([''])


def test_whitespace_option_menu():
    # list with only whitespace options
    with pytest.raises(ValueError):
        pimento.menu(['', ' ', '\t', '\n', '\r  '])


def test_pre_default_selection():
    # test default selection
    p = pexpect.spawn('pimento "" "RED" " " "red" "\n\t\r" "green" -Id 5', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  RED')
    p.expect_exact('  green')
    p.expect_exact('Enter an option to continue [green]: ')


def test_rstrip_items():
    # test rstripping items
    p = pexpect.spawn('pimento "red " "red  " "red\t"', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  red')
    p.expect_exact('Enter an option to continue: ')


def test_empty_default_selection():
    # test empty default
    with pytest.raises(ValueError):
        pimento.menu(['', 'foo'], default_index=0)


def test_empty_default_selection_cli():
    # empty default
    p = pexpect.spawn('pimento "" "foo" -d 0', timeout=1)
    p.expect_exact('ERROR: The default index (0) points to an empty item.')


def test_ctrl_c():
    # stop with ctrl-c
    p = pexpect.spawn('pimento foo', timeout=1)
    p.expect_exact('Enter an option to continue:')
    p.sendcontrol('c')
    p.expect_exact('CTRL-C detected. Exiting.')


def test_partial_option():
    # test an exact match, even if another option exists which starts with what was entered
    p = pexpect.spawn('pimento foo "foo bar"', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  foo')
    p.expect_exact('  foo bar')
    p.expect_exact('Enter an option to continue: ')
    p.sendline('foo')
    p.expect_exact('foo')
    index = p.expect_exact(['[!]', 'foo'])
    assert index != 0, "Got unexpected warning"


def test_partial_fuzzy_option():
    # test an exact match, even if another option exists which also (incompletely) macthes what was entered
    p = pexpect.spawn('pimento foo "foo bar" "foo bar baz" -f', timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  foo')
    p.expect_exact('  foo bar')
    p.expect_exact('  foo bar baz')
    p.expect_exact('Enter an option to continue: ')
    p.sendline('oo')
    p.expect_exact('[!] "oo" matches multiple choices:')
    p.expect_exact('[!]   foo')
    p.expect_exact('[!]   foo bar')
    p.expect_exact('[!]   foo bar baz')
    p.expect_exact('[!] Please specify your choice further.')
    p.sendline('bar foo')
    p.expect_exact('foo bar baz')


def test_piping_to_cli():
    # pipe to the CLI and still allow interaction
    p = pexpect.spawn('bash', args = ['-c', 'echo -e "hello\ngoodbye" | pimento'], timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  hello')
    p.expect_exact('  goodbye')
    p.expect_exact('Enter an option to continue: ')


def test_piping_from_cli():
    # pipe from the CLI to something else
    p = pexpect.spawn('bash', args = ['-c', 'echo -e "hello\ngoodbye" | pimento | cat'], timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  hello')
    p.expect_exact('  goodbye')
    p.expect_exact('Enter an option to continue: ')


def test_piping_from_cli_and_tab():
    # test tab complition whith piping
    p = pexpect.spawn('bash', args = ['-c', 'echo -e "hello\ngoodbye" | pimento | cat'], timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  hello')
    p.expect_exact('  goodbye')
    p.expect_exact('Enter an option to continue: ')
    p.send('he')
    p.sendcontrol('i')
    index = p.expect_exact(['hello', pexpect.TIMEOUT])
    # python 2 should match
    if sys.version_info.major == 2:
        assert index == 0
    # python 3 fails, because readline is disabled if piped
    else:
        assert index == 1

def test_piping_from_cli_and_tab_with_stdout_stream():
    # pipe with stdout as the interactive stream
    # swap stdout and stderr
    # send stdout to cat
    # expect to still get interactive
    p = pexpect.spawn('bash', args = ['-c', 'pimento "hello" "goodbye" --stdout 3>&1 1>&2 2>&3 | cat'], timeout=1)
    p.expect_exact('Options:')
    p.expect_exact('  hello')
    p.expect_exact('  goodbye')
    p.expect_exact('Enter an option to continue: ')
    p.send('he')
    p.sendcontrol('i')
    p.expect_exact('hello')

def test_version_option():
    # test the version is printed
    p = pexpect.spawn('pimento --version', timeout=1)
    p.expect_exact('Pimento - v0.7.1')
    p.close()
    assert p.exitstatus == 0
    p = pexpect.spawn('pimento -v', timeout=1)
    p.expect_exact('Pimento - v0.7.1')
    p.close()
    assert p.exitstatus == 0

def test_piping_to_cli_and_tab():
    # pipe to the cli and use tab (different than tabbing when cli is piped to something)
    p = pexpect.spawn('bash', args = ['-c', 'echo -e "hello\ngoodbye" | pimento '], timeout=1)
    # until the python3 input bug is fixed, and the warnings are removed, expect a warning message here
    if sys.version_info.major == 3:
        p.expect_exact('python3 input bug')
    p.expect_exact('Options:')
    p.expect_exact('  hello')
    p.expect_exact('  goodbye')
    p.expect_exact('Enter an option to continue: ')
    p.send('he')
    p.sendcontrol('i')
    # until the python3 input bug is fixed, expect an actual tab in python3
    i = p.expect_exact(['hello', pexpect.TIMEOUT])
    if sys.version_info.major == 2:
        assert i == 0
    else:
        assert i == 1
        return


#still need test for piping from and doing tab completion

# meant to make sure that the backspace doesn't clear the prompt line (issue #70),
# but I'm not sure how to test the erasure of terminal data with pexpect
#def test_backspace():
#    p = pexpect.spawn('pimento foo "foo bar" "foo bar baz"', timeout=1)
#    p.expect_exact('Options:')
#    p.expect_exact('  foo')
#    p.expect_exact('  foo bar')
#    p.expect_exact('  foo bar baz')
#    p.expect_exact('Enter an option to continue: ')
#    p.sendcontrol('h')
#    p.expect_exact('Enter an option to continue: ')

def test_fuzzy_option_tc_matching():
    '''
    Ensure that even when the correct matching for all initial arguments can't be determined
    until the final arg is evaluated, the correct matches come back.
    '''
    options = [
        'abcde bcda cdab dabc',
        'bcdaf abcdg cdab dabc',
        'bcda cdabf abcdh dabc',
        'bcda cdab dabcf abcdi',
    ]
    text = 'abcd'
    correct_matches = ['abcde', 'abcdg', 'abcdh', 'abcdi']
    matches = pimento._get_fuzzy_tc_matches(text, 'a b c ' + text, options)
    assert matches == correct_matches
    matches = pimento._get_fuzzy_tc_matches(text, 'a b d ' + text, options)
    assert matches == correct_matches
    matches = pimento._get_fuzzy_tc_matches(text, 'a b ' + text, options)
    assert matches == correct_matches
    matches = pimento._get_fuzzy_tc_matches(text, 'a ' + text, options)
    assert matches == correct_matches
    matches = pimento._get_fuzzy_tc_matches(text, text, options)
    assert matches == correct_matches
    matches = pimento._get_fuzzy_tc_matches(text, 'bc ab cd ' + text, options)
    assert matches == correct_matches

# [ Manual Interaction ]
if __name__ == '__main__':
    # create a menu with specific args - this is to functionally test specific API inputs which should
    # respond interactively
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--indexed-numbers', help='a numbered list of numbers',
                        action='store_true')
    group.add_argument('--tuple', help='use a tuple',
                        action='store_true')
    group.add_argument('--string', help='use a string',
                        action='store_true')
    group.add_argument('--dictionary', help='use a dictionary',
                        action='store_true')
    group.add_argument('--set', help='use a set',
                        action='store_true')
    group.add_argument('--pre-only', help='only a pre-prompt',
                        action='store_true')
    group.add_argument('--pre-only-default', help='only a pre-prompt with a default arg',
                        action='store_true')
    group.add_argument('--list-only', help='only a list of options',
                        action='store_true')
    args = parser.parse_args()
    if args.indexed_numbers:
        result = pimento.menu(['100', '200', '300'], "Select one of the following:", "Please select by index or value: ", indexed=True)
    elif args.tuple:
        result = pimento.menu(('100', '200', '300'), "Select one of the following:", "Please select: ")
    elif args.string:
        result = pimento.menu('abc', "Select one of the following:", "Please select: ")
    elif args.dictionary:
        result = pimento.menu({'key1': 'v1', 'key2': 'v2'}, "Select one of the following:", "Please select: ")
    elif args.set:
        result = pimento.menu(set([1, 2]), "Select one of the following:", "Please select: ")
    elif args.pre_only:
        result = pimento.menu([1, 2], "Select one of the following:", )
    elif args.pre_only_default:
        result = pimento.menu([1, 2], "Select one of the following:", default_index=0)
    elif args.list_only:
        result = pimento.menu([1, 2])
    print('Result is {}'.format(result))
