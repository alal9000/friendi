from events.models import Event
from django.utils.dateparse import parse_date

# Define the cutoff date
cutoff_date = parse_date("2024-08-10")

# Filter events based on the event_date and delete them
events_to_delete = Event.objects.filter(event_date__lte=cutoff_date)

if events_to_delete.exists():
    count = events_to_delete.count()
    events_to_delete.delete()
    print(f"{count} events with event_date on or before {cutoff_date} and their related records have been deleted.")
else:
    print(f"No events found with event_date on or before {cutoff_date}.")
