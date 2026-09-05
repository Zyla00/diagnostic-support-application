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

**Keywords:** web application, clinical decision support, machine learning, natural language processing (NLP), XGBoost, HerBERT, Mistral, RAG

## Web application interface

### Rejestracja oraz logowanie użytkownika 

W aplikacji MedPred proces logowania i rejestracji użytkowników został 
zaprojektowany w sposób intuicyjny i prosty. Nowi użytkownicy mogą założyć konto, 
wybierając jedną z dwóch ról: Pacjent lub Specjalista. Formularz rejestracyjny przewiduje 
różne pola w zależności od wybranej roli – w przypadku specjalisty konieczne jest dodatkowe 
podanie numeru licencji zawodowej. System posiada również wbudowany mechanizm 
walidacji danych – w sytuacji, gdy wprowadzone hasła różnią się od siebie, adres e-mail jest 
już zajęty, bądź wybrana nazwa użytkownika jest niedostępna, aplikacja wyświetla odpowiedni 
komunikat błędu. Dzięki temu proces rejestracji jest zabezpieczony przed duplikacją kont 
i nieprawidłowym wprowadzeniem danych. Na rysunku 7.1.A przedstawiono ekran logowania, 
gdzie użytkownik musi podać swoją nazwę oraz hasło, a dodatkowo ma możliwość zaznaczenia 
opcji Pamiętaj mnie. Na rysunku 7.1.B znajdują się przykładowe komunikaty błędów – w tym 

<p>
<img width="253" height="296" alt="image" src="https://github.com/user-attachments/assets/5e60e275-6dde-4808-8ff1-cf36947fdda1" />
</p>

Cały mechanizm logowania i rejestracji zapewnia przejrzystość oraz bezpieczeństwo 
korzystania z aplikacji. Dzięki odpowiedniej walidacji danych użytkownicy mają pewność, że 
ich konta są unikalne i chronione przed nieuprawnionym dostępem.

#### Informacje profilowe oraz zmiana hasła 

W aplikacji MedPred użytkownik ma dostęp do panelu zarządzania swoim kontem 
poprzez ikonę awatara znajdującą się w lewym dolnym rogu paska bocznego. Po kliknięciu 
w tę ikonę rozwija się menu z trzema opcjami: Profil, Zmień hasło oraz Wyloguj (rysunek 
7.2.A). Dzięki temu specjalista może w prosty sposób zarządzać informacjami dotyczącymi 
swojego konta. 
Wybór opcji Zmień hasło powoduje wysunięcie się panelu z prawej strony ekranu (rysunek 
7.2.B). Panel ten zawiera formularz umożliwiający wpisanie starego hasła, wprowadzenie 
nowego oraz jego potwierdzenie. Po zatwierdzeniu zmian przyciskiem Zapisz zmiany, system 
wyświetla w prawym górnym rogu stosowny komunikat informujący o poprawnym zapisaniu 
nowego hasła lub o ewentualnym błędzie, np. niezgodności haseł.

<p>
<img width="254" height="233" alt="image" src="https://github.com/user-attachments/assets/4d67d8ef-d94c-46d0-bd5c-8bd25e23df56" />
</p>

Analogicznie, wybierając opcję Profil, użytkownikowi wyświetla się widok podglądu profilu 
(rysunek 7.3). Znajdują się tam wszystkie kluczowe dane specjalisty, takie jak imię, nazwisko, 
adres e-mail, telefon, numer PWZ, adres przyjęć, wykształcenie, doświadczenie zawodowe czy 
specjalizacja. 

<p>
<img width="259" height="151" alt="image" src="https://github.com/user-attachments/assets/d57609aa-655b-44f6-9575-e8572e1a6ae2" />
</p>

W prawym górnym rogu widoczny jest przycisk umożliwiający przejście do trybu edycji. Po 
jego wybraniu otwiera się panel z formularzem (rysunek 7.4), w którym specjalista może 
uzupełniać lub modyfikować wszystkie pola. Po zapisaniu zmian system ponownie generuje 
komunikat potwierdzający operację. Zarówno panel zmiany hasła, jak i panel profilu można 
zamknąć na dwa sposoby: klikając w krzyżyk w prawym górnym rogu lub klikając 
w zaciemnione pole po lewej stronie ekranu.

<p>
<img width="276" height="157" alt="image" src="https://github.com/user-attachments/assets/07f910a4-78cc-4e38-9965-b9bbf2e964b7" />
</p>

