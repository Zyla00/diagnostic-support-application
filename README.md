# diagnostic-support-application

## Ewaluacja wyników

###  Klasyfikacja 
W zadaniu klasyfikacji objawów do odpowiednich specjalistów medycznych wykorzystano 
model Mistral w trybie zero-shot, czyli bez wcześniejszego treningu, oraz jego rozszerzoną 
wersję z mechanizmem RAG, wspartą zewnętrzną bazą wiedzy. Do eksperymentu 
wykorzystano zbiór 260 przypadków (10 przypadków dla każdej klasy). Klasy odpowiadały 
różnym specjalizacjom lekarskim. Celem było wskazanie właściwego specjalisty na podstawie 
zestawu objawów. 
Model Mistral bez zewnętrznej wiedzy poradził sobie dobrze, uzyskując ogólną skuteczność na 
poziomie 71%. Jednak często miał trudność z podjęciem jednoznacznej decyzji. Skłaniał się do 
przypisywania kilku specjalistów naraz, czasem także tych nieadekwatnych. Obserwowano 
również tendencję do nadmiernej ostrożności np. objawy typowe dla infekcji (np. ból głowy 
i kaszel) były kierowane też do onkologa, ze względu na wzmiankę o powiększonych węzłach chłonnych. Tego rodzaju błędy wynikały z braku zdolności eliminacji mniej prawdopodobnych 
hipotez. Model często przypisywał jakiegoś lekarza nawet tam, gdzie brakowało pełnych 
danych. Również w przypadkach przewlekłych problemów żołądkowych, takich jak biegunka 
i zmęczenie, zalecał gastroenterologa, ale czasami także internistę lub dietetyka – w zależności 
od użytego promptu. 
Wersja Mistrala z mechanizmem RAG osiągnęła wyższą trafność. Poprawnie zaklasyfikowała 
78% przypadków. Dzięki dodatkowej bazie wiedzy lepiej radziła sobie z dopasowaniem mniej 
oczywistych objawów do specjalizacji. Nadal jednak pojawiała się tendencja do nadmiarowego 
przypisywania kilku specjalistów (np. pulmonolog + alergolog + immunolog przy klasycznych 
objawach astmy). Model nie zawsze potrafił ograniczyć odpowiedź do najbardziej 
prawdopodobnej kategorii. Oba modele wykazały dobrą zdolność rozumienia tekstu, 
logicznego łączenia objawów oraz sugerowania racjonalnych podejść diagnostycznych. 
Problemem pozostał brak eliminacji zbędnych kierunków diagnostycznych, co skutkowało 
przeszacowaniem liczby sugerowanych specjalistów. Należy podkreślić, że do analizy 
wykorzystano przypadki z pełnym opisem obejmującym objawy i wyniki badań 
laboratoryjnych, które nie należały do szczególnie skomplikowanych pod względem 
klinicznym.

