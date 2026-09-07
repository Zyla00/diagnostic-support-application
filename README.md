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

### User Registration and Login

The MedPred application provides a simple and intuitive user authentication system. New users can create an account by selecting one of two roles: **Patient** or **Specialist**. The registration form is adjusted to the selected role. Specialists are additionally required to provide their professional license number.

The system validates the entered data during registration. Appropriate error messages are displayed when passwords do not match, an email address is already registered, or a username is unavailable. This prevents duplicate accounts and reduces incorrect data entry.

Figure 7.1.A presents the login screen, where users enter their username and password and can select the **Remember me** option. Figure 7.1.B shows examples of validation and authentication error messages.

<p>
<img width="506" height="592" alt="image" src="https://github.com/user-attachments/assets/5e60e275-6dde-4808-8ff1-cf36947fdda1" />
</p>

Overall, the registration and login process ensures secure and convenient access to the application while maintaining the uniqueness and validity of user accounts.

#### Profile Information and Password Change

In the MedPred application, users can manage their account through the avatar icon located in the lower-left corner of the sidebar. Clicking the icon opens a menu with three options: Profile, Change Password, and Log Out (Figure 7.2.A).

The Change Password option opens a side panel containing fields for the current password, the new password, and its confirmation (Figure 7.2.B). After saving the changes, the system displays a notification confirming success or informing the user about an error, such as mismatched passwords.

<p>
<img width="506" height="466" alt="image" src="https://github.com/user-attachments/assets/4d67d8ef-d94c-46d0-bd5c-8bd25e23df56" />
</p>

The Profile view presents the user’s account information. For specialists, it includes personal and professional data such as name, email address, phone number, professional license number, workplace address, education, experience, and specialization (Figure 7.3). The profile can be edited using the button in the upper-right corner, which opens an editable form (Figure 7.4). After saving, the system displays a confirmation message.

<p>
<img width="506" height="302" alt="image" src="https://github.com/user-attachments/assets/d57609aa-655b-44f6-9575-e8572e1a6ae2" />
</p>

<p>
<img width="506" height="314" alt="image" src="https://github.com/user-attachments/assets/07f910a4-78cc-4e38-9965-b9bbf2e964b7" />
</p>

The patient profile contains a simpler set of information, including personal and contact details, date of birth, PESEL number, and health insurance information (Figure 7.5). Unlike the specialist profile, it does not include professional fields such as education, license number, or work experience.

<p>
<img width="506" height="220" alt="image" src="https://github.com/user-attachments/assets/b7996cf8-c897-4979-9952-49ef52ba32f4" />
</p>

Both the profile and password panels can be closed using the close button or by clicking outside the panel.

#### Messages

The Messages feature enables direct communication between patients and specialists. It can be used to ask questions, discuss diagnostic details, and consult changes in the treatment plan.

New messages are clearly indicated in the sidebar by a red badge showing the number of unread messages (Figure 7.6). After opening the Messages section, the user sees a list of conversations with a preview of the latest message and unread message indicators (Figure 7.7).

<p>
<img width="312" height="156" alt="image" src="https://github.com/user-attachments/assets/6afbdeb2-8f3f-417f-bcfd-64fe02be42ea" />
</p>

<p>
<img width="506" height="310" alt="image" src="https://github.com/user-attachments/assets/5ff41235-38ed-41b2-bc69-92e6693df0a1" />
</p>

Selecting a conversation opens the full chat view, where the entire message history is available (Figure 7.8). Messages from both participants are displayed together with their date and time of delivery.

<p>
<img width="506" height="316" alt="image" src="https://github.com/user-attachments/assets/cf255cbe-1602-4e0d-9a23-4aed9c0c0bbb" />  
</p>

This module provides a simple and accessible communication channel between patients and specialists, allowing users to quickly identify and respond to new messages.

### Features Available to Specialists

After logging in, a specialist has access to the list of assigned patients. Initially, the list is empty, but it is automatically populated as patients are assigned to the specialist. Each entry contains the patient’s name and current status, such as active or inactive. A search field allows patients to be quickly found by name or surname.

Navigation is provided through a collapsible sidebar, which can be displayed in expanded or compact form (Figures 7.9 and 7.10). It contains four main sections:

Patients – displays assigned patients and provides access to their detailed information.
Survey Manager – allows specialists to create, view, and edit surveys that can later be assigned to patients.
Predictive Models – provides tools for retraining predictive models using new patient data and updating the knowledge base used by the RAG mechanism.
Messages – enables direct communication with patients.

