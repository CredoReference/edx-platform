"""
Functions for accessing and displaying courses within the
courseware.
"""
import logging
from collections import defaultdict
from datetime import datetime

import pytz
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from fs.errors import ResourceNotFoundError
from opaque_keys.edx.keys import UsageKey
from path import Path as path

import branding
from courseware.access import has_access
from courseware.date_summary import (
    CourseEndDate,
    CourseStartDate,
    TodaysDate,
    VerificationDeadlineDate,
    VerifiedUpgradeDeadlineDate
)
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module, get_module_for_descriptor
from edxmako.shortcuts import render_to_string
from lms.djangoapps.courseware.courseware_access_exception import CoursewareAccessException
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from static_replace import replace_static_urls
from student.models import CourseEnrollment
from credo_modules.models import CourseUsage
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.x_module import STUDENT_VIEW

log = logging.getLogger(__name__)


def get_course(course_id, depth=0):
    """
    Given a course id, return the corresponding course descriptor.

    If the course does not exist, raises a ValueError.  This is appropriate
    for internal use.

    depth: The number of levels of children for the modulestore to cache.
    None means infinite depth.  Default is to fetch no children.
    """
    course = modulestore().get_course(course_id, depth=depth)
    if course is None:
        raise ValueError(u"Course not found: {0}".format(course_id))
    return course


def get_course_by_id(course_key, depth=0):
    """
    Given a course id, return the corresponding course descriptor.

    If such a course does not exist, raises a 404.

    depth: The number of levels of children for the modulestore to cache. None means infinite depth
    """
    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=depth)
    if course:
        return course
    else:
        raise Http404("Course not found: {}.".format(unicode(course_key)))


def get_course_with_access(user, action, course_key, depth=0, check_if_enrolled=False):
    """
    Given a course_key, look up the corresponding course descriptor,
    check that the user has the access to perform the specified action
    on the course, and return the descriptor.

    Raises a 404 if the course_key is invalid, or the user doesn't have access.

    depth: The number of levels of children for the modulestore to cache. None means infinite depth

    check_if_enrolled: If true, additionally verifies that the user is either enrolled in the course
      or has staff access.
    """
    course = get_course_by_id(course_key, depth)
    check_course_access(course, user, action, check_if_enrolled)
    return course


def get_course_overview_with_access(user, action, course_key, check_if_enrolled=False):
    """
    Given a course_key, look up the corresponding course overview,
    check that the user has the access to perform the specified action
    on the course, and return the course overview.

    Raises a 404 if the course_key is invalid, or the user doesn't have access.

    check_if_enrolled: If true, additionally verifies that the user is either enrolled in the course
      or has staff access.
    """
    try:
        course_overview = CourseOverview.get_from_id(course_key)
    except CourseOverview.DoesNotExist:
        raise Http404("Course not found.")
    check_course_access(course_overview, user, action, check_if_enrolled)
    return course_overview


def check_course_access(course, user, action, check_if_enrolled=False):
    """
    Check that the user has the access to perform the specified action
    on the course (CourseDescriptor|CourseOverview).

    check_if_enrolled: If true, additionally verifies that the user is either
    enrolled in the course or has staff access.
    """
    access_response = has_access(user, action, course, course.id)

    if not access_response:
        # Deliberately return a non-specific error message to avoid
        # leaking info about access control settings
        raise CoursewareAccessException(access_response)

    if check_if_enrolled:
        # Verify that the user is either enrolled in the course or a staff
        # member.  If the user is not enrolled, raise a Redirect exception
        # that will be handled by middleware.
        if not ((user.id and CourseEnrollment.is_enrolled(user, course.id)) or has_access(user, 'staff', course)):
            raise CourseAccessRedirect(reverse('about_course', args=[unicode(course.id)]))


