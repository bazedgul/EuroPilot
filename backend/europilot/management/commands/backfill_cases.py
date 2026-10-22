from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.db import transaction

from europilot.models import CaseRecord, InvestigationRecord


class Command(BaseCommand):
    help = "Create missing local reconciliation cases for existing investigations."

    def handle(self, *args, **options):
        created = 0
        existing = 0

        for investigation in InvestigationRecord.objects.order_by("investigation_id"):
            case_id = f"case-{investigation.investigation_id}"
            with transaction.atomic():
                existing_case = CaseRecord.objects.filter(investigation=investigation).first()
                if existing_case is not None:
                    was_created = False
                else:
                    conflicting_case = CaseRecord.objects.filter(case_id=case_id).first()
                    if conflicting_case is not None and conflicting_case.investigation_id != investigation.investigation_id:
                        raise CommandError(
                            f"Case ID collision for '{case_id}': it belongs to investigation "
                            f"'{conflicting_case.investigation_id}', not '{investigation.investigation_id}'."
                        )

                    try:
                        _, was_created = CaseRecord.objects.get_or_create(
                            investigation=investigation,
                            defaults={"case_id": case_id, "state": CaseRecord.State.OPEN},
                        )
                    except IntegrityError:
                        # The preliminary check handles observable collisions. An
                        # IntegrityError during creation is not portable evidence
                        # of which database constraint failed, so preserve it.
                        raise

            if was_created:
                created += 1
            else:
                existing += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} case(s); {existing} case(s) already existed."))