### Generowanie opisów chorób 
W niniejszej pracy dane opisujące objawy chorób wygenerowano przy wykorzystaniu 
modelu językowego Mistral, wspieranego samodzielnie stworzoną, zewnętrzną bazą wiedzy 
medycznej. Po wygenerowaniu treści każdy opis został dodatkowo sprawdzony ponownie przy 
użyciu modelu Mistral zarówno w wariancie z wykorzystaniem bazy wiedzy, jak i bez niej. 
Weryfikacja była oparta na pytaniu o potencjalne nieprawidłowości lub anomalie. Całość 
procedury można określić jako zastosowanie koncepcji „LLM judge”, tj. wykorzystania 
modelu językowego jako narzędzia oceniającego jakość i spójność treści. W wyniku tego etapu: 
• 17% przypadków (52 z 301) zostało zakwalifikowanych jako wymagające ponownej 
analizy (zawierały mniejsze lub większe przekłamania). W takich sytuacjach proszono 
model o poprawienie treści zgodnie z zaproponowanymi sugestiami, 
• 10% przypadków (30 z 301) model uznał za poprawne, jednak stanowiące ogólne ujęcie 
objawów. Uznano, że na potrzeby niniejszej pracy nie ma konieczności ich modyfikacji. 
Przykładowo, w przypadku migreny model ograniczył się do ujęcia głównych objawów 
(silny ból głowy, nudności, światłowstręt), pomijając mniej oczywiste, ale istotne 
aspekty takie jak allodynia (nadwrażliwość skóry na dotyk) czy objawy prodromalne 
w postaci senności i zwiększonego apetytu na określone produkty. Uznano jednak, że 
dla potrzeb niniejszej pracy takie uproszczenie jest wystarczające. Następnie cały proces walidacji powtórzono. W tym etapie model nie wskazał już poważnych 
nieprawidłowości. Natomiast 12% przypadków (36 z 301) zostało oznaczonych jako 
wymagające zachowania ostrożności (np. drobne braki informacyjne lub potencjalne 
uproszczenia). 
Dla zapewnienia wiarygodności, przeprowadzono dodatkową ręczną weryfikację 10% 
wszystkich przypadków (31 z 301) poprzez porównanie opisów z literaturą medyczną. W tym 
etapie nie znaleziono rażących przekłamań. Natomiast około 9% z przejrzanych rekordów 
(3 z 31) uznano za duże uproszczenia i możliwości na poszerzenia listy często występujących 
objawów. Należy podkreślić, że już na etapie planowania zakładano, iż dane generowane na 
potrzeby niniejszej pracy nie muszą być wyczerpujące ani w pełni szczegółowe, lecz powinny 
odzwierciedlać typowe, główne objawy. Dlatego przyjęto opisaną metodę generowania 
i  walidacji treści.

### Generowanie etykiet dla danych 
W osobnym etapie opracowywania danych, dla drugiego zbioru, przeprowadzono proces 
przypisywania kategorii specjalistycznych do wcześniej zdefiniowanych nazw jednostek 
chorobowych. W tym przypadku dane wejściowe zawierały już nazwy chorób, natomiast 
brakowało informacji dotyczącej specjalisty lub specjalizacji medycznej, której dana jednostka 
najczęściej podlega. Do przypisania etykiety specjalistycznej zastosowano dokładnie tę samą 
procedurę, jak w przypadku opisu objawów: 
• wykorzystano model językowy Mistral, 
• wspierany własną bazą wiedzy medycznej, 
• a następnie przeprowadzono automatyczną walidację wyników z użyciem podejścia 
„LLM-as-a-judge”, czyli metody, w której duży model językowy ocenia jakość 
i poprawność wcześniej wygenerowanych danych. 
Zgodnie z założeniem, do każdej choroby przypisywano jedną, najczęściej powiązaną 
specjalizację medyczną. Takie podejście stanowiło pewne uproszczenie, ponieważ w praktyce 
diagnostycznej wiele chorób może wymagać konsultacji z kilkoma specjalistami (np. 
neurologiem i psychiatrą, albo internistą i endokrynologiem). W wyniku analizy: 
• model nie zidentyfikował żadnych rażących błędów w przypisaniu jednostek do 1081 
chorób, 
• natomiast około 30% przypadków (324 z 1081) zostało oznaczonych jako wymagające 
potencjalnego przypisania co najmniej dwóch specjalizacji, z czego druga kategoria 
miała charakter opcjonalny lub zależny od indywidualnego przebiegu choroby. 
Również w tym przypadku przeprowadzono ręczną weryfikację 10% danych (109 z 1081 
przypadków). Nie stwierdzono sytuacji, w których przypisana główna specjalizacja byłaby 
nieprawidłowa lub nieodpowiednia dla danej jednostki chorobowej. Należy podkreślić, że na potrzeby niniejszej pracy przyjęto założenie, iż przypisanie jednej, 
najczęstszej kategorii specjalistycznej jest wystarczające, zwłaszcza że celem opracowania nie 
było odwzorowanie pełnej ścieżki diagnostycznej, lecz zbudowanie struktury klasyfikacyjnej. 
W trakcie oceny wyników skupiano się przede wszystkim na identyfikacji 
potencjalnych nieścisłości i błędów merytorycznych. Ostateczny zbiór stanowi efekt 
kompromisu pomiędzy dokładnością a spójnością i użytecznością danych, z uwzględnieniem 
realiów zastosowania w kontekście niniejszego opracowania.