def find_file(filesystem, dirs, filename):
    """
    Looks for a filename in a list of dirs on a filesystem, in the specified order.

    filesystem: an OSFS filesystem
    dirs: a list of path objects
    filename: a string

    Returns d / filename if found in dir d, else raises ResourceNotFoundError.
    """
    for directory in dirs:
        filepath = path(directory) / filename
        if filesystem.exists(filepath):
            return filepath
    raise ResourceNotFoundError(u"Could not find {0}".format(filename))


def get_course_about_section(request, course, section_key):
    """
    This returns the snippet of html to be rendered on the course about page,
    given the key for the section.

    Valid keys:
    - overview
    - short_description
    - description
    - key_dates (includes start, end, exams, etc)
    - video
    - course_staff_short
    - course_staff_extended
    - requirements
    - syllabus
    - textbook
    - faq
    - effort
    - more_info
    - ocw_links
    """

    # Many of these are stored as html files instead of some semantic
    # markup. This can change without effecting this interface when we find a
    # good format for defining so many snippets of text/html.

    html_sections = {
        'short_description',
        'description',
        'key_dates',
        'video',
        'course_staff_short',
        'course_staff_extended',
        'requirements',
        'syllabus',
        'textbook',
        'faq',
        'more_info',
        'overview',
        'effort',
        'end_date',
        'prerequisites',
        'ocw_links'
    }

    if section_key in html_sections:
        try:
            loc = course.location.replace(category='about', name=section_key)

            # Use an empty cache
            field_data_cache = FieldDataCache([], course.id, request.user)
            about_module = get_module(
                request.user,
                request,
                loc,
                field_data_cache,
                log_if_not_found=False,
                wrap_xmodule_display=False,
                static_asset_path=course.static_asset_path,
                course=course
            )

            html = ''

            if about_module is not None:
                try:
                    html = about_module.render(STUDENT_VIEW).content
                except Exception:  # pylint: disable=broad-except
                    html = render_to_string('courseware/error-message.html', None)
                    log.exception(
                        u"Error rendering course=%s, section_key=%s",
                        course, section_key
                    )
            return html

        except ItemNotFoundError:
            log.warning(
                u"Missing about section %s in course %s",
                section_key, course.location.to_deprecated_string()
            )
            return None

    raise KeyError("Invalid about key " + str(section_key))


def get_course_info_usage_key(course, section_key):
    """
    Returns the usage key for the specified section's course info module.
    """
    return course.id.make_usage_key('course_info', section_key)


def get_course_info_section_module(request, user, course, section_key):
    """
    This returns the course info module for a given section_key.

    Valid keys:
    - handouts
    - guest_handouts
    - updates
    - guest_updates
    """
    usage_key = get_course_info_usage_key(course, section_key)

    # Use an empty cache
    field_data_cache = FieldDataCache([], course.id, user)

    return get_module(
        user,
        request,
        usage_key,
        field_data_cache,
        log_if_not_found=False,
        wrap_xmodule_display=False,
        static_asset_path=course.static_asset_path,
        course=course
    )


def get_course_info_section(request, user, course, section_key):
    """
    This returns the snippet of html to be rendered on the course info page,
    given the key for the section.

    Valid keys:
    - handouts
    - guest_handouts
    - updates
    - guest_updates
    """
    info_module = get_course_info_section_module(request, user, course, section_key)

    html = ''
    if info_module is not None:
        try:
            html = info_module.render(STUDENT_VIEW).content.strip()
        except Exception:  # pylint: disable=broad-except
            html = render_to_string('courseware/error-message.html', None)
            log.exception(
                u"Error rendering course_id=%s, section_key=%s",
                unicode(course.id), section_key
            )

    return html


def get_course_date_blocks(course, user):
    """
    Return the list of blocks to display on the course info page,
    sorted by date.
    """
    block_classes = (
        CourseEndDate,
        CourseStartDate,
        TodaysDate,
        VerificationDeadlineDate,
        VerifiedUpgradeDeadlineDate,
    )

    blocks = (cls(course, user) for cls in block_classes)

    def block_key_fn(block):
        """
        If the block's date is None, return the maximum datetime in order
        to force it to the end of the list of displayed blocks.
        """
        if block.date is None:
            return datetime.max.replace(tzinfo=pytz.UTC)
        return block.date
    return sorted((b for b in blocks if b.is_enabled), key=block_key_fn)


