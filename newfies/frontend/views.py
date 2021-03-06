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

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required,\
    permission_required
from django.contrib.auth.views import password_reset, password_reset_done,\
    password_reset_confirm, password_reset_complete
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.db.models import Sum, Avg, Count
from django.conf import settings
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from dialer_contact.models import Contact
from dialer_contact.constants import CONTACT_STATUS
from dialer_campaign.models import Campaign, Subscriber
from dialer_campaign.function_def import date_range, \
    user_dialer_setting_msg
from dialer_cdr.models import VoIPCall
from dialer_cdr.constants import VOIPCALL_DISPOSITION
from frontend.forms import LoginForm, DashboardForm
from frontend.function_def import calculate_date
from frontend.constants import COLOR_DISPOSITION, SEARCH_TYPE
from common.common_functions import current_view
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import logging


def logout_view(request):
    try:
        del request.session['has_notified']
    except KeyError:
        pass

    logout(request)
    # set language cookie
    response = HttpResponseRedirect('/')
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME,
                        request.LANGUAGE_CODE)
    return response


def login_view(request):
    """Check User credentials

    **Attributes**:

        * ``form`` - LoginForm
        * ``template`` - frontend/index.html

    **Logic Description**:

        * Submitted user credentials need to be checked. If it is not valid
          then the system will redirect to the login page.
        * If submitted user credentials are valid then system will redirect to
          the dashboard.
    """
    template = 'frontend/index.html'
    errorlogin = ''

    if request.method == 'POST':
        loginform = LoginForm(request.POST)
        if loginform.is_valid():
            cd = loginform.cleaned_data
            user = authenticate(username=cd['user'],
                                password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    request.session['has_notified'] = False
                    # Redirect to a success page (dashboard).
                    return HttpResponseRedirect('/dashboard/')
                else:
                    # Return a 'disabled account' error message
                    errorlogin = _('disabled account')
            else:
                # Return an 'invalid login' error message.
                errorlogin = _('invalid login.')
        else:
            # Return an 'Valid User Credentials' error message.
            errorlogin = _('enter valid user credentials.')
    else:
        loginform = LoginForm()

    data = {
        'module': current_view(request),
        'loginform': loginform,
        'errorlogin': errorlogin,
        'is_authenticated': request.user.is_authenticated(),
        'dialer_setting_msg': user_dialer_setting_msg(request.user),
    }

    return render_to_response(template, data,
           context_instance=RequestContext(request))


def index(request):
    """Index view of the Customer Interface

    **Attributes**:

        * ``form`` - LoginForm
        * ``template`` - frontend/index.html
    """
    template = 'frontend/index.html'
    errorlogin = ''
    data = {
        'module': current_view(request),
        'user': request.user,
        'loginform': LoginForm(),
        'errorlogin': errorlogin,
        'dialer_setting_msg': user_dialer_setting_msg(request.user),
    }

    return render_to_response(template, data,
           context_instance=RequestContext(request))


def pleaselog(request):
    template = 'frontend/index.html'

    data = {
        'loginform': LoginForm(),
        'notlogged': True,
    }
    return render_to_response(template, data,
           context_instance=RequestContext(request))


@permission_required('dialer_campaign.view_dashboard', login_url='/')
@login_required
def customer_dashboard(request, on_index=None):
    """Customer dashboard gives the following information

        * No of Campaigns for logged in user
        * Total phonebook contacts
        * Total Campaigns contacts
        * Amount of contact reached today
        * Disposition of calls via pie chart
        * Call records & Duration of calls are shown on graph by days/hours

    **Attributes**:

        * ``template`` - frontend/dashboard.html
        * ``form`` - DashboardForm
    """
    logging.debug('Start Dashboard')
    # All campaign for logged in User
    campaign_id_list = Campaign.objects.values_list('id', flat=True)\
        .filter(user=request.user).order_by('id')
    campaign_count = campaign_id_list.count()

    # Contacts count which are active and belong to those phonebook(s) which is
    # associated with all campaign
    pb_active_contact_count = Contact.objects\
        .filter(phonebook__campaign__in=campaign_id_list, status=CONTACT_STATUS.ACTIVE)\
        .count()

    total_of_phonebook_contacts =\
        Contact.objects.filter(phonebook__user=request.user).count()

    form = DashboardForm(request.user)
    logging.debug('Got Campaign list')

    total_record = dict()
    total_duration_sum = 0
    total_call_count = 0
    total_answered = 0
    total_not_answered = 0
    total_busy = 0
    total_cancel = 0
    total_congestion = 0
    total_failed = 0
    search_type = SEARCH_TYPE.D_Last_24_hours  # default Last 24 hours
    selected_campaign = ''

    if campaign_id_list:
        selected_campaign = campaign_id_list[0]  # default campaign id

    # selected_campaign should not be empty
    if selected_campaign:
        if request.method == 'POST':
            form = DashboardForm(request.user, request.POST)
            selected_campaign = request.POST['campaign']
            search_type = request.POST['search_type']

        end_date = datetime.today()
        start_date = calculate_date(search_type)

        # date_length is used to do group by starting_date
        if int(search_type) >= SEARCH_TYPE.B_Last_7_days:  # all options except 30 days
            date_length = 13
            if int(search_type) == SEARCH_TYPE.C_Yesterday:  # yesterday
                now = datetime.now()
                start_date = datetime(now.year,
                                      now.month,
                                      now.day,
                                      0, 0, 0, 0) - relativedelta(days=1)
                end_date = datetime(now.year,
                                    now.month,
                                    now.day,
                                    23, 59, 59, 999999) - relativedelta(days=1)
            if int(search_type) >= SEARCH_TYPE.E_Last_12_hours:
                date_length = 16
        else:
            date_length = 10  # Last 30 days option

        select_data = {
            "starting_date": "SUBSTR(CAST(starting_date as CHAR(30)),1,%s)" % str(date_length)
        }

        # This calls list is used by pie chart
        calls = VoIPCall.objects\
            .filter(callrequest__campaign=selected_campaign,
                duration__isnull=False,
                user=request.user,
                starting_date__range=(start_date, end_date))\
            .extra(select=select_data)\
            .values('starting_date', 'disposition')\
            .annotate(Count('starting_date'))\
            .order_by('starting_date')

        logging.debug('Aggregate VoIPCall')

        for i in calls:
            total_call_count += i['starting_date__count']
            if (i['disposition'] == VOIPCALL_DISPOSITION.ANSWER
               or i['disposition'] == 'NORMAL_CLEARING'):
                total_answered += i['starting_date__count']
            elif (i['disposition'] == VOIPCALL_DISPOSITION.BUSY
               or i['disposition'] == 'USER_BUSY'):
                total_busy += i['starting_date__count']
            elif (i['disposition'] == VOIPCALL_DISPOSITION.NOANSWER
               or i['disposition'] == 'NO_ANSWER'):
                total_not_answered += i['starting_date__count']
            elif (i['disposition'] == VOIPCALL_DISPOSITION.CANCEL
               or i['disposition'] == 'ORIGINATOR_CANCEL'):
                total_cancel += i['starting_date__count']
            elif (i['disposition'] == VOIPCALL_DISPOSITION.CONGESTION
               or i['disposition'] == 'NORMAL_CIRCUIT_CONGESTION'):
                total_congestion += i['starting_date__count']
            else:
                #VOIP CALL FAILED
                total_failed += i['starting_date__count']

        # following calls list is without disposition & group by call date
        calls = VoIPCall.objects\
            .filter(callrequest__campaign=selected_campaign,
                duration__isnull=False,
                user=request.user,
                starting_date__range=(start_date, end_date))\
            .extra(select=select_data)\
            .values('starting_date').annotate(Sum('duration'))\
            .annotate(Avg('duration'))\
            .annotate(Count('starting_date'))\
            .order_by('starting_date')

        logging.debug('Aggregate VoIPCall (2)')

        mintime = start_date
        maxtime = end_date
        calls_dict = {}
        calls_dict_with_min = {}

        for data in calls:
            if int(search_type) >= SEARCH_TYPE.B_Last_7_days:
                ctime = datetime(int(data['starting_date'][0:4]),
                                 int(data['starting_date'][5:7]),
                                 int(data['starting_date'][8:10]),
                                 int(data['starting_date'][11:13]),
                                 0,
                                 0,
                                 0)
                if int(search_type) >= SEARCH_TYPE.E_Last_12_hours:
                    ctime = datetime(int(data['starting_date'][0:4]),
                                     int(data['starting_date'][5:7]),
                                     int(data['starting_date'][8:10]),
                                     int(data['starting_date'][11:13]),
                                     int(data['starting_date'][14:16]),
                                     0,
                                     0)
            else:
                ctime = datetime(int(data['starting_date'][0:4]),
                                 int(data['starting_date'][5:7]),
                                 int(data['starting_date'][8:10]),
                                 0,
                                 0,
                                 0,
                                 0)
            if ctime > maxtime:
                maxtime = ctime
            elif ctime < mintime:
                mintime = ctime

            # all options except 30 days
            if int(search_type) >= SEARCH_TYPE.B_Last_7_days:
                calls_dict[int(ctime.strftime("%Y%m%d%H"))] =\
                    {
                        'call_count': data['starting_date__count'],
                        'duration_sum': data['duration__sum'],
                        'duration_avg': float(data['duration__avg']),
                    }

                calls_dict_with_min[int(ctime.strftime("%Y%m%d%H%M"))] =\
                    {
                        'call_count': data['starting_date__count'],
                        'duration_sum': data['duration__sum'],
                        'duration_avg': float(data['duration__avg']),
                    }
            else:
                # Last 30 days option
                calls_dict[int(ctime.strftime("%Y%m%d"))] =\
                    {
                        'call_count': data['starting_date__count'],
                        'duration_sum': data['duration__sum'],
                        'duration_avg': float(data['duration__avg']),
                    }

        logging.debug('After Call Loops')

        dateList = date_range(mintime, maxtime, q=search_type)

        for date in dateList:
            inttime = int(date.strftime("%Y%m%d"))

            # last 7 days | yesterday | last 24 hrs
            if int(search_type) == SEARCH_TYPE.B_Last_7_days \
                or int(search_type) == SEARCH_TYPE.C_Yesterday \
                    or int(search_type) == SEARCH_TYPE.D_Last_24_hours:

                for option in range(0, 24):
                    day_time = int(str(inttime) + str(option).zfill(2))

                    graph_day = datetime(int(date.strftime("%Y")),
                                         int(date.strftime("%m")),
                                         int(date.strftime("%d")),
                                         int(str(option).zfill(2)))

                    dt = int(1000 * time.mktime(graph_day.timetuple()))
                    total_record[dt] = {
                        'call_count': 0,
                        'duration_sum': 0,
                        'duration_avg': 0.0,
                    }

                    if day_time in calls_dict.keys():
                        total_record[dt]['call_count'] += calls_dict[day_time]['call_count']
                        total_record[dt]['duration_sum'] += calls_dict[day_time]['duration_sum']
                        total_record[dt]['duration_avg'] += float(calls_dict[day_time]['duration_avg'])

            # last 12 hrs | last 6 hrs | last 1 hrs
            elif (int(search_type) == SEARCH_TYPE.E_Last_12_hours
                 or int(search_type) == SEARCH_TYPE.F_Last_6_hours
                 or int(search_type) == SEARCH_TYPE.G_Last_hour):

                for hour in range(0, 24):
                    for minute in range(0, 60):
                        hr_time = int(str(inttime) + str(hour).zfill(2) + str(minute).zfill(2))

                        graph_day = datetime(int(date.strftime("%Y")),
                                             int(date.strftime("%m")),
                                             int(date.strftime("%d")),
                                             int(str(hour).zfill(2)),
                                             int(str(minute).zfill(2)))

                        dt = int(1000 * time.mktime(graph_day.timetuple()))
                        total_record[dt] = {
                            'call_count': 0,
                            'duration_sum': 0,
                            'duration_avg': 0.0,
                        }

                        if hr_time in calls_dict_with_min.keys():
                            total_record[dt]['call_count'] += calls_dict_with_min[hr_time]['call_count']
                            total_record[dt]['duration_sum'] += calls_dict_with_min[hr_time]['duration_sum']
                            total_record[dt]['duration_avg'] += float(calls_dict_with_min[hr_time]['duration_avg'])
            else:
                # Last 30 days option
                graph_day = datetime(int(date.strftime("%Y")),
                                     int(date.strftime("%m")),
                                     int(date.strftime("%d")))
                dt = int(1000 * time.mktime(graph_day.timetuple()))
                total_record[dt] = {
                    'call_count': 0,
                    'duration_sum': 0,
                    'duration_avg': 0,
                }
                if inttime in calls_dict.keys():
                    total_record[dt]['call_count'] += calls_dict[inttime]['call_count']
                    total_record[dt]['duration_sum'] += calls_dict[inttime]['duration_sum']
                    total_record[dt]['duration_avg'] += float(calls_dict[inttime]['duration_avg'])

    logging.debug('After dateList Loops')

    # sorting on date col
    total_record = total_record.items()
    total_record = sorted(total_record, key=lambda k: k[0])

    # Contacts which are successfully called for running campaign
    reached_contact = 0
    if campaign_id_list:
        now = datetime.now()
        start_date = datetime(now.year, now.month, now.day, 0, 0, 0, 0)
        end_date = datetime(now.year, now.month, now.day, 23, 59, 59, 999999)
        reached_contact = Subscriber.objects\
            .filter(campaign_id__in=campaign_id_list,  # status=5,
                    updated_date__range=(start_date, end_date))\
            .count()

    template = 'frontend/dashboard.html'

    data = {
        'module': current_view(request),
        'form': form,
        'dialer_setting_msg': user_dialer_setting_msg(request.user),
        'campaign_count': campaign_count,
        'total_of_phonebook_contacts': total_of_phonebook_contacts,
        'campaign_phonebook_active_contact_count': pb_active_contact_count,
        'reached_contact': reached_contact,
        'total_record': total_record,
        'total_duration_sum': total_duration_sum,
        'total_call_count': total_call_count,
        'total_answered': total_answered,
        'total_not_answered': total_not_answered,
        'total_busy': total_busy,
        #'total_others': total_others,
        'total_cancel': total_cancel,
        'total_congestion': total_congestion,
        'total_failed': total_failed,
        'answered_color': COLOR_DISPOSITION['ANSWER'],
        'busy_color': COLOR_DISPOSITION['BUSY'],
        'not_answered_color': COLOR_DISPOSITION['NOANSWER'],
        'cancel_color': COLOR_DISPOSITION['CANCEL'],
        'congestion_color': COLOR_DISPOSITION['CONGESTION'],
        'failed_color': COLOR_DISPOSITION['FAILED'],
        'SEARCH_TYPE': SEARCH_TYPE,
        'VOIPCALL_DISPOSITION': VOIPCALL_DISPOSITION,
    }
    if on_index == 'yes':
        return data
    return render_to_response(template, data,
        context_instance=RequestContext(request))


def cust_password_reset(request):
    """Use ``django.contrib.auth.views.password_reset`` view method for
    forgotten password on the Customer UI

    This method sends an e-mail to the user's email-id which is entered in
    ``password_reset_form``
    """
    if not request.user.is_authenticated():
        data = {'loginform': LoginForm()}
        return password_reset(request,
            template_name='frontend/registration/password_reset_form.html',
            email_template_name='frontend/registration/password_reset_email.html',
            post_reset_redirect='/password_reset/done/',
            from_email='newfies_admin@localhost.com',
            extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_done(request):
    """Use ``django.contrib.auth.views.password_reset_done`` view method for
    forgotten password on the Customer UI

    This will show a message to the user who is seeking to reset their
    password.
    """
    if not request.user.is_authenticated():
        data = {'loginform': LoginForm()}
        return password_reset_done(request,
            template_name='frontend/registration/password_reset_done.html',
            extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_confirm(request, uidb36=None, token=None):
    """Use ``django.contrib.auth.views.password_reset_confirm`` view method for
    forgotten password on the Customer UI

    This will allow a user to reset their password.
    """
    if not request.user.is_authenticated():
        data = {'loginform': LoginForm()}
        return password_reset_confirm(request, uidb36=uidb36, token=token,
        template_name='frontend/registration/password_reset_confirm.html',
        post_reset_redirect='/reset/done/',
        extra_context=data)
    else:
        return HttpResponseRedirect("/")


def cust_password_reset_complete(request):
    """Use ``django.contrib.auth.views.password_reset_complete`` view method
    for forgotten password on theCustomer UI

    This shows an acknowledgement to the user after successfully resetting
    their password for the system.
    """
    if not request.user.is_authenticated():
        data = {'loginform': LoginForm()}
        return password_reset_complete(request,
        template_name='frontend/registration/password_reset_complete.html',
        extra_context=data)
    else:
        return HttpResponseRedirect("/")