Warto podkreślić, że widok profilu pacjenta różni się od widoku dostępnego dla specjalisty 
(rysunek 7.5). Zawiera on podstawowe informacje osobowe i kontaktowe, takie jak imię, 
nazwisko, data urodzenia, numer PESEL, adres e-mail, numer telefonu oraz dane dotyczące 
ubezpieczenia zdrowotnego (np. NFZ). W odróżnieniu od profilu specjalisty nie ma tu pól 
związanych z wykształceniem, numerem PWZ czy doświadczeniem zawodowym, co wynika 
z odmiennej roli pacjenta w systemie. 

<p>
<img width="262" height="110" alt="image" src="https://github.com/user-attachments/assets/b7996cf8-c897-4979-9952-49ef52ba32f4" />
</p>
Profil pacjenta jest zatem uproszczony, ale zawiera wszystkie istotne dane niezbędne w procesie 
diagnostycznym i komunikacji ze specjalistą.

#### Wiadomości

Funkcjonalność wiadomości umożliwia bezpośrednią i wygodną komunikację pomiędzy 
pacjentem a specjalistą. Dzięki niej możliwe jest zadawanie pytań, ustalanie szczegółów 
diagnostyki czy konsultowanie zmian w planie leczenia w czasie rzeczywistym. System 
zapewnia przejrzyste oznaczenia nowych wiadomości, co minimalizuje ryzyko ich 
przeoczenia. Na rysunku 7.6 przedstawiono widok paska bocznego, na którym obok zakładki 
Wiadomości pojawia się czerwona ikona z liczbą nowych wiadomości. Dzięki temu użytkownik 
od razu widzi, że w skrzynce oczekuje nowa korespondencja.

<p>
<img width="156" height="78" alt="image" src="https://github.com/user-attachments/assets/6afbdeb2-8f3f-417f-bcfd-64fe02be42ea" />
</p>

Po kliknięciu w zakładkę Wiadomości otwiera się panel czatu (rysunek 7.7). Z lewej strony 
znajduje się lista pacjentów lub specjalistów, wraz z podglądem ostatniej wiadomości. Nowe 
wiadomości oznaczane są dodatkowym czerwonym komunikatem z liczbą oczekujących 
wiadomości, co ułatwia ich szybkie odnalezienie. 

<p>
<img width="209" height="155" alt="image" src="https://github.com/user-attachments/assets/5ff41235-38ed-41b2-bc69-92e6693df0a1" />
</p>

Po wybraniu rozmówcy użytkownik przechodzi do szczegółowego widoku konwersacji 
(rysunek 7.8). W tym miejscu dostępna jest cała historia czatu oraz możliwość swobodnego 
prowadzenia dalszej korespondencji. Wiadomości są prezentowane w sposób intuicyjny. 
Użytkownik widzi zarówno swoje wiadomości, jak i odpowiedzi rozmówcy, wraz z datą 
i godziną ich wysłania.

<p>
<img width="178" height="158" alt="image" src="https://github.com/user-attachments/assets/cf255cbe-1602-4e0d-9a23-4aed9c0c0bbb" />  
</p>

System wiadomości w aplikacji pełni rolę bezpośredniego kanału komunikacji, który zwiększa 
dostępność specjalisty i umożliwia szybkie reagowanie na potrzeby pacjenta. Jasne oznaczenia 
nowych wiadomości oraz prosty interfejs czatu sprawiają, że korzystanie z tej funkcjonalności 
jest intuicyjne i efektywne. 

### Funkcjonalności dostępne dla specjalisty

Po zalogowaniu się do aplikacji specjalista otrzymuje dostęp do widoku listy swoich 
pacjentów. Bezpośrednio po rejestracji lista ta jest pusta, natomiast wraz z przypisaniem 
pierwszych osób pojawiają się tutaj pacjenci danego specjalisty. Każdy rekord na liście zawiera 
imię i nazwisko pacjenta oraz informację o jego statusie – aktywnym lub nieaktywnym. 
Dodatkowo dostępne jest pole wyszukiwania, które umożliwia szybkie odnalezienie pacjenta 
po imieniu lub nazwisku. 
Po lewej stronie znajduje się boczny pasek nawigacyjny, który został zaprojektowany w formie 
wsuwanego panelu. Może on być zarówno rozwinięty (rysunek 7.9), jak i zwinięty (rysunek 
7.10), co pozwala na oszczędność miejsca w głównym obszarze roboczym. Pasek boczny 
zawiera cztery kluczowe sekcje: 
• Pacjenci – zakładka prezentująca listę przypisanych pacjentów wraz z możliwością ich 
wyszukiwania, umożliwia również wybranie (poprzez kliknięcie) i podgląd bardziej 
szczegółowych informacji na temat danej osoby, 
• Menadżer ankiet – moduł umożliwiający podgląd, tworzenie oraz edycję ankiet, które 
mogą być następnie udostępniane pacjentom, 
• Modele predykcyjne – sekcja pozwalająca na ingerencję w działanie systemu 
predykcyjnego, w tym na retrening istniejących modeli na podstawie nowych danych 
pochodzących od pacjentów oraz na wzbogacanie bazy wiedzy w mechanizmie RAG, 
• Wiadomości – miejsce do wymiany informacji między specjalistą a pacjentami, 
ułatwiające bieżący kontakt i szybkie reagowanie na potrzeby chorych. 
Na rysunku 7.9 przedstawiono widok listy pacjentów w momencie, gdy specjalista nie ma 
jeszcze przypisanych żadnych osób. 