# TODO: Fix this such that these are pulled in as extra course-specific tabs.
#       arjun will address this by the end of October if no one does so prior to
#       then.
def get_course_syllabus_section(course, section_key):
    """
    This returns the snippet of html to be rendered on the syllabus page,
    given the key for the section.

    Valid keys:
    - syllabus
    - guest_syllabus
    """

    # Many of these are stored as html files instead of some semantic
    # markup. This can change without effecting this interface when we find a
    # good format for defining so many snippets of text/html.

    if section_key in ['syllabus', 'guest_syllabus']:
        try:
            filesys = course.system.resources_fs
            # first look for a run-specific version
            dirs = [path("syllabus") / course.url_name, path("syllabus")]
            filepath = find_file(filesys, dirs, section_key + ".html")
            with filesys.open(filepath) as html_file:
                return replace_static_urls(
                    html_file.read().decode('utf-8'),
                    getattr(course, 'data_dir', None),
                    course_id=course.id,
                    static_asset_path=course.static_asset_path,
                )
        except ResourceNotFoundError:
            log.exception(
                u"Missing syllabus section %s in course %s",
                section_key, course.location.to_deprecated_string()
            )
            return "! Syllabus missing !"

    raise KeyError("Invalid about key " + str(section_key))


def get_courses(user, org=None, filter_=None):
    """
    Returns a list of courses available, sorted by course.number and optionally
    filtered by org code (case-insensitive).
    """
    courses = branding.get_visible_courses(org=org, filter_=filter_)

    permission_name = configuration_helpers.get_value(
        'COURSE_CATALOG_VISIBILITY_PERMISSION',
        settings.COURSE_CATALOG_VISIBILITY_PERMISSION
    )

    courses = [c for c in courses if has_access(user, permission_name, c)]

    return courses


def get_permission_for_course_about():
    """
    Returns the CourseOverview object for the course after checking for access.
    """
    return configuration_helpers.get_value(
        'COURSE_ABOUT_VISIBILITY_PERMISSION',
        settings.COURSE_ABOUT_VISIBILITY_PERMISSION
    )


def sort_by_announcement(courses):
    """
    Sorts a list of courses by their announcement date. If the date is
    not available, sort them by their start date.
    """

    # Sort courses by how far are they from they start day
    key = lambda course: course.sorting_score
    courses = sorted(courses, key=key)

    return courses


def sort_by_start_date(courses):
    """
    Returns a list of courses sorted by their start date, latest first.
    """
    courses = sorted(
        courses,
        key=lambda course: (course.has_ended(), course.start is None, course.start),
        reverse=False
    )

    return courses


def get_cms_course_link(course, page='course'):
    """
    Returns a link to course_index for editing the course in cms,
    assuming that the course is actually cms-backed.
    """
    # This is fragile, but unfortunately the problem is that within the LMS we
    # can't use the reverse calls from the CMS
    return u"//{}/{}/{}".format(settings.CMS_BASE, page, unicode(course.id))


def get_cms_block_link(block, page):
    """
    Returns a link to block_index for editing the course in cms,
    assuming that the block is actually cms-backed.
    """
    # This is fragile, but unfortunately the problem is that within the LMS we
    # can't use the reverse calls from the CMS
    return u"//{}/{}/{}".format(settings.CMS_BASE, page, block.location)


def get_studio_url(course, page):
    """
    Get the Studio URL of the page that is passed in.

    Args:
        course (CourseDescriptor)
    """
    studio_link = None
    if course.course_edit_method == "Studio":
        studio_link = get_cms_course_link(course, page)
    return studio_link


