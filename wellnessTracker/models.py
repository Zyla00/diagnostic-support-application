from django.db import models
from django.conf import settings
from multiselectfield import MultiSelectField
from decimal import Decimal
from django.utils.translation import gettext_lazy as _


class MoodScale(models.Model):
    SCALE_CHOICES = [(i, str(i)) for i in range(0, 11)]

    scale = models.IntegerField(
        _("Skala nastroju"),
        choices=SCALE_CHOICES,
        default=0,
        blank=True,
        null=True,
        help_text=_("Jak dziś się czułeś/aś w skali od 0 do 10?")
    )
    updated_at = models.DateTimeField(
        _("Zaktualizowano"),
        auto_now=True,
        help_text=_("Czas ostatniej aktualizacji skali")
    )

    class Meta:
        verbose_name = _("Skala nastroju")
        verbose_name_plural = _("Skale nastroju")


class MoodEmotion(models.Model):
    EMOTION_CHOICES = (
        ('happy', _("Szczęśliwy/a")), ('sad', _("Smutny/a")), ('angry', _("Zły/a")),
        ('excited', _("Podekscytowany/a")), ('nervous', _("Nerwowy/a")),
        ('scared', _("Wystraszony/a")), ('relaxed', _("Zrelaksowany/a")),
        ('bored', _("Znudzony/a")), ('content', _("Zadowolony/a")), ('curious', _("Ciekawy/a")),
        ('anxious', _("Zaniepokojony/a")), ('confused', _("Zdezorientowany/a")),
        ('surprised', _("Zaskoczony/a")), ('grateful', _("Wdzięczny/a")),
        ('frustrated', _("Sfrustrowany/a")), ('jealous', _("Zazdrosny/a")),
        ('lonely', _("Samotny/a")), ('proud', _("Dumny/a")), ('ashamed', _("Zawstydzony/a")),
        ('guilty', _("Winny/a")), ('embarrassed', _("Zażenowany/a")),
        ('disappointed', _("Rozczarowany/a")), ('inspired', _("Zainspirowany/a")),
        ('amused', _("Rozbawiony/a")), ('sympathetic', _("Współczujący/a")),
        ('thoughtful', _("Zamyślony/a")), ('energetic', _("Pełen/na energii")),
        ('overwhelmed', _("Przytłoczony/a")), ('hopeful', _("Pełen/na nadziei"))
    )

    emotions = MultiSelectField(
        _("Emocje"),
        choices=EMOTION_CHOICES,
        max_length=99999,
        blank=True,
        help_text=_("Jakie emocje dziś odczuwałeś/aś?")
    )
    updated_at = models.DateTimeField(
        _("Zaktualizowano"),
        auto_now=True,
        help_text=_("Czas ostatniej aktualizacji emocji")
    )

    class Meta:
        verbose_name = _("Emocje")
        verbose_name_plural = _("Emocje")


class MoodNote(models.Model):
    note = models.TextField(
        _("Notatka"),
        blank=True,
        help_text=_("Własna notatka związana z nastrojem")
    )
    updated_at = models.DateTimeField(
        _("Zaktualizowano"),
        auto_now=True,
        help_text=_("Czas ostatniej aktualizacji notatki")
    )

    class Meta:
        verbose_name = _("Notatka nastroju")
        verbose_name_plural = _("Notatki nastroju")


class Sleep(models.Model):
    SCALE_CHOICES_HALF = [(Decimal(i) / 2, f'{Decimal(i) / 2:.1f}') for i in range(0, 49)]

    slept_scale = models.FloatField(
        _("Czas snu (w godzinach)"),
        choices=SCALE_CHOICES_HALF,
        default=0,
        blank=True,
        null=True,
        help_text=_("Jak długo spałeś/aś dziś (w godzinach)?")
    )
    updated_at = models.DateTimeField(
        _("Zaktualizowano"),
        auto_now=True,
        help_text=_("Czas ostatniej aktualizacji")
    )

    class Meta:
        verbose_name = _("Sen")
        verbose_name_plural = _("Sen")