### Ocena modelu HerBERT po treningu 
Model HerBERT został poddany retreningowi w celu dostosowania go do zadania 
klasyfikacji przypadków medycznych do odpowiednich specjalizacji lekarskich. Wyniki 
ewaluacji przeprowadzonej na zbiorach walidacyjnym i testowym wskazują na bardzo wysoką 
skuteczność modelu. Wartości dokładności dla obu zbiorów wyniosły odpowiednio 97,38% dla 
walidacyjnego oraz 97,29% dla testowego, co oznacza, że model z powodzeniem klasyfikował 
dane. 
Równie wysoka jakość klasyfikacji znajduje potwierdzenie w innych metrykach F1 – zarówno 
F1-macro (0,9745 walidacja, 0,9744 test), jak i F1-weighted (0,9769 walidacja, 0,9758 test) 
utrzymują się na bardzo stabilnym i wyrównanym poziomie. Brak większych różnic pomiędzy 
zbiorami sugeruje, że model nie uległ przeuczeniu (overfitting) i wykazuje bardzo dobrą 
zdolność generalizacji. Model potrafi skutecznie radzić sobie również z nowymi danymi, które 
nie były widziane wcześniej. Dodatkowo, analiza wykresów ilustrujących przebieg treningu 
potwierdza te obserwacje. Wykres dokładności (rysunek 8.1) po początkowym wzroście 
wartości do poziomu około 97%, krzywe dokładności dla zbioru walidacyjnego i testowego 
pozostają stabilne i niemal zbieżne aż do końca treningu. Taka zgodność wskazuje, że proces 
uczenia przebiegł optymalnie. Mmodel osiągnął wysoką trafność przy zachowaniu dobrej 
równowagi między dopasowaniem do danych uczących a uogólnianiem na dane nowe.

<p>
<img width="326" height="179" alt="image" src="https://github.com/user-attachments/assets/4ec80e32-2568-453d-8096-e897a0c71761" />
</p>

<p>
  <img width="319" height="176" alt="image" src="https://github.com/user-attachments/assets/a93a5323-3e1f-4ce3-a2f3-251e78d4e2d0" />
</p>
Uzupełnieniem tej analizy jest macierz pomyłek (rysunek 8.3), która przedstawia szczegółowe 
wyniki klasyfikacji dla poszczególnych kategorii specjalistycznych. Dominujące wartości na 
przekątnej macierzy świadczą o tym, że model poprawnie przypisuje większość przypadków do właściwych klas. Przykładowo, kategorie takie jak Neurologia (1176 poprawnych 
przypadków), Pulmonologia (936), czy Ortopedia (1377) zostały zaklasyfikowane niemal 
bezbłędnie. Zdarzają się jednak drobne pomyłki, głównie między klasami o pokrywających się 
objawach np. Psychiatria bywała mylona z Neurologią, a Onkologia z Hematologią lub 
Gastroenterologią. Tego typu błędy mogą być wynikiem realnego klinicznego podobieństwa 
przypadków. 
<p>
<img width="328" height="288" alt="image" src="https://github.com/user-attachments/assets/613013d6-dc10-413f-bf8d-63bbd22b6c3c" />
</p>
Podsumowując, HerBERT po retreningu prezentuje wysoki poziom dokładności, stabilność 
działania i bardzo dobrą zdolność generalizacji, bez oznak przeuczenia. W połączeniu z niską 
wartością funkcji straty oraz nielicznymi pomyłkami, model ten można uznać za skuteczne 
narzędzie wspomagające automatyczną klasyfikację specjalistyczną przypadków medycznych.

