from datetime import timedelta, date, datetime
from django.utils import timezone
import logging
import calendar
from versatileimagefield.image_warmer import VersatileImageFieldWarmer
from simple_history.models import HistoricalRecords

logger = logging.getLogger(__name__)

def create_thumbnails(pk, model, size_set, image_attr=None):
    instance = model.objects.get(pk=pk)
    if not image_attr:
        image_attr = 'image'

    image_instance = getattr(instance, image_attr)
    if image_instance.name == '':
        # There is no file, skip processing
        return
    warmer = VersatileImageFieldWarmer(
        instance_or_queryset=instance,
        rendition_key_set=size_set, image_attr=image_attr)
    logger.info('Creating thumbnails for  %s', pk)
    num_created, failed_to_create = warmer.warm()
    if num_created:

        logger.info('Created %d thumbnails', num_created)
    if failed_to_create:

        logger.error('Failed to generate thumbnails',
                     extra={'paths': failed_to_create})


def add_history_ip_address(sender, **kwargs):
    history_instance = kwargs['history_instance']
    # thread.request for use only when the simple_history middleware is on and enabled
    history_instance.ip_address = HistoricalRecords.thread.request.META['REMOTE_ADDR']

def get_week_day(date=date.today()):
    return calendar.day_name[date.weekday()].upper()

def get_next_days_array(count=7, date=datetime.now()):
    dates = []
    for single_date in (date + timedelta(n) for n in range(count)):
        dates.append(single_date)
    return dates

def split_time(time_from, time_end, start_limit=None):
    curr = datetime(
        2020, 1, 1,
        hour=time_from.hour,
        minute=time_from.minute,
        second=time_from.second
    )
    end = datetime(
        2020, 1, 1,
        hour=time_end.hour,
        minute=time_end.minute,
        second=time_end.second
    )
    seq = []
    while True:
        prevCurr = curr
        curr = curr + timedelta(minutes=60)
        if curr.time() < end.time():
            if start_limit:
                now_60 = datetime.now() + timedelta(minutes=60)
                now_time = now_60.time()
                if curr.time() > now_time:
                    seq.append({"from":prevCurr.strftime("%H:%M"), "to": curr.strftime("%H:%M")})
            else:
                seq.append({"from": prevCurr.strftime("%H:%M"), "to": curr.strftime("%H:%M")})
        else:
            break
    return seq

def get_current_date_time(time_zone=None):
    if time_zone:
        return timezone.now()
    return timezone.localtime(timezone.now())

def get_current_date(time_zone=None):
    if time_zone:
        return timezone.now()
    return timezone.localtime(timezone.now())

def get_current_time(time_zone=None):
    if time_zone:
        return timezone.now()
    return timezone.localtime(timezone.now())