Figure 7.9 shows the patient list when no patients have yet been assigned, while Figure 7.10 presents the same view after patients have been added. The collapsible sidebar allows the workspace to be adjusted according to the user’s current needs.

<p>
<img width="506" height="286" alt="image" src="https://github.com/user-attachments/assets/f23a0ab5-39b1-403e-af79-f9db1023489f" />  
</p>

<p>
<img width="506" height="302" alt="image" src="https://github.com/user-attachments/assets/11028644-81f4-4fce-95f1-1846dfdbd42b" />
</p>


#### Patient Record and Data Analysis

After selecting a patient from the Patients section, the specialist is redirected to the patient record, which contains basic identification data and four main tabs: Recommendations, Surveys, Laboratory Tests, and AI.

The Recommendations tab allows the specialist to add new recommendations, which are immediately visible in the patient’s dashboard, as well as review the history of previous recommendations (Figure 7.11).

<p>
<img width="506" height="386" alt="image" src="https://github.com/user-attachments/assets/6865dc5d-188c-4d21-8d4f-cc4e7950e2b1" />  
</p>

The Surveys tab contains all surveys assigned to the patient and indicates whether each survey has been completed. Specialists can preview survey questions before completion and review the patient’s answers afterwards. New surveys can be selected from the available system or custom surveys and sent after confirmation. Once assigned, a survey cannot be edited or withdrawn (Figures 7.12.A–D).

<p>
<img width="506" height="524" alt="image" src="https://github.com/user-attachments/assets/209fbbaa-cab7-47f1-a34b-cb146d9864b9" />
</p>
The Laboratory Tests tab provides access to the history of test results uploaded by the patient. Specialists can review detailed values, including individual laboratory parameters such as hormone levels (Figures 7.13.A–B).

<p>
<img width="506" height="304" alt="image" src="https://github.com/user-attachments/assets/fdcfd0a9-14af-4bc3-9f37-735109ebc64c" /> 
</p>

The AI tab supports patient data analysis using several machine learning models:

XGBoost – classification based on survey and laboratory data,
HerBERT – classification based on survey data,
Mistral – text-based analysis using surveys and laboratory results,
Mistral RAG – analysis enhanced with an external knowledge base.

The specialist selects the model and relevant patient data before starting the analysis. Input data are filtered to match the features used during model training. For Mistral-based models, the specialist can also enter a custom question or use a predefined prompt.

Mistral and Mistral RAG return textual summaries and recommendations, while XGBoost and HerBERT present probability scores for different medical specialties and highlight the most probable result. The RAG variant additionally uses the connected knowledge base to provide broader contextual information (Figures 7.14–7.18).

<p>
<img width="506" height="122" alt="image" src="https://github.com/user-attachments/assets/c6b8fcd1-d998-437d-9839-8861946138e4" />  
</p>
<p>
<img width="506" height="614" alt="image" src="https://github.com/user-attachments/assets/fc1fa2d1-6df9-46f0-866b-fdabb21395fe" />
</p>
<p>
<img width="506" height="280" alt="image" src="https://github.com/user-attachments/assets/fea4880c-c758-45ae-a65b-c6cc2241ff18" />
</p>

<p>
<img width="506" height="136" alt="image" src="https://github.com/user-attachments/assets/57deda2a-a6e1-4913-b4ee-a3fd648abd6f" />
</p>
<p>
<img width="506" height="370" alt="image" src="https://github.com/user-attachments/assets/50cb7d07-4642-4525-9fb8-fb736a944868" />
</p>

<p>
<img width="506" height="124" alt="image" src="https://github.com/user-attachments/assets/9d6d3cbd-af35-49fe-94e2-318b056eb93c" />
</p>

<p>
<img width="506" height="400" alt="image" src="https://github.com/user-attachments/assets/6734a3a9-9051-436d-8ad0-343a2fefef75" />
</p>

The AI output is intended to support, rather than replace, clinical judgment. When several classes receive similar probability scores, the specialist can interpret the results independently and determine further diagnostic steps.

<p>
<img width="506" height="124" alt="image" src="https://github.com/user-attachments/assets/7530a8cf-4774-45e4-b893-9519cf22906c" />
</p>

<p>
<img width="506" height="408" alt="image" src="https://github.com/user-attachments/assets/971683f9-e5bb-447d-91a8-0e132dbb0356" />
</p>

Overall, the patient record combines medical history, surveys, laboratory results, recommendations, and AI-assisted analysis in a single workspace.