class CoffeHabit(models.Model):
    CHOICES = [(i, str(i)) for i in range(0, 1001, 1)]
    UNIT_CHOICES = [
        ('ml', 'ml'),
        ('l', 'l')
    ]

    coffee_amount = models.PositiveIntegerField(
        _("Ile kawy wypiłeś/aś?"),
        blank=True,
        null=True
    )
    coffee_unit = models.CharField(
        _("Jednostka kawy"),
        max_length=2,
        choices=UNIT_CHOICES,
        default='ml',
        blank=True,
        null=True
    )
    updated_at = models.DateTimeField(
        _("Zaktualizowano"),
        auto_now=True,
        help_text=_("Czas ostatniej aktualizacji")
    )

    class Meta:
        verbose_name = _("Nawyki kawowe")
        verbose_name_plural = _("Nawyki kawowe")


class CigaretteHabit(models.Model):
    CHOICES = [
        ('choose-type', _("Wybierz typ")),
        ('full-flavor', _("Mocne")),
        ('light', _("Light")),
        ('ultra-light', _("Ultra light")),
        ('menthol', _("Mentolowe")),
        ('flavored', _("Aromatyzowane")),
        ('heated-tobacco', _("Podgrzewany tytoń (HTP)")),
        ('e-cigarette', _("E-papieros")),
        ('roll-your-own', _("Skręcane")),
        ('nicotine-free', _("Beznikotynowe")),
        ('premium', _("Premium")),
        ('organic', _("Organiczne")),
        ('other', _("Inne")),
    ]

    cigarettes = models.PositiveIntegerField(
        _("Ile papierosów wypaliłeś/aś?"),
        blank=True,
        null=True
    )
    cigarette_type = models.CharField(
        _("Typ papierosa"),
        max_length=20,
        choices=CHOICES,
        blank=True
    )
    updated_at = models.DateTimeField(
        _("Zaktualizowano"),
        auto_now=True,
        help_text=_("Czas ostatniej aktualizacji")
    )

    class Meta:
        verbose_name = _("Nawyki tytoniowe")
        verbose_name_plural = _("Nawyki tytoniowe")


class Sports(models.Model):
    UNIT = [
        ('minutes', _("minuty")),
        ('hours', _("godziny")),
    ]

    CHOICES = [
        ('gym', _("Siłownia")),
        ('running', _("Bieganie")),
        ('cycling', _("Jazda na rowerze")),
        ('swimming', _("Pływanie")),
        ('basketball', _("Koszykówka")),
        ('soccer', _("Piłka nożna")),
        ('tennis', _("Tenis")),
        ('yoga', _("Joga")),
        ('pilates', _("Pilates")),
        ('hiking', _("Turystyka piesza")),
        ('climbing', _("Wspinaczka")),
        ('dancing', _("Taniec")),
        ('boxing', _("Boks")),
        ('martial-arts', _("Sztuki walki")),
        ('weightlifting', _("Podnoszenie ciężarów")),
        ('crossfit', _("CrossFit")),
        ('aerobics', _("Aerobik")),
        ('rowing', _("Wioślarstwo")),
        ('skiing', _("Narciarstwo")),
        ('snowboarding', _("Snowboard")),
        ('skating', _("Łyżwiarstwo")),
        ('surfing', _("Surfing")),
        ('kayaking', _("Kajakarstwo")),
        ('golf', _("Golf")),
        ('cricket', _("Krykiet")),
        ('rugby', _("Rugby")),
        ('baseball', _("Baseball")),
        ('volleyball', _("Siatkówka")),
        ('badminton', _("Badminton")),
        ('table-tennis', _("Tenis stołowy")),
        ('archery', _("Łucznictwo")),
        ('fencing', _("Szermierka")),
        ('horse-riding', _("Jazda konna")),
        ('gymnastics', _("Gimnastyka")),
        ('triathlon', _("Triathlon")),
        ('bouldering', _("Bouldering")),
    ]

    exercise_times = models.PositiveIntegerField(
        _("Jak długo ćwiczyłeś/aś?"),
        blank=True,
        null=True
    )
    exercise_unit = models.CharField(
        _("Jednostka czasu"),
        max_length=8,
        choices=UNIT,
        default='minutes',
        blank=True,
        null=True
    )
    exercise_type = MultiSelectField(
        _("Rodzaj aktywności"),
        max_length=99999,
        choices=CHOICES,
        blank=True
    )
    updated_at = models.DateTimeField(
        _("Zaktualizowano"),
        auto_now=True,
        help_text=_("Czas ostatniej aktualizacji")
    )

    class Meta:
        verbose_name = _("Aktywność fizyczna")
        verbose_name_plural = _("Aktywność fizyczna")


