# -*- coding: utf-8 -*-

#
# Newfies-Dialer License
# http://www.newfies-dialer.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.conf.urls import patterns, url, include
from rest_framework import routers

from apirest.view_contenttype import ContentTypeViewSet
from apirest.view_user import UserViewSet
from apirest.view_audiofile import AudioFileViewSet
from apirest.view_dnc import DNCViewSet
from apirest.view_dnc_contact import DNCContactViewSet
from apirest.view_gateway import GatewayViewSet
from apirest.view_phonebook import PhonebookViewSet
from apirest.view_contact import ContactViewSet
from apirest.view_campaign import CampaignViewSet
from apirest.view_subscriber import SubscriberViewSet
from apirest.view_bulk_contact import BulkContactViewSet
from apirest.view_callrequest import CallrequestViewSet
from apirest.view_survey_template import SurveyTemplateViewSet
from apirest.view_survey import SurveyViewSet
from apirest.view_section_template import SectionTemplateViewSet
from apirest.view_branching_template import BranchingTemplateViewSet
from apirest.view_survey_aggregate_result import SurveyAggregateResultViewSet
from apirest.view_subscriber_per_campaign import SubscriberPerCampaignList
from apirest.view_queue import QueueViewSet
from apirest.view_tier import TierViewSet
from apirest.view_calendar import CalendarViewSet
from apirest.view_calendar_setting import CalendarSettingViewSet
from apirest.view_calendar_user import CalendarUserViewSet
from apirest.view_calendar_user_profile import CalendarUserProfileViewSet
from apirest.view_rule import RuleViewSet
from apirest.view_event import EventViewSet

from agent.api_views import AgentViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'campaigns', CampaignViewSet)
router.register(r'audio_files', AudioFileViewSet)
router.register(r'dnc', DNCViewSet)
router.register(r'dnc_contact', DNCContactViewSet)
router.register(r'gateway', GatewayViewSet)
router.register(r'content_type', ContentTypeViewSet)
router.register(r'phonebook', PhonebookViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'subscriber', SubscriberViewSet)
router.register(r'callrequest', CallrequestViewSet)
router.register(r'survey_template', SurveyTemplateViewSet)

# frozen survey
router.register(r'frozen-survey', SurveyViewSet)

router.register(r'section_template', SectionTemplateViewSet)
router.register(r'branching_template', BranchingTemplateViewSet)
router.register(r'queue', QueueViewSet)
router.register(r'tier', TierViewSet)
router.register(r'calendar', CalendarViewSet)
router.register(r'calendar-setting', CalendarSettingViewSet)
router.register(r'calendar-user', CalendarUserViewSet)
router.register(r'calendar-user-profile', CalendarUserProfileViewSet)
router.register(r'rule', RuleViewSet)
router.register(r'event', EventViewSet)

router.register(r'agents', AgentViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^rest-api/subcampaign/$', SubscriberPerCampaignList.as_view(), name="subscriber_campaign"),
    url(r'^rest-api/subcampaign/(?P<campaign_id>[0-9]+)/$', SubscriberPerCampaignList.as_view(), name="subscriber_campaign"),
    url(r'^rest-api/subcampaign/(?P<campaign_id>[0-9]+)/(?P<contact_id>[0-9]+)/$', SubscriberPerCampaignList.as_view(), name="subscriber_campaign"),

    url(r'^rest-api/surveyaggregate/$', SurveyAggregateResultViewSet.as_view(), name="survey_aggregate_result"),
    url(r'^rest-api/surveyaggregate/(?P<campaign_id>[0-9]+)/$', SurveyAggregateResultViewSet.as_view(), name="survey_aggregate_result"),

    url(r'^rest-api/bulkcontact/$', BulkContactViewSet.as_view(), name="bulk_contact"),

    url(r'^rest-api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
)