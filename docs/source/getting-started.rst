
.. _getting_started:

Getting Started
===============

:Web: http://www.newfies-dialer.org/
:Download: http://www.newfies-dialer.org/download/
:Source: https://github.com/Star2Billing/newfies-dialer/
:Keywords: dialer, voip, freeswitch, django, asynchronous, rabbitmq, redis, python, distributed


--

Newfies is an open source VoIP Dialer based on distributed message passing.
It has been built to support cloud based servers and can also work on standalone servers.
It uses `Freeswitch`_ (VoIP Server) to outbound calls, but support for other
VoIP Servers such as `Asterisk`_ could be easily added in the future.
The platform is focused on real-time operations and task call distributions
to clustered brokers and workers.

Newfies-Dialer is written in Python, using the `Django`_ Framework. It also operates
with message brokers such as `RabbitMQ`_, `Redis`_ but support for Beanstalk,
MongoDB, CouchDB and DBMS is also available.

Newfies-Dialer provides an extensive set of APIs to easily integrate with
third-party applications.

Using very simple steps, Newfies-Dialer will help you create campaigns, add
phonebooks, contacts, build audio messages and create complex telephony
applications. Once your campaigns are ready to start, your messages
will be dispatched and delivered.

.. _`Freeswitch`: http://www.freeswitch.org/
.. _`Asterisk`: http://www.asterisk.org/
.. _`Django`: http://djangoproject.com/
.. _`RabbitMQ`: http://www.rabbitmq.com/
.. _`Redis`: http://code.google.com/p/redis/


.. contents::
    :local:
    :depth: 1


.. _overview:

Overview
--------

Newfies-Dialer can be installed and used by anyone who has a need for mass
outbound calling, voice broadcasting or providing outbound IVR. Some of the
potential uses for Newfies-Dialer are listed below.

The system may be installed and used by either companies who wish to make calls
on their own behalf, or by SaaS (Software as a Service) companies that want to
provide bulk dialling facilities to their own customers.


.. _utility:

Utility
--------
Newfies-Dialer is loaded up with a list of telephone numbers that can be dialled
sequentially at very high rates of calling depending on carrier capacity and
hardware, potentially delivering many millions of calls per day.

When the called party answers the call, Newfies-Dialer passes the call to a telephony
application that is custom designed to provide the desired behaviour.

Below are examples of some of the uses for Newfies-Dialer


    * ``Telecasting``: Broadcast marketing or informational messages to customers and clients.

    * ``Phone Polling, Surveys and Voting``: Ring large numbers of people and present
      IVR options for either polling their opinions, interactive surveys, or taking
      their vote and record the results.

    * ``Debt Control``: Customers can be automatically reminded at intervals that
      they owe money, and an IVR menu presented to talk to the finance department
      or passed to a credit card capture IVR to pay over the phone.

    * ``Appointment reminders``: Doctors, Dentists, and other organisations that make
      appointments for their clients can integrate Newfies-Dialer into their
      appointment systems to pass a message reminding them of an upcoming appointment.

    * ``Dissemination of information via phone``: Newfies-Dialer was originally
      designed to call large numbers of people and disseminate medical and health advice
      via the ubiquitous cellphone in 3rd world countries where often, literacy
      levels are low. On a local scale, it can be used to disseminate information
      about forthcoming community events.

    * ``Mass Emergency broadcast``: Where there is a necessity to warn large numbers
      of people in a short space of time, such as weather warnings.

    * ``Subscription Reminders and Renewals``: Where a company sells an annual
      subscription for a product or service, Newfies-Dialer can be configured to
      dial the customer, remind them that the subscription is due. a


.. _features:

Features
--------

    +-----------------+----------------------------------------------------+
    | Telephony PBX   | Based on leading open source Freeswitch, Asterisk  |
    +-----------------+----------------------------------------------------+
    | Distributed     | Runs on one or more machines. Supports             |
    |                 | broker `clustering` and `HA` when used in          |
    |                 | combination with `RabbitMQ`.  You can set up new   |
    |                 | workers without central configuration (e.g. use    |
    |                 | your grandma's laptop to help if the queue is      |
    |                 | temporarily congested).                            |
    +-----------------+----------------------------------------------------+
    | Concurrency     | Throttle Concurrent Calls                          |
    +-----------------+----------------------------------------------------+
    | Scheduling      | Supports recurring tasks like cron, or specifying  |
    |                 | an exact date or countdown for when the task       |
    |                 | should be executed. Can re-try to the non connected|
    |                 | numbers at a later time                            |
    +-----------------+----------------------------------------------------+
    | IVR support     | Accommodates multiple IVR scripts with options to  |
    |                 | connect the user to some other IVR/phone number on |
    |                 | pressing a key                                     |
    +-----------------+----------------------------------------------------+
    | Web Interface   | Newfies can be managed via a Web interface.        |
    |                 | Realtime web-based reports for call details and    |
    |                 | current calls.                                     |
    |                 | You can query status and results via URLs, enabling|
    |                 | the ability  to poll task status using Ajax.       |
    +-----------------+----------------------------------------------------+
    | Error Emails    | Can be configured to send emails to the            |
    |                 | administrator if a tasks fails.                    |
    +-----------------+----------------------------------------------------+
    | Import Contact  | Import contact details from a .csv file            |
    +-----------------+----------------------------------------------------+


.. _extra_features:

Extra Features
--------------

    +-----------------+----------------------------------------------------+
    | AMD             | Answer Machine Detection module is available.      |
    |                 | For this module see the section addons on website  |
    +-----------------+----------------------------------------------------+
    | SMS             | SMS delivery, SMS Gateway support, SMS campaign.   |
    |                 | For this module see the section addons on website  |
    +-----------------+----------------------------------------------------+



.. _architecture:

Architecture
------------

.. image:: ./_static/images/newfies-dialer_architecture.png

* User selects contacts, phonebooks and campaigns, then chooses a voice application to use. The campaign is then launched

* ``Newfies-Dialer`` spools the outbound calls to ``FreeSWITCH`` via ``ESL``.

* ``FreeSWITCH`` dials the contact via the configured telephony gateways.

* Contact picks up the call, and the answer event is received in ``FreeSWITCH`` and passed back to our Lua IVR Application.

* ``Newfies-Dialer`` is notified that the call is answered, then renders the appropriate IVR.

* The application is delivered to the contact by ``FreeSWITCH``.
