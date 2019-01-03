import dateutil
import pytest
from haralyzer import HarPage, HarParser
from haralyzer.compat import iteritems
from haralyzer.errors import PageNotFoundError
import re

BAD_PAGE_ID = 'sup_dawg'
PAGE_ID = 'page_3'


def test_init(har_data):
    """
    Test the object loading
    """
    with pytest.raises(ValueError):
        page = HarPage(PAGE_ID)

    init_data = har_data('humanssuck.net.har')

    # Throws PageNotFoundException with bad page ID
    with pytest.raises(PageNotFoundError):
        page = HarPage(BAD_PAGE_ID, har_data=init_data)

    # Make sure it can load with either har_data or a parser
    page = HarPage(PAGE_ID, har_data=init_data)
    assert isinstance(page, HarPage)
    parser = HarParser(init_data)
    page = HarPage(PAGE_ID, har_parser=parser)
    assert isinstance(page, HarPage)

    assert len(page.entries) == 4
    # Make sure that the entries are actually in order. Going a little bit
    # old school here.
    for index in range(0, len(page.entries)):
        if index != len(page.entries) - 1:
            current_date = dateutil.parser.parse(
                page.entries[index]['startedDateTime'])
            next_date = dateutil.parser.parse(
                page.entries[index + 1]['startedDateTime'])
            assert current_date <= next_date


def test_filter_entries(har_data):
    """
    Tests ability to filter entries, with or without regex
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    # Filter by request type only
    entries = page.filter_entries(request_type='.*ET')
    assert len(entries) == 4
    for entry in entries:
        assert entry['request']['method'] == 'GET'

    # Filter by request type and content_type
    entries = page.filter_entries(request_type='.*ET', content_type='image.*')
    assert len(entries) == 1
    for entry in entries:
        assert entry['request']['method'] == 'GET'
        for header in entry['response']['headers']:
            if header['name'] == 'Content-Type':
                assert re.search('image.*', header['value'])

    # Filter by request type, content type, and status code
    entries = page.filter_entries(request_type='.*ET', content_type='image.*',
                                  status_code='2.*')
    assert len(entries) == 1
    for entry in entries:
        assert entry['request']['method'] == 'GET'
        assert re.search('2.*', str(entry['response']['status']))
        for header in entry['response']['headers']:
            if header['name'] == 'Content-Type':
                assert re.search('image.*', header['value'])

    entries = page.filter_entries(request_type='.*ST')
    assert len(entries) == 0
    entries = page.filter_entries(request_type='.*ET', content_type='video.*')
    assert len(entries) == 0
    entries = page.filter_entries(request_type='.*ET', content_type='image.*',
                                  status_code='3.*')


def test_get_load_time(har_data):
    """
    Tests HarPage.get_load_time()
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    assert page.get_load_time(request_type='GET') == 463
    assert page.get_load_time(request_type='GET', async=False) == 843
    assert page.get_load_time(content_type='image.*') == 304
    assert page.get_load_time(status_code='2.*') == 463


def test_entries(har_data):
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    for entry in page.entries:
        assert entry['pageref'] == page.page_id


def test_file_types(har_data):
    """
    Test file type properties
    """
    init_data = har_data('cnn.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    file_types = {'image_files': ['image'], 'css_files': ['css'],
                  'js_files': ['javascript'], 'audio_files': ['audio'],
                  'video_files': ['video', 'flash'], 'text_files': ['text'],
                  'html_files': ['html']}

    for k, v in iteritems(file_types):
        for asset in getattr(page, k, None):
            assert _correct_file_type(asset, v)


def test_request_types(har_data):
    """
    Test request type filters
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    # Check request type lists
    for req in page.get_requests:
        assert req['request']['method'] == 'GET'

    for req in page.post_requests:
        assert req['request']['method'] == 'POST'

def test_sizes_trans(har_data):
    init_data = har_data('cnn-chrome.har')
    page = HarPage('page_1', har_data=init_data)

    assert page.page_size_trans == 2609508
    assert page.text_size_trans == 569814
    assert page.css_size_trans == 169573
    assert page.js_size_trans == 1600321
    assert page.image_size_trans == 492950
    # TODO - Get test data for audio and video
    assert page.audio_size_trans == 0
    assert page.video_size_trans == 0

def test_sizes(har_data):
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)

    assert page.page_size == 62204
    assert page.text_size == 246
    assert page.css_size == 8
    assert page.js_size == 38367
    assert page.image_size == 23591
    # TODO - Get test data for audio and video
    assert page.audio_size == 0
    assert page.video_size == 0


def test_load_times(har_data):
    """
    This whole test really needs better sample data. I need to make a
    web page with like 2-3 of each asset type to really test the load times.
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)
    # Check initial page load
    assert page.actual_page['request']['url'] == 'http://humanssuck.net/'

    # Check initial page load times
    assert page.initial_load_time == 153
    assert page.content_load_time == 543
    # Check content type browser (async) load times
    assert page.image_load_time == 304
    assert page.css_load_time == 76
    assert page.js_load_time == 310
    assert page.html_load_time == 153
    assert page.page_load_time == 567
    # TODO - Need to get sample data for these types
    assert page.audio_load_time == 0
    assert page.video_load_time == 0


def test_time_to_first_byte(har_data):
    """
    Tests that TTFB is correctly reported as a property of the page.
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)
    assert page.time_to_first_byte == 153


def test_hostname(har_data):
    """
    Makes sure that the correct hostname is returned.
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)
    assert page.hostname == 'humanssuck.net'


def test_url(har_data):
    """
    Makes sure that the correct URL is returned.
    """
    init_data = har_data('humanssuck.net.har')
    page = HarPage(PAGE_ID, har_data=init_data)
    assert page.url == 'http://humanssuck.net/'


def _correct_file_type(entry, file_types):
    for header in entry['response']['headers']:
        if header['name'] == 'Content-Type':
            return any(ft in header['value'] for ft in file_types)