#### Survey Manager

The Survey Manager enables specialists to create, edit, and organize surveys that can later be assigned to patients.

The main view displays both system and user-created surveys (Figure 7.18). System surveys are marked with a lock icon and can only be viewed or copied, while custom surveys can be edited, renamed, and deleted. A search field and pagination simplify navigation through larger survey collections.

<p>
<img width="506" height="224" alt="image" src="https://github.com/user-attachments/assets/8ddf8a14-6e3d-4a7a-be05-47c069b3dac1" />
</p>

A new survey can be created using the New Survey button. After entering its name, the survey is added to the list and can be further configured (Figures 7.19.A–B).

<p>
<img width="506" height="142" alt="image" src="https://github.com/user-attachments/assets/bf769e77-80d8-4590-83c0-8bda0d4f42da" />
</p>

In edit mode, specialists can divide the survey into sections and add different types of questions:

 - open-ended text questions,
 - single-choice questions,
 - multiple-choice questions.

<p>
<img width="506" height="660" alt="image" src="https://github.com/user-attachments/assets/eed6c677-2ce8-46ba-bc1f-f68adbc2b914" />
</p>

<p>
<img width="506" height="322" alt="image" src="https://github.com/user-attachments/assets/423ff8fe-632b-4f1c-92f4-2b7439fea4fd" />
</p>

For closed questions, available answers are entered as comma-separated options. Specialists can switch between edit and preview modes before saving the final version (Figures 7.20–7.21).

<p>
<img width="506" height="282" alt="image" src="https://github.com/user-attachments/assets/ff18ac3c-4980-4720-be4d-a8567c9b67f5" />
</p>

The system also displays notifications confirming successful operations or reporting errors. This module provides a structured way to prepare questionnaires for collecting consistent patient information.

#### Predictive Model Management

The Predictive Models section allows specialists to update and extend the AI components used in MedPred. It contains three modules: HerBERT, XGBoost, and Mistral RAG – Notes.

The HerBERT module allows retraining the model using completed patient surveys. Only filled surveys can be selected, while incomplete ones remain disabled. Search and filtering tools help specialists quickly locate relevant training data (Figure 7.21).

<p>
<img width="506" height="390" alt="image" src="https://github.com/user-attachments/assets/30daec9d-e078-4676-acde-202edc20e666" />
</p>

The XGBoost module works similarly but can use both completed surveys and laboratory test results as training data (Figure 7.22). Selected records can then be assigned to a new training case.

<p>
<img width="506" height="268" alt="image" src="https://github.com/user-attachments/assets/27d210bc-5cb2-4efa-9ca7-1037fa8385ee" />
</p>

During case definition, the specialist assigns a label, optionally adds a clinical description, and selects the relevant surveys or laboratory results (Figure 7.23). After saving, the new sample is used to retrain the model. The previous model version is archived automatically, while the updated version becomes available for further predictions.

<p>
<img width="506" height="282" alt="image" src="https://github.com/user-attachments/assets/64914ba5-e703-4794-8aae-951b4a6a485b" />
</p>

The Mistral RAG – Notes module enables specialists to extend the system knowledge base without retraining the model. Notes may contain a title, text, and an optional attachment. After rebuilding the index, the new content can be used during RAG-based analyses and recommendation generation (Figure 7.24).

<p>
<img width="506" height="312" alt="image" src="https://github.com/user-attachments/assets/fac4f09c-1730-4ad5-963a-0c29985443e8" />
</p>

Overall, this section allows specialists to improve model performance and expand the available medical context as new data become available.

### Features Available to Patients

#### Patient Dashboard

After logging in, the patient is redirected to the Recommendations view, which serves as the main dashboard (Figure 7.25). It displays recommendations and comments provided by the assigned specialist, including suggestions based on surveys, laboratory results, and predictive analyses.

The sidebar provides access to the main patient functions:

Recommendations – displays recommendations from the specialist,
Surveys – provides access to completed and newly assigned surveys,
Laboratory Results – stores previous test results and allows new results to be added,
My Doctor – allows the patient to view and change the assigned specialist,
Habits – supports tracking selected health-related habits,
Calendar – displays scheduled appointments and events,
Statistics – presents selected health and well-being indicators,
Messages – enables communication with the specialist.

<p>
<img width="506" height="298" alt="image" src="https://github.com/user-attachments/assets/49852812-f8b4-4383-a464-ea534a74e962" />
</p>

