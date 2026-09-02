# diagnostic-support-application

### Abstract  
The project developed a web application for early patient health risk assessment, integrating 
profile data, test results, and surveys to support primary care physicians in the diagnostic 
process and clinical decision-making. Machine learning and natural language processing (NLP) 
models were used for data analysis: XGBoost, HerBERT, Mistral, and its variant enriched with 
an additional knowledge base (RAG), as well as MarianMT for translation. The HerBERT and 
XGBoost models were trained on datasets of 154,896 and 147,853 cases, respectively, spanning 
26 classes representing medical specialties. The XGBoost model achieved 87.4% accuracy, 
HerBERT 97.3%, and Mistral and Mistral, with an external knowledge base, achieved 71% and 
78% correct classifications, respectively. Implementation required Python with the pandas, 
NumPy, scikit-learn, PyTorch, and Transformers libraries, and the Django framework for 
interface development. The developed system combines medical case classification, model 
retraining and patient data analysis.

**Keywords:** web application, clinical decision support, machine learning, natural language 
processing (NLP), XGBoost, HerBERT, Mistral, RAG

## Evaluation of Results

### Classification

For the task of assigning patient symptoms to appropriate medical specialists, the Mistral model was evaluated in two configurations: zero-shot, without additional training, and with a Retrieval-Augmented Generation (RAG) mechanism supported by an external knowledge base. The experiment was conducted on 260 cases, with 10 cases representing each medical specialty. 

The zero-shot Mistral model achieved an overall classification accuracy of 71%. It demonstrated a good understanding of symptoms and was generally able to suggest relevant specialists. However, it often produced overly broad recommendations by assigning several specialists to a single case, including less relevant ones. This tendency resulted from limited ability to eliminate unlikely diagnostic hypotheses, particularly when symptom descriptions were incomplete or ambiguous.

The RAG-enhanced version of Mistral improved classification accuracy to 78%. Access to an external medical knowledge base enabled better interpretation of less obvious symptom combinations and more accurate specialist selection. Nevertheless, the model still occasionally suggested multiple specialists instead of identifying the single most probable category.

Both configurations demonstrated strong natural language understanding and the ability to logically connect symptoms with possible medical specialties. The main limitation was excessive caution, leading to overestimation of the number of recommended specialists.

It should also be noted that the evaluation was performed on cases containing relatively complete symptom descriptions and laboratory results and did not include highly complex clinical scenarios. Therefore, further evaluation on more diverse and challenging medical cases would be necessary to assess the model’s suitability for broader clinical use.

### Generation of Disease Descriptions

Disease symptom descriptions were generated using the Mistral language model supported by a custom external medical knowledge base. Each generated description was then evaluated again using Mistral, both with and without access to the knowledge base. This validation followed an “LLM-as-a-judge” approach, where the model assessed the generated content for potential inconsistencies, inaccuracies, or anomalies.

During the first validation stage, 17% of cases (52 out of 301) were identified as requiring revision due to minor or more significant inaccuracies. These descriptions were subsequently corrected according to the model’s suggestions. An additional 10% of cases (30 out of 301) were considered correct but relatively general. Since the objective was to represent the most common and characteristic symptoms rather than provide exhaustive clinical descriptions, these cases were accepted without modification.

After the revision process, validation was repeated. No major errors were identified, although 12% of cases (36 out of 301) were marked as requiring caution due to minor omissions or simplifications.

To further assess reliability, 10% of all records (31 out of 301) were manually reviewed against medical literature. No significant factual errors were found. Approximately 9% of the manually reviewed cases (3 out of 31) were considered overly simplified and could potentially be expanded with additional common symptoms.

Overall, the adopted generation and validation procedure provided sufficiently accurate and consistent symptom descriptions for the purposes of this study while maintaining a practical balance between completeness and usability.

### Generation of Data Labels

A separate data preparation stage focused on assigning medical specialty labels to predefined disease entities. Since the input dataset contained disease names but no information about the most relevant medical specialty, Mistral was used to generate these labels with support from the same external medical knowledge base.

The generated labels were automatically validated using the same “LLM-as-a-judge” approach. For consistency within the classification task, each disease was assigned one primary medical specialty, even though many conditions may in practice involve several specialists.

Among 1,081 diseases, the model did not identify any major errors in the assigned primary specialties. However, approximately 30% of cases (324 out of 1,081) were identified as potentially associated with at least one additional specialty, depending on the clinical context or progression of the disease.

A manual review was also conducted on approximately 10% of the dataset (109 out of 1,081 cases). No cases were found in which the assigned primary specialty was clearly incorrect or inappropriate.

The final labeling strategy therefore represents a deliberate simplification intended to support a consistent classification structure rather than reproduce complete diagnostic pathways. The resulting dataset reflects a compromise between medical accuracy, consistency, and practical usefulness for the purposes of this project.


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


## Conclusions and Comments

The project began with a literature review on the use of machine learning and deep learning in medicine, particularly in diagnostics and health risk prediction. The analysis indicated that models such as Mistral, HerBERT, and XGBoost can effectively process survey and laboratory data and support clinical decision-making.

As part of the project, an application was developed with an intuitive user interface enabling patients to enter profile information, complete medical questionnaires, and integrate laboratory test results. The system also included specialist management, habit monitoring, and messaging modules, supporting both patients and healthcare professionals.

Two main datasets were used for model development: MedSynora DW, a synthetic medical data warehouse used primarily for training XGBoost, and the Symptom-Disease Dataset, which supported the improvement of the HerBERT model. The data were cleaned, translated, standardized, and filtered according to the requirements of each algorithm. Additionally, a medical knowledge base in PDF and TXT formats was created and integrated with the Mistral model using a Retrieval-Augmented Generation (RAG) approach.

Experimental results confirmed the effectiveness of the developed models. Mistral achieved 71% classification accuracy in the zero-shot setting and 78% when supported by RAG. The model was capable of connecting symptoms, suggesting relevant specialists, generating disease descriptions, and assigning medical specialty labels, although it occasionally predicted multiple classes excessively.

After retraining, HerBERT achieved an accuracy of 97.3%, with F1-macro of 0.974 and F1-weighted of 0.976. The model showed strong generalization capabilities, with only minor errors between specialties with overlapping clinical symptoms, such as neurology and psychiatry.

XGBoost achieved an accuracy of 87.4%, with F1-macro of 0.845 and F1-weighted of 0.874. It performed particularly well for specialties with clearly defined clinical profiles, including nephrology, pulmonology, hematology, and hepatology, while lower performance was observed for less represented or more diverse categories.

The MarianMT model, used for translating medical terminology from English into Polish, received an average expert evaluation score of 4.2/5. Automatic metrics produced BLEU = 0.23 and chrF = 0.76. While the model handled common terminology effectively, difficulties occurred with specialized terms, rare diseases, and laboratory abbreviations, indicating the need for additional validation in clinical applications.

Overall, the experiments confirmed the research hypothesis that patient health parameters combined with predictive algorithms can effectively identify potential health problems and provide useful, interpretable information for both patients and physicians. The main limitation remains the quality and completeness of input data, particularly incomplete questionnaires and missing laboratory results.

The final system integrates patient and physician functionalities with several machine learning approaches for health data analysis. Future development could include integration with wearable devices, visualization of health trends, and further expansion of the knowledge base used by generative models.

