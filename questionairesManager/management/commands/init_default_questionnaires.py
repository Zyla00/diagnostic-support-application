from django.core.management.base import BaseCommand
from questionairesManager.models import Questionnaire, Section, Question, Choice

class Command(BaseCommand):
    help = "Wczytuje domyślne ankiety dostępne dla wszystkich użytkowników"

    def handle(self, *args, **kwargs):
        if Questionnaire.objects.filter(is_global=True).exists():
            self.stdout.write("Ankiety domyślne już istnieją.")
            return

        # == Ankieta 1 ==
        ankieta1 = Questionnaire.objects.create(name="Informacje dodatkowe", is_global=True)

        sekcje1 = {
            "Cechy demograficzne i antropometryczne": [
                ("Wiek", "text"),
                ("Płeć", "single_choice", ["Mężczyzna", "Kobieta", "Inna"]),
                ("Waga (kg)", "text"),
                ("Wzrost (cm)", "text"),
                ("Narodowość / rasa", "text"),
                ("Grupa krwi", "single_choice", ["A", "B", "AB", "0"]),
                ("Rh", "single_choice", ["+", "-"]),
                ("Zawód / charakter pracy", "text"),
            ],
            "Wywiad medyczny": [
                ("Czy choruje Pan/Pani przewlekle? Jeśli tak, proszę podać szczegóły.", "text"),
                ("Czy w rodzinie występowały choroby genetyczne?", "text"),
                ("Czy przeszedł/ęła Pan/Pani operacje lub był/a hospitalizowany/a?", "text"),
                ("Jakie leki przyjmuje Pan/Pani na stałe?", "text"),
                ("Czy występują u Pana/Pani alergie? Jeśli tak, proszę podać jakie.", "text"),
                ("Czy wystąpiły u Pana/Pani niepożądane reakcje na leki?", "text"),
            ],
            "Styl życia i nawyki": [
                ("Czy pali Pan/Pani papierosy? Jeśli tak, ile dziennie i od kiedy?", "text"),
                ("Jak często spożywa Pan/Pani alkohol?", "text"),
                ("Czy używa Pan/Pani substancji psychoaktywnych (narkotyków)?", "text"),
                ("Jak wygląda aktywność fizyczna w ciągu tygodnia?", "text"),
                ("Jakie są Pana/Pani nawyki żywieniowe?", "text"),
                ("Ile godzin Pan/Pani zwykle śpi i jak ocenia Pan/Pani jakość snu?", "text"),
                ("Jak ocenił(a)by Pan/Pani poziom stresu w skali 1–10?", "single_choice", [str(i) for i in range(1, 11)]),
                ("Czy są inne informacje dotyczące stylu życia, które chciał(a)by Pan/Pani przekazać?", "text"),
            ],
            "Dane kontekstowe": [
                ("Czy jest Pani w ciąży lub karmi piersią? (odpowiedź jeśli dotyczy)", "single_choice", ["Tak", "Nie"]),
                ("Ile razy była Pani w ciąży, ile porodów oraz poronień? (odpowiedź jeśli dotyczy)", "text"),
                ("Jakie szczepienia zostały przyjęte przez Pana/Panią?", "text"),
                ("Czy ma Pan/Pani częsty kontakt z osobami chorymi?", "single_choice", ["Tak", "Nie"]),
                ("Czy posiada Pan/Pani dostęp do opieki medycznej?", "single_choice", ["Tak", "Nie", "Ograniczony"]),
            ],
        }

        for section_name, questions in sekcje1.items():
            section = Section.objects.create(name=section_name, questionnaire=ankieta1)
            for q in questions:
                q_text = q[0]
                q_type = q[1]
                choices = q[2] if len(q) > 2 else []
                question = Question.objects.create(
                    question_text=q_text,
                    question_type="single_choice" if choices else q_type,
                    section=section,
                    questionnaire=ankieta1
                )
                for choice_text in choices:
                    Choice.objects.create(question=question, text=choice_text)

        # == Ankieta 2 ==
        ankieta2 = Questionnaire.objects.create(name="Pierwszy wywiad ogólny", is_global=True)

        sekcje2 = {
            "Dane demograficzne": [
                ("Imię i nazwisko", "text"),
                ("Data urodzenia", "text"),
                ("Płeć", "single_choice", ["Mężczyzna", "Kobieta", "Inna"]),
                ("Zawód / tryb życia", "text"),
                ("Miejsce zamieszkania", "text"),
            ],
            "Główna dolegliwość": [
                ("Co skłoniło Pana/Panią do wizyty?", "text"),
                ("Od kiedy występują objawy?", "text"),
                ("Czy objawy ulegają zmianie lub nasileniu?", "text"),
                ("Co łagodzi bądź nasila objawy?", "text"),
            ],
            "Choroby i hospitalizacje": [
                ("Czy choruje Pan/Pani przewlekle?", "text"),
                ("Czy był/a Pan/Pani hospitalizowany/a?", "text"),
                ("Czy przeszedł/ęła Pan/Pani poważne operacje?", "text"),
                ("Czy przebył/a Pan/Pani choroby zakaźne? Jeśli tak, jakie?", "text"),
            ],
            "Wywiad rodzinny": [
                ("Czy w rodzinie występowały choroby przewlekłe?", "text"),
                ("Czy w rodzinie występowały choroby psychiczne?", "text"),
                ("Czy ktoś w rodzinie zmarł nagle lub w młodym wieku?", "text"),
            ],
            "Leki i suplementy": [
                ("Czy przyjmuje Pan/Pani leki na stałe?", "text"),
                ("Czy stosuje Pan/Pani suplementy diety?", "text"),
                ("Czy doświadczył/a Pan/Pani działań niepożądanych po lekach?", "text"),
            ],
        }

        for section_name, questions in sekcje2.items():
            section = Section.objects.create(name=section_name, questionnaire=ankieta2)
            for q in questions:
                q_text = q[0]
                q_type = q[1]
                choices = q[2] if len(q) > 2 else []
                question = Question.objects.create(
                    question_text=q_text,
                    question_type="single_choice" if choices else q_type,
                    section=section,
                    questionnaire=ankieta2
                )
                for choice_text in choices:
                    Choice.objects.create(question=question, text=choice_text)

        self.stdout.write(self.style.SUCCESS("Dodano domyślne ankiety."))