<p>
<img width="260" height="143" alt="image" src="https://github.com/user-attachments/assets/f23a0ab5-39b1-403e-af79-f9db1023489f" />  
</p>
Natomiast rysunek 7.10 prezentuje sytuację, w której pacjenci są już przypisani – można ich 
przeglądać wraz ze statusem aktywności.  

<p>
<img width="260" height="151" alt="image" src="https://github.com/user-attachments/assets/11028644-81f4-4fce-95f1-1846dfdbd42b" />
</p>
Oba widoki dobrze obrazują zarówno elastyczność interfejsu, jak i możliwość dostosowania 
przestrzeni roboczej do aktualnych potrzeb użytkownika.


#### Karta pacjenta i analiza danych

Po przejściu do zakładki Pacjenci i wybraniu konkretnego pacjenta (aktywnego lub 
nieaktywnego), system przenosi specjalistę do karty pacjenta, gdzie na samej górze 
wyświetlana jest podstawowa informacja identyfikacyjna (rysunek 7.11). Poniżej dostępne są 
cztery zakładki: Rekomendacje, Ankiety, Badania laboratoryjne oraz AI. 
Zakładka Rekomendacje (rysunek 7.11) umożliwia lekarzowi wpisanie nowej rekomendacji, 
która natychmiast trafia do pacjenta i pojawia się również w jego panelu startowym. Dostępna 
jest też pełna historia wcześniejszych zaleceń.

<p>
<img width="262" height="193" alt="image" src="https://github.com/user-attachments/assets/6865dc5d-188c-4d21-8d4f-cc4e7950e2b1" />  
</p>

Zakładka Ankiety (rysunki 7.12.A–D) zawiera historię ankiet wysyłanych do danego pacjenta. 
Każda ankieta ma oznaczenie  „Wypełniona” (zielony znacznik) lub „Niewypełniona” (szary 
znacznik). Lekarz może wyświetlić zawartość ankiety zarówno przed wypełnieniem (podgląd 
pytań), jak i po jej uzupełnieniu (z odpowiedziami pacjenta). Po prawej stronie znajduje się 
pole wyszukiwania, w którym można znaleźć i wybrać dowolną ankietę z dostępnych 
(systemowych lub stworzonych przez specjalistę). Po wybraniu ankiety pojawia się okno 
potwierdzenia wysyłki (rysunek 7.12.C). Wysłanie ankiety jest procesem nieodwracalnym. Nie 
można jej edytować ani cofnąć.

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


### Evaluation of the HerBERT Model After Training

The HerBERT model was retrained to perform classification of medical cases into appropriate medical specialties. Evaluation on the validation and test datasets showed very high performance, with accuracy reaching 97.38% on the validation set and 97.29% on the test set.

The results were also confirmed by the F1 metrics. F1-macro reached 0.9745 for the validation set and 0.9744 for the test set, while F1-weighted achieved 0.9769 and 0.9758, respectively. The small differences between validation and test results indicate good generalization and no significant signs of overfitting.

The training curves further supported these findings. After an initial increase, accuracy stabilized at approximately 97%, while the validation and test curves remained closely aligned until the end of training. This suggests that the model achieved a good balance between fitting the training data and maintaining high performance on previously unseen cases.

Overall, the retrained HerBERT model demonstrated high and stable classification performance, confirming its effectiveness for assigning medical cases to relevant specialties.


<p>
<img width="652" height="358" alt="image" src="https://github.com/user-attachments/assets/4ec80e32-2568-453d-8096-e897a0c71761" />
</p>