### Ocena modelu XGBoost 
Model XGBoost został wykorzystany jako klasyfikator przypisujący przypadki 
medyczne do odpowiednich kategorii specjalistycznych. Ewaluacja jego skuteczności została 
przeprowadzona na dużym zbiorze testowym zawierającym 29 571 przykładów obejmujących 
26 klas (specjalizacji). Analiza objęła metryki takie jak dokładność (accuracy), precyzja 
(precision), czułość (recall) oraz F1-score, zarówno na poziomie ogólnym, jak i dla każdej klasy 
osobno. 
Model XGBoost osiągnął dokładność ogólną na poziomie 87,4%, co świadczy o solidnej 
skuteczności w zadaniu klasyfikacji przypadków medycznych do 26 specjalizacji. Wartości 
średnich metryk : F1-score (0,8454), precyzja (0,8937) i recall (0,8127) potwierdzają, że model 
dobrze rozpoznaje zarówno liczniejsze, jak i mniej reprezentowane klasy, choć cechuje się 
lekką tendencją do zachowawczości (wyższa precyzja niż czułość). 
Najwyższe wyniki uzyskano w kategoriach o wyraźnym profilu klinicznym, takich jak 
nefrologia (F1 = 0,96), pulmonologia (0,96), hepatologia (0,97) czy hematologia (0,95). W tych 
przypadkach objawy były na tyle charakterystyczne, że model niemal bezbłędnie przypisywał 
je do właściwej specjalizacji. Z kolei niższe wyniki zaobserwowano w trudniejszych klasach: 
pediatria (F1 = 0,62), medycyna zawodowa (0,68), ginekologia (0,71) czy ratunkowa (0,73). 
Obniżona skuteczność w tych obszarach wynika prawdopodobnie z niewielkiej liczby 
przykładów treningowych oraz z nakładania się objawów z innymi specjalizacjami. 
Analiza macierzy pomyłek wskazuje na dominującą poprawność klasyfikacji (większość 
przypadków na przekątnej), jednak widoczne są także pojedyncze błędy między pokrewnymi 
dziedzinami, np. neurologią a psychiatrią czy interną a medycyną ogólną. Pomimo tych 
przypadków, model zachowuje stabilność i nie wykazuje oznak przeuczenia. 

<p>
<img width="296" height="277" alt="image" src="https://github.com/user-attachments/assets/c360803f-e8c8-4383-a146-3ee40778e35b" />
</p>
Podsumowując, model XGBoost wykazał się wysoką skutecznością w przypisywaniu 
przypadków medycznych do odpowiednich specjalizacji. Uzyskane wyniki potwierdzają jego 
przydatność w zadaniach klasyfikacyjnych, zwłaszcza tam, gdzie istotne są stabilność 
działania, przejrzystość decyzji oraz niska złożoność obliczeniowa. Dzięki dobrej równowadze 
między precyzją a czułością, model ten może być z powodzeniem stosowany jako szybkie 
i niezawodne narzędzie wspomagające analizę danych medycznych.