class AlcoholHabit(models.Model):
    UNIT = [
        ('ml', 'ml'),
        ('l', 'l'),
    ]

    CHOICES = [
        ('beer', _("Piwo")),
        ('wine', _("Wino")),
        ('vodka', _("Wódka")),
        ('whiskey', _("Whisky")),
        ('rum', _("Rum")),
        ('tequila', _("Tequila")),
        ('gin', _("Gin")),
        ('brandy', _("Brandy")),
        ('champagne', _("Szampan")),
        ('cider', _("Cydr")),
        ('absinthe', _("Absynt")),
        ('liqueur', _("Likier")),
        ('sake', _("Sake")),
        ('vermouth', _("Wermut")),
        ('mead', _("Miód pitny")),
        ('sherry', _("Sherry")),
        ('port', _("Porto")),
        ('cocktail', _("Koktajl")),
        ('schnapps', _("Sznaps")),
        ('perry', _("Perry")),
        ('moonshine', _("Bimber")),
        ('armagnac', _("Armaniak")),
        ('calvados', _("Calvados")),
        ('grappa', _("Grappa")),
        ('aquavit', _("Akvavit")),
        ('baijiu', _("Baijiu")),
        ('ouzo', _("Ouzo")),
        ('rakia', _("Rakija")),
        ('tequila-sunrise', _("Tequila Sunrise")),
        ('martini', _("Martini")),
        ('manhattan', _("Manhattan")),
        ('margarita', _("Margarita")),
        ('mojito', _("Mojito")),
        ('bloody-mary', _("Bloody Mary")),
        ('pina-colada', _("Piña Colada")),
        ('cosmopolitan', _("Cosmopolitan")),
        ('old-fashioned', _("Old Fashioned")),
    ]

    alcohol_amount = models.PositiveIntegerField(
        _("Czy piłeś/aś alkohol? (ilość)"),
        blank=True,
        null=True
    )
    alcohol_unit = models.CharField(
        _("Jednostka alkoholu"),
        max_length=2,
        choices=UNIT,
        default='ml',
        blank=True,
        null=True
    )
    alcohol_type = MultiSelectField(
        _("Rodzaj alkoholu"),
        max_length=99999,
        choices=CHOICES,
        blank=True
    )
    updated_at = models.DateTimeField(
        _("Zaktualizowano"),
        auto_now=True,
        help_text=_("Czas ostatniej aktualizacji")
    )

    class Meta:
        verbose_name = _("Spożycie alkoholu")
        verbose_name_plural = _("Spożycie alkoholu")


class Day(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Użytkownik"))
    mood_scale = models.OneToOneField(
        MoodScale, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Skala nastroju")
    )
    mood_emotion = models.OneToOneField(
        MoodEmotion, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Emocje")
    )
    mood_note = models.OneToOneField(
        MoodNote, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Notatka nastroju")
    )
    sleep = models.ForeignKey(
        'Sleep', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Sen")
    )
    coffee_habit = models.ForeignKey(
        'CoffeHabit', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Kawa")
    )
    cigarette_habit = models.ForeignKey(
        'CigaretteHabit', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Palenie")
    )
    alcohol_habit = models.ForeignKey(
        AlcoholHabit, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Alkohol")
    )
    sports = models.ForeignKey(
        'Sports', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Aktywność fizyczna")
    )
    date = models.DateField(_("Data"))
    updated_at = models.DateTimeField(_("Zaktualizowano"), auto_now=True)

    class Meta:
        verbose_name = _("Dzień")
        verbose_name_plural = _("Dni")

    def delete(self, *args, **kwargs):
        if self.mood_scale:
            self.mood_scale.delete()
        if self.mood_emotion:
            self.mood_emotion.delete()
        if self.mood_note:
            self.mood_note.delete()
        if self.sleep:
            self.sleep.delete()
        if self.coffee_habit:
            self.coffee_habit.delete()
        if self.cigarette_habit:
            self.cigarette_habit.delete()
        if self.alcohol_habit:
            self.alcohol_habit.delete()
        if self.sports:
            self.sports.delete()
        super().delete(*args, **kwargs)
