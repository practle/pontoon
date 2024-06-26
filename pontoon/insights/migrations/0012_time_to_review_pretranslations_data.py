# Generated by Django 3.2.4 on 2021-11-30 19:56

from datetime import timedelta

from django.db import migrations
from django.db.models import F


def populate_time_to_review_pretranslations(apps, schema_editor):
    ActionLog = apps.get_model("actionlog", "ActionLog")

    actions = (
        ActionLog.objects.filter(
            translation__entity__resource__project__system_project=False,
            translation__entity__resource__project__visibility="public",
            translation__user__email__in=[
                "pontoon-tm@example.com",
                "pontoon-gt@example.com",
            ],
            action_type__in=["translation:approved", "translation:rejected"],
        )
        .exclude(performed_by=F("translation__user"))
        .exclude(performed_by__email="pontoon-sync@example.com")
        .values(
            "created_at",
            "action_type",
            "translation__locale",
            date=F("translation__date"),
            approved_date=F("translation__approved_date"),
            rejected_date=F("translation__rejected_date"),
        )
    )

    action_data = dict()

    # Store action data in a dict for faster matching with snapshots
    for action in actions:
        key = (action["translation__locale"], action["created_at"].date())
        data = action_data.setdefault(key, list())

        if action["action_type"] == "translation:approved" and action["approved_date"]:
            data.append(action["approved_date"] - action["date"])

        elif (
            action["action_type"] == "translation:rejected" and action["rejected_date"]
        ):
            data.append(action["rejected_date"] - action["date"])

    LocaleInsightsSnapshot = apps.get_model("insights", "LocaleInsightsSnapshot")
    snapshots = LocaleInsightsSnapshot.objects.all()
    snapshot_data = dict()

    # Store snapshots in a map with the same key format we use for action data
    for snapshot in snapshots:
        key = (snapshot.locale_id, snapshot.created_at)
        snapshot_data[key] = snapshot

    # Update snapshots
    for key, times_to_review in action_data.items():
        if key in snapshot_data and len(times_to_review) > 0:
            times_to_review = [i for i in times_to_review if i is not None]
            snapshot_data[key].time_to_review_pretranslations = sum(
                times_to_review, timedelta()
            ) / len(times_to_review)

    LocaleInsightsSnapshot.objects.bulk_update(
        snapshots, ["time_to_review_pretranslations"], batch_size=1000
    )


def reset_time_to_review_pretranslations(apps, schema_editor):
    LocaleInsightsSnapshot = apps.get_model("insights", "LocaleInsightsSnapshot")
    LocaleInsightsSnapshot.objects.update(time_to_review_pretranslations=None)


class Migration(migrations.Migration):
    dependencies = [
        ("insights", "0011_time_to_review_pretranslations"),
    ]

    operations = [
        migrations.RunPython(
            code=populate_time_to_review_pretranslations,
            reverse_code=reset_time_to_review_pretranslations,
        ),
    ]