The dashboard therefore provides a central overview of the patient’s current recommendations and quick access to the most important application features.

####  Survey Handling 

The Surveys section displays all questionnaires assigned by the specialist. Surveys are marked as either Pending or Completed, and users can either fill in a pending survey or review previously submitted answers (Figure 7.26).

<p>
<img width="506" height="254" alt="image" src="https://github.com/user-attachments/assets/92f8b1f4-3c99-4363-bc61-5655f8cf692a" />
</p>

When completing a survey, the patient answers questions prepared by the specialist. Before submission, the system displays a confirmation message informing the patient that the survey can only be submitted once and cannot be edited later (Figure 7.27). After successful submission, a confirmation notification is displayed (Figure 7.28).

<p>
<img width="506" height="328" alt="image" src="https://github.com/user-attachments/assets/c053a864-ade3-4933-9966-121ea7f15c98" />
</p>

<p>
<img width="506" height="118" alt="image" src="https://github.com/user-attachments/assets/d9ba8096-1b89-4686-a89f-77514ea5ead8" />
</p>

This module provides a simple way to complete, track, and review patient questionnaires.

#### Laboratory Results 

The Laboratory Results section provides access to the full history of medical test data entered by the patient. Results are displayed as individual records and can be filtered by date (Figure 7.29).

<p>
<img width="506" height="176" alt="image" src="https://github.com/user-attachments/assets/9e7aa7a7-b053-4b2d-bf1c-c665761e056d" />
</p>

Patients can also add new laboratory results through a structured form containing multiple categories, including hormone tests, stool tests, and basic health parameters (Figure 7.30). The form supports numerical, categorical, and descriptive values.

<p>
<img width="506" height="508" alt="image" src="https://github.com/user-attachments/assets/2c9da23c-be07-44b7-8da0-0918a9a15f35" />
</p>

Once saved, laboratory results cannot be edited, so patients are required to verify the entered data before submission. The module therefore provides a structured medical data source that can later be reviewed by the specialist and used during diagnostic analysis.

####  Doctor Selection 

The My Doctor section allows patients to search for and select a specialist. Doctors can be filtered by name, while their profiles provide information such as specialization, education, professional experience, license number, location, and additional details (Figure 7.31).

<p>
<img width="506" height="424" alt="image" src="https://github.com/user-attachments/assets/b837fa9a-9fb6-4df0-8dc3-2048b5cfc2f6" />
</p>

After selecting a doctor, the specialist is assigned to the patient and displayed in the My Specialist section (Figure 7.32). The patient can also end the relationship using the Resign option. This action requires confirmation before it is processed (Figure 7.33).

<p>
<img width="506" height="318" alt="image" src="https://github.com/user-attachments/assets/bd8dd0d9-9f8e-4bba-b9d1-998fcfa9d388" />
</p>

After resignation, the system displays a notification and updates the patient’s status in the specialist’s profile to inactive (Figure 7.34). 

<p>
<img width="506" height="144" alt="image" src="https://github.com/user-attachments/assets/fa26ede7-8a2a-47b4-9e26-e53a9ca43891" />
</p>


<p>
<img width="506" height="72" alt="image" src="https://github.com/user-attachments/assets/01eff250-b419-4998-8dac-0afb402dfe58" />
</p>

This functionality gives patients direct control over selecting and changing their assigned specialist.

#### Habit and Well-being Monitoring

The Habits, Calendar, and Statistics sections provide a simple system for tracking the patient’s daily well-being and lifestyle.

In the Habits section, the patient completes a daily form covering mood, sleep duration, emotions, notes, coffee and alcohol consumption, smoking, and physical activity (Figure 7.35).

<p>
<img width="506" height="566" alt="image" src="https://github.com/user-attachments/assets/49282702-edb8-421d-94ea-20468b7e3545" />
</p>

The Calendar stores completed daily entries and allows users to review, edit, delete, export, or add missing records (Figure 7.36).

<p>
<img width="506" height="284" alt="image" src="https://github.com/user-attachments/assets/56f8ab7a-47ee-4ef2-b223-2bcd33879135" />
</p>

The Statistics section visualizes collected data using charts, making it easier to identify trends in mood and other health-related indicators over time (Figure 7.37).

<p>
<img width="506" height="330" alt="image" src="https://github.com/user-attachments/assets/c8268b8d-c4f1-460d-99bc-65f502ef2202" />
</p>

Together, these features support regular self-monitoring and provide additional data that may be useful during medical assessment and diagnosis.

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