def get_problems_in_section(section):
    """
    This returns a dict having problems in a section.
    Returning dict has problem location as keys and problem
    descriptor as values.
    """

    problem_descriptors = defaultdict()
    if not isinstance(section, UsageKey):
        section_key = UsageKey.from_string(section)
    else:
        section_key = section
    # it will be a Mongo performance boost, if you pass in a depth=3 argument here
    # as it will optimize round trips to the database to fetch all children for the current node
    section_descriptor = modulestore().get_item(section_key, depth=3)

    # iterate over section, sub-section, vertical
    for subsection in section_descriptor.get_children():
        for vertical in subsection.get_children():
            for component in vertical.get_children():
                if component.location.category == 'problem' and getattr(component, 'has_score', False):
                    problem_descriptors[unicode(component.location)] = component

    return problem_descriptors


def get_current_child(xmodule, min_depth=None, requested_child=None):
    """
    Get the xmodule.position's display item of an xmodule that has a position and
    children.  If xmodule has no position or is out of bounds, return the first
    child with children of min_depth.

    For example, if chapter_one has no position set, with two child sections,
    section-A having no children and section-B having a discussion unit,
    `get_current_child(chapter, min_depth=1)`  will return section-B.

    Returns None only if there are no children at all.
    """
    # TODO: convert this method to use the Course Blocks API
    def _get_child(children):
        """
        Returns either the first or last child based on the value of
        the requested_child parameter.  If requested_child is None,
        returns the first child.
        """
        if requested_child == 'first':
            return children[0]
        elif requested_child == 'last':
            return children[-1]
        else:
            return children[0]

    def _get_default_child_module(child_modules):
        """Returns the first child of xmodule, subject to min_depth."""
        if min_depth <= 0:
            return _get_child(child_modules)
        else:
            content_children = [
                child for child in child_modules
                if child.has_children_at_depth(min_depth - 1) and child.get_display_items()
            ]
            return _get_child(content_children) if content_children else None

    child = None
    if hasattr(xmodule, 'position'):
        children = xmodule.get_display_items()
        if len(children) > 0:
            if xmodule.position is not None and not requested_child:
                pos = xmodule.position - 1  # position is 1-indexed
                if 0 <= pos < len(children):
                    child = children[pos]
                    if min_depth > 0 and not child.has_children_at_depth(min_depth - 1):
                        child = None
            if child is None:
                child = _get_default_child_module(children)

    return child


def can_self_enroll_in_course(course_key):
    """
    Returns True if the user can enroll themselves in a course.

    Note: an example of a course that a user cannot enroll in directly
    is a CCX course. For such courses, a user can only be enrolled by
    a CCX coach.
    """
    if hasattr(course_key, 'ccx'):
        return False
    return True


def update_lms_course_usage(request, usage_key, course_key):
    if request.method == 'HEAD':
        return

    item = None
    block_type = ''
    max_attempts = 10
    num_attempt = 0

    while block_type != 'course' and num_attempt < max_attempts:
        if item is None:
            item = modulestore().get_item(usage_key)
            if item.category == 'sequential':
                add_vertical_usage(item, request, course_key)
        CourseUsage.update_block_usage(request, course_key, item.location)
        item = item.get_parent()
        block_type = item.category
        num_attempt = num_attempt + 1


def add_vertical_usage(item, request, course_key):
    activate_block_id = request.GET.get('activate_block_id')
    if activate_block_id:
        try:
            item = modulestore().get_item(UsageKey.from_string(activate_block_id))
            CourseUsage.update_block_usage(request, course_key, item.location)
            return
        except ItemNotFoundError:
            pass

    course = get_course_by_id(course_key, depth=1)
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, item, depth=2
    )
    course_module = get_module_for_descriptor(
        request.user, request, item, field_data_cache, course.id, course=course
    )
    if course_module is not None:
        real_position = (course_module.position - 1) if course_module.position else 0
        try:
            child = course_module.get_children()[real_position]
            CourseUsage.update_block_usage(request, course_key, child.location)
        except IndexError:
            pass