### Ocena modelu MarianMT 
Jakość tłumaczeń uzyskanych z modelu MarianMT została oceniona z wykorzystaniem 
metryk automatycznych. Metryka BLEU równa 0,23 oraz chrF  równa 0,76 oraz subiektywnej 
oceny eksperckiej, gdzie średnia nota to około 4,2 na 5. Analizie poddano: nazwy chorób, 
alergeny oraz nazwy badaniach laboratoryjnych, opisy objawów. Do oceny jakości tłumaczeń 
wybrano losowo 10% danych, które następnie przetłumaczono z wykorzystaniem narzędzia 
„Google Translator”. Analizie poddano je według następujących kryteriów: poprawność terminologiczną, wierność znaczeniową względem oryginału, naturalność językową oraz 
obecność błędów, mogących prowadzić do nieporozumień klinicznych. Metryka BLEU (0,23) 
oznacza umiarkowaną zgodność tłumaczenia z wersją referencyjną na poziomie ciągów słów 
(tzw. n-gramów). Wartość 0,23 wskazuje, że model w części przypadków poprawnie 
odwzorowuje struktury językowe oryginału, ale często stosuje inne formy lub popełnia 
uproszczenia. Wynik ten sugeruje, że tłumaczenia nie są bliskie dosłownemu odwzorowaniu 
tekstu źródłowego. Metryka chrF (0,76) mierzy podobieństwo na poziomie znaków i jest 
szczególnie przydatna w językach fleksyjnych, takich jak polski. Wartość 0,76 wskazuje na 
stosunkowo wysoką zgodność pod względem formy i składni. Nawet jeśli tłumaczenie nie jest 
identyczne ze wzorcem, to na poziomie morfologii i końcówek wyrazów model często generuje 
poprawne konstrukcje. Dobrze radził sobie z prostymi i popularnymi terminami medycznymi, 
jednak trudności pojawiały się w przypadku rzadkich jednostek chorobowych, specjalistycznej 
terminologii i skrótów laboratoryjnych. W tłumaczeniach nazw chorób większość wyników 
była poprawna, choć odnotowano pojedyncze błędy, takie jak błędne odwzorowanie choroby 
„Chronic Lyme Disease”. W zakresie alergenów MarianMT prawidłowo tłumaczył najczęściej 
spotykane nazwy („Penicillin”, „Peanuts”), ale generował halucynacje przy mniej 
jednoznacznych terminach. Najlepsze wyniki uzyskano w przypadku danych laboratoryjnych. 
Większość skrótów została poprawnie zachowana, choć zdarzały się przekłamania wynikające 
z błędnej obsługi znaków. MarianMT zapewnia dobrą jakość tłumaczeń medycznych 
w kontekście podstawowej terminologii, natomiast w przypadku terminów specjalistycznych 
i rzadziej spotykanych wymaga dodatkowej walidacji. Pojedyncze błędy oraz halucynacje 
wskazują, że przy zastosowaniach klinicznych konieczne jest wsparcie eksperta lub dodatkowy 
etap automatycznej kontroli jakości.


