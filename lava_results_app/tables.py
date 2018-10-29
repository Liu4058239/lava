# -*- coding: utf-8 -*-
# Copyright (C) 2015-2018 Linaro Limited
#
# Author: Neil Williams <neil.williams@linaro.org>
#         Stevan Radakovic <stevan.radakovic@linaro.org>
#
# This file is part of LAVA.
#
# LAVA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# LAVA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with LAVA.  If not, see <http://www.gnu.org/licenses/>.

import django_tables2 as tables

from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from django.utils.html import escape

from lava.utils.lavatable import LavaTable
from lava_scheduler_app.tables import RestrictedIDLinkColumn
from lava_results_app.models import (
    TestCase,
    BugLink,
    TestSuite
)


def results_pklink(record):
    job_id = record.pk
    complete = '<a class="btn btn-xs btn-success pull-right" title="test job results" href="%s">' % record.results_link
    button = '<span class="glyphicon glyphicon-signal"></span></a>'
    return mark_safe(
        '<a href="%s" title="test job summary">%s</a>&nbsp;%s%s' % (
            record.get_absolute_url(),
            escape(job_id), complete, button))


class IndexResultsColumn(RestrictedIDLinkColumn):

    def render(self, record, table=None):
        user = table.context.get('request').user
        if record.job.can_view(user):
            return results_pklink(record.job)
        else:
            return record.job.pk


class ResultsTable(LavaTable):
    """
    List of LAVA TestSuite results
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.length = 25

    def _check_job(self, record, table=None):  # pylint: disable=no-self-use
        """
        Slightly different purpose to RestrictedIDLinkColumn.render
        """
        user = table.context.get('request').user
        return bool(record.job.can_view(user))

    def render_submitter(self, record, table=None):
        if not self._check_job(record, table):
            return 'Unavailable'
        return record.job.submitter

    def render_passes(self, record, table=None):
        if not self._check_job(record, table):
            return ''
        return record.testcase_count('pass')

    def render_fails(self, record, table=None):
        if not self._check_job(record, table):
            return ''
        return record.testcase_count('fail')

    def render_total(self, record, table=None):
        if not self._check_job(record, table):
            return ''
        return TestCase.objects.filter(
            suite__job=record.job,
            suite=record,
        ).count()

    def render_logged(self, record, table=None):
        if not self._check_job(record, table):
            return ''
        if not TestCase.objects.filter(
                suite__job=record.job,
                suite=record):
            return record.job.start_time
        return TestCase.objects.filter(
            suite__job=record.job,
            suite=record,
        )[0].logged

    def render_buglinks(self, record, table=None):

        suite_links_count = BugLink.objects.filter(
            content_type=ContentType.objects.get_for_model(TestSuite),
            object_id=record.id).count()
        case_links_count = BugLink.objects.filter(
            content_type=ContentType.objects.get_for_model(TestCase),
            object_id__in=TestCase.objects.filter(
                suite=record)).count()

        user = table.context.get('request').user
        if not user.is_anonymous():
            return mark_safe(
                '<a href="#" class="buglink" id="buglink_%s" data-content-type="%s">[%s]</a> (%s)' % (
                    record.id,
                    ContentType.objects.get_for_model(TestSuite).id,
                    suite_links_count,
                    case_links_count
                )
            )
        else:
            return mark_safe(
                '[%s] (%s)' % (
                    suite_links_count,
                    case_links_count
                )
            )

    job_id = tables.Column(verbose_name='Job ID')
    actions = tables.TemplateColumn(
        template_name="lava_results_app/results_actions_field.html")
    actions.orderable = False
    submitter = tables.Column(accessor='job.submitter')
    name = tables.Column(verbose_name='Test Suite')
    passes = tables.Column(accessor='job', verbose_name='Passes')
    fails = tables.Column(accessor='job', verbose_name='Fails')
    total = tables.Column(accessor='job', verbose_name='Totals')
    logged = tables.Column(accessor='job', verbose_name='Logged')
    buglinks = tables.Column(accessor='job', verbose_name='Bug Links')
    buglinks.orderable = False

    class Meta(LavaTable.Meta):  # pylint: disable=no-init,too-few-public-methods
        searches = {
            'name': 'contains'
        }
        sequence = {
            'job_id', 'actions'
        }


class ResultsIndexTable(ResultsTable):

    job_id = tables.Column(verbose_name='Job ID')
    submitter = tables.Column(accessor='job.submitter')
    name = tables.Column(verbose_name='Test Suite')
    passes = tables.Column(accessor='job', verbose_name='Passes')
    fails = tables.Column(accessor='job', verbose_name='Fails')
    total = tables.Column(accessor='job', verbose_name='Totals')
    logged = tables.Column(accessor='job', verbose_name='Logged')

    class Meta(LavaTable.Meta):  # pylint: disable=no-init,too-few-public-methods
        searches = {
            'name': 'contains'
        }


class TestJobResultsTable(ResultsTable):

    job_id = tables.Column(verbose_name='Job ID')
    actions = tables.TemplateColumn(
        template_name="lava_results_app/suite_actions_field.html")
    actions.orderable = False
    submitter = tables.Column(accessor='job.submitter')
    name = tables.Column(verbose_name='Test Suite')
    passes = tables.Column(accessor='job', verbose_name='Passes')
    fails = tables.Column(accessor='job', verbose_name='Fails')
    total = tables.Column(accessor='job', verbose_name='Totals')
    logged = tables.Column(accessor='job', verbose_name='Logged')

    class Meta(LavaTable.Meta):  # pylint: disable=no-init,too-few-public-methods
        searches = {
            'name': 'contains'
        }


class SuiteTable(LavaTable):
    """
    Details of the test sets or test cases in a test suite
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.length = 25

    name = tables.Column()
    test_set = tables.Column(verbose_name="Test Set")
    result = tables.Column()
    measurement = tables.Column()
    units = tables.Column()
    logged = tables.DateTimeColumn()
    buglinks = tables.Column(accessor='suite', verbose_name='Bug Links')
    buglinks.orderable = False

    def render_name(self, record):  # pylint: disable=no-self-use
        return mark_safe(
            '<a href="%s">%s</a>' % (record.get_absolute_url(), record.name)
        )

    def render_result(self, record):  # pylint: disable=no-self-use
        code = record.result_code
        if code == 'pass':
            icon = 'ok'
        elif code == 'fail':
            icon = 'remove'
        else:
            icon = 'minus'
        return mark_safe(
            '<a href="%s"><span class="glyphicon glyphicon-%s"></span> %s</a>' % (
                record.get_absolute_url(), icon, code)
        )

    def render_test_set(self, record):  # pylint: disable=no-self-use
        return mark_safe(
            '<a href="%s">%s</a>' % (
                record.test_set.get_absolute_url(), record.test_set.name
            )
        )

    def render_buglinks(self, record, table=None):  # pylint: disable=no-self-use
        case_links_count = BugLink.objects.filter(
            content_type=ContentType.objects.get_for_model(TestCase),
            object_id=record.id).count()

        user = table.context.get('request').user
        if not user.is_anonymous():
            return mark_safe(
                '<a href="#" class="buglink" id="buglink_%s" data-content-type="%s">[%s]</a>' % (
                    record.id,
                    ContentType.objects.get_for_model(TestCase).id,
                    case_links_count
                ))
        else:
            return mark_safe(
                '[%s]' % (
                    case_links_count
                )
            )

    class Meta(LavaTable.Meta):  # pylint: disable=no-init,too-few-public-methods
        searches = {
            'name': 'contains'
        }