<p>
  <img width="652" height="358" alt="image" src="https://github.com/user-attachments/assets/a93a5323-3e1f-4ce3-a2f3-251e78d4e2d0" />
</p>

The confusion matrix (Figure 8.3) provides a detailed overview of classification performance across individual medical specialties. The strong concentration of values along the main diagonal confirms that the model correctly classified the vast majority of cases.

Several categories were recognized with particularly high accuracy, including Neurology with 1,176 correctly classified cases, Pulmonology with 936, and Orthopedics with 1,377. Only a small number of misclassifications were observed, mainly between specialties with overlapping clinical symptoms. For example, Psychiatry was occasionally confused with Neurology, while Oncology was sometimes misclassified as Hematology or Gastroenterology.

These errors are likely related to genuine similarities between clinical presentations rather than major limitations of the model itself. Overall, the confusion matrix confirms the high classification accuracy and consistency of the retrained HerBERT model.


<p>
<img width="656" height="576" alt="image" src="https://github.com/user-attachments/assets/613013d6-dc10-413f-bf8d-63bbd22b6c3c" />
</p>
Overall, the retrained HerBERT model demonstrated high accuracy, stable performance, and very good generalization, with no clear signs of overfitting. Combined with the low loss values and relatively few classification errors, these results indicate that the model is an effective tool for supporting the automatic classification of medical cases into relevant specialties.


### Evaluation of the XGBoost Model

The XGBoost model was used as a classifier to assign medical cases to appropriate medical specialties. Its performance was evaluated on a large test dataset containing 29,571 examples across 26 classes. The analysis included accuracy, precision, recall, and F1-score, both overall and for individual classes.

The model achieved an overall accuracy of 87.4%, indicating solid performance in classifying medical cases. The average metrics, including F1-score of 0.8454, precision of 0.8937, and recall of 0.8127, confirm that the model performed well across both common and less represented classes. The higher precision compared to recall also suggests a slightly conservative classification approach.

The best results were observed for specialties with clearly defined clinical profiles, including Nephrology (F1 = 0.96), Pulmonology (0.96), Hepatology (0.97), and Hematology (0.95). Lower performance was recorded for more challenging classes such as Pediatrics (F1 = 0.62), Occupational Medicine (0.68), Gynecology (0.71), and Emergency Medicine (0.73). These differences were likely caused by a smaller number of training examples and overlapping symptoms between specialties.

The confusion matrix showed that most predictions were correctly classified along the main diagonal. However, some errors occurred between clinically related specialties, such as Neurology and Psychiatry or Internal Medicine and General Medicine. Despite these misclassifications, the model remained stable and showed no clear signs of overfitting.


<p>
<img width="656" height="576" alt="image" src="https://github.com/user-attachments/assets/c360803f-e8c8-4383-a146-3ee40778e35b" />
</p>

Overall, the XGBoost model demonstrated high effectiveness in assigning medical cases to appropriate specialties. The obtained results confirm its usefulness for classification tasks, particularly where stable performance, decision transparency, and relatively low computational complexity are important. Thanks to a good balance between precision and recall, the model can serve as a fast and reliable tool for supporting the analysis and classification of medical data.


### Evaluation of the MarianMT Model

The quality of translations generated by the MarianMT model was evaluated using both automatic metrics and expert assessment. The model achieved a BLEU score of 0.23 and a chrF score of 0.76, while the average expert rating was approximately 4.2 out of 5. The evaluation covered disease names, allergens, laboratory test names, and symptom descriptions.

A randomly selected 10% of the dataset was compared with translations produced using Google Translator. The assessment focused on terminological accuracy, semantic consistency, linguistic naturalness, and the presence of errors that could potentially lead to clinical misunderstandings.

The BLEU score of 0.23 indicates moderate similarity to the reference translations at the word-sequence level, suggesting that the model often used alternative wording or simplified certain expressions. In contrast, the chrF score of 0.76 indicates relatively high similarity at the character level, which is particularly relevant for morphologically rich languages such as Polish.

MarianMT performed well with common and straightforward medical terminology but showed difficulties with rare diseases, specialized terms, and laboratory abbreviations. Most disease names and common allergens were translated correctly, while occasional errors and hallucinations appeared in less common or ambiguous terms. The best performance was observed for laboratory data, where most abbreviations were preserved correctly.

Overall, MarianMT provided good translation quality for basic medical terminology. However, specialized and less frequent terms require additional validation. Occasional errors and hallucinations indicate that expert review or an additional quality-control stage would be necessary for clinical applications.



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