## Wnioski i komentarze 
Realizacja projektu rozpoczęła się od analizy literaturowej dotyczącej wykorzystania 
algorytmów uczenia maszynowego i głębokiego w medycynie, a w szczególności 
w diagnostyce oraz predykcji ryzyka zdrowotnego. Przegląd dostępnych źródeł pozwolił na 
sformułowanie założeń, że zastosowanie modeli takich jak Mistral, HerBERT czy XGBoost 
umożliwia skuteczne przetwarzanie danych ankietowych i laboratoryjnych, co może realnie 
wspierać procesy diagnostyczne i decyzje lekarzy. 
W ramach pracy przygotowano aplikację z intuicyjnym interfejsem użytkownika, 
pozwalającą na wprowadzanie danych profilowych, wypełnianie ankiet oraz integrację 
z wynikami badań laboratoryjnych. Dane te stanowiły bazę do przeprowadzania analiz 
z użyciem wybranych modeli uczenia maszynowego. Implementacja objęła również moduł 
zarządzania specjalistami, monitoring nawyków oraz moduł wiadomości, dzięki czemu 
system wspiera zarówno stronę pacjenta, jak i lekarza. 
Istotnym elementem realizacji projektu było odpowiednie przygotowanie oraz wzbogacenie 
danych treningowych i testowych. Wykorzystano dwa główne zbiory: MedSynora DW 
(syntetyczna hurtownia danych medycznych) oraz Symptom-Disease Dataset (zbiór objawów 
i odpowiadających im chorób). Pierwszy z nich posłużył jako główny materiał do analizy 
i trenowania modelu XGBoost, drugi zaś stanowił uzupełnienie w procesie doskonalenia 
modelu HerBERT. Dane były oczyszczane, tłumaczone, ujednolicane oraz filtrowane w taki 
sposób, aby odpowiadały wymaganiom poszczególnych algorytmów. 
Dodatkowo przygotowano bazę wiedzy w formacie PDF i TXT, obejmującą definicje 
specjalistów oraz fragmenty literatury medycznej, które zostały wykorzystane w modelu 
Mistral z mechanizmem RAG. Pozwoliło to na wzbogacenie procesu analizy o kontekst 
ekspercki, poprawiając trafność i użyteczność generowanych rekomendacji. W części eksperymentalnej przeprowadzono ocenę działania modeli. Model Mistral w trybie 
zero-shot, bez dodatkowej bazy wiedzy, osiągnął skuteczność klasyfikacji na poziomie 71%, 
natomiast jego wariant z mechanizmem RAG poprawił wynik do 78%. Obie wersje dobrze 
radziły sobie z logicznym łączeniem objawów i sugerowaniem potencjalnych specjalistów, 
jednak miały tendencję do nadmiernego przypisywania kilku klas jednocześnie. Dodatkowo, 
model ten umożliwił skuteczne generowanie opisów chorób oraz przypisywanie etykiet 
specjalistycznych do jednostek chorobowych, co zwiększa interpretowalność wyników dla 
lekarzy. 
Model HerBERT, po retreningu na danych z aplikacji, osiągnął dokładność 97,3%, przy 
wartościach F1-macro 0,974 i F1-weighted 0,976. Wyniki te potwierdzają bardzo wysoką 
skuteczność oraz zdolność generalizacji modelu, bez oznak przeuczenia. Analiza macierzy 
pomyłek wykazała nieliczne błędy, głównie pomiędzy klasami o podobnym profilu 
klinicznym (np. neurologia i psychiatria), co wynika raczej z nakładania się objawów niż 
z niedoskonałości samego modelu. 
Model XGBoost, oparty na danych ankietowych i laboratoryjnych, uzyskał dokładność 
87,4%, przy średnich wynikach F1-macro 0,845 i F1-weighted 0,874. Wysoką skuteczność 
odnotowano zwłaszcza w specjalizacjach o jednoznacznych profilach (nefrologia, 
pulmonologia, hematologia, hepatologia), natomiast trudności występowały w kategoriach 
mniej licznych lub o szerokim spektrum objawów (pediatria, medycyna zawodowa, 
ginekologia). 
W przypadku modelu MarianMT, zastosowanego do tłumaczenia terminów medycznych 
z języka angielskiego na polski, średnia ocena ekspercka jakości tłumaczeń wyniosła 4,2/5. 
Metryki automatyczne wskazały na umiarkowaną zgodność ze wzorcami (BLEU = 0,23, chrF 
= 0,76). Model dobrze radził sobie z prostymi i popularnymi terminami, natomiast trudności 
pojawiały się przy terminologii specjalistycznej, rzadkich jednostkach chorobowych oraz 
skrótach laboratoryjnych. Pojedyncze błędy krytyczne i halucynacje wskazują na konieczność 
dodatkowej walidacji w przypadku zastosowań klinicznych. 
Przeprowadzone testy potwierdziły postawioną hipotezę badawczą. Parametry zdrowotne 
pacjentów, wspierane algorytmami predykcyjnymi, pozwalają skutecznie przewidywać 
potencjalne problemy zdrowotne i dostarczać wartościowych, interpretowalnych informacji 
zarówno dla lekarzy, jak i pacjentów. Największym wyzwaniem pozostaje jakość danych 
wejściowych, niekompletne ankiety oraz brak wyników badań ograniczały dokładność 
predykcji. Jednak zastosowanie mechanizmów filtracji oraz możliwość retreningu modeli 
pozwoliły w znacznym stopniu zminimalizować ten problem. 
Efektem końcowym jest opracowany system, który łączy elementy aplikacji dla pacjenta 
i lekarza oraz implementuje różne algorytmy uczenia maszynowego do analizy danych 
zdrowotnych. System ten może być w przyszłości rozwijany o dodatkowe moduły m.in. 
integrację z urządzeniami ubieralnymi, wizualizację trendów zdrowotnych czy rozszerzenie 
bazy wiedzy dla modeli generatywnych. 
